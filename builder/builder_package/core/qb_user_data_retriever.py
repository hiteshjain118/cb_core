from typing import Any, Dict, Optional, Tuple
import hashlib
import json
import requests
from requests.exceptions import HTTPError
from builder_package.core.http_retriever import HTTPRetriever
from builder_package.core.itool_call import IToolCall, ToolCallResult
from builder_package.core.cb_user import CBUser
from builder_package.core.iauthenticator import IHTTPConnection
from builder_package.core.logging_config import setup_logging
import logging

# Setup logging for this module
setup_logging()

class QBUserDataRetriever(HTTPRetriever, IToolCall):
    def __init__(
            self, 
            connection: IHTTPConnection,
            cb_user: CBUser,
            endpoint: str,
            params: Dict[str, Any],
            expected_row_count: int,
            save_file_path: Optional[str] = None
        ):
        super().__init__(connection, cb_user, save_file_path)
        self.endpoint = endpoint
        self.params = params
        self.expected_row_count = expected_row_count
    
    def is_query_valid(self) -> bool:
        if 'SELECT *' not in self.params.get('query', '').upper():
            raise ValueError('Please select all columns by doing SELECT *')
        if 'ORDER BY' not in self.params.get('query', ''):
            raise ValueError('ORDER BY clause is missing')
        if self.expected_row_count is None or self.expected_row_count < 0:
            raise ValueError('Expected row count must be provided and greater than or equal to 0')
        if self.expected_row_count > 1000:
            raise ValueError('Expected row count must be less than 1000')
        return True
    
    def _get_endpoint(self) -> str:
        # Ensure endpoint starts with a forward slash for proper URL construction
        if not self.endpoint.startswith('/'):
            return f"/{self.endpoint}"
        return self.endpoint
    
    def _get_params(self) -> Dict[str, Any]:
        return {
            'query': f"{self.params['query']} STARTPOSITION {self.start_pos} MAXRESULTS {self.page_size}"
        }
    
    def _to_json(self, response: requests.Response) -> Tuple[Dict[str, Any], int]:
        response_json = response.json()
        return (
            response_json, 
            len(response_json.get('QueryResponse', {}).get(self.extract_query_response_key(), []))
        )
    
    def extract_query_response_key(self) -> str:
        query = self.params.get('query')
        if query:
            # Find the position of FROM in the original query (case-insensitive)
            from_index = query.upper().find('FROM')
            if from_index != -1:
                # Extract everything after FROM
                from_part = query[from_index + 4:].strip()
                # Handle cases where there might be WHERE, ORDER BY, etc. after the table name
                table_name = from_part.split()[0].strip()
                return table_name
        return "Unknown"
    
    def _cache_key(self) -> str:
        params_hash_6chars = hashlib.sha256(json.dumps(self.params).encode()).hexdigest()[:6]
        return f"qb_user_data_retriever_{self.endpoint}_{self.extract_query_response_key()}_{params_hash_6chars}"

    def api_summary(self) -> str:
        return f"Makes QB HTTP calls using endpoint and params to get user data"
    
    def call_tool(self) -> ToolCallResult:
        try:
            self.is_query_valid()
            responses = self.retrieve()
            if len(responses) == 0 or len(responses[0].get('QueryResponse', {})) == 0:
                return ToolCallResult.error(
                    tool_name=QBUserDataRetriever.tool_name(),
                    error_type="NoData",
                    error_message="No data found"
                )
            return ToolCallResult.success(
                tool_name=QBUserDataRetriever.tool_name(),
                file_name=self._cache_key() + ".jsonl", 
                data=self.extract_result_summary(responses)
            )
        except HTTPError as e:
            logging.error(f"HTTP error: {e}")
            return ToolCallResult.error(
                tool_name=QBUserDataRetriever.tool_name(),
                error_type=e.__class__.__name__, 
                error_message=str(e), 
                status_code=e.response.status_code
            )
        except Exception as e:
            logging.error(f"Error returning data from quickbooks api: {e}")
            return ToolCallResult.error(
                tool_name=QBUserDataRetriever.tool_name(),
                error_type=e.__class__.__name__, 
                error_message=str(e)
            )
    
    @staticmethod
    def tool_name() -> str:
        return f"qb_user_data_retriever"
    
    @staticmethod
    def tool_description() -> dict:
        return {
            "type": "function",
            "function": {
                "name": QBUserDataRetriever.tool_name(),
                "description": "Retrieve user's data from Quickbooks using Quickbooks HTTP platform API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "endpoint": {
                            "type": "string",
                            "description": "The endpoint to query"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "HTTP parameters for querying the endpoint"
                        },
                        "expected_row_count": {
                            "type": "integer",
                            "description": "The expected number of rows to be returned from the query"
                        }
                    }
                }
            }
        }
    
    def extract_result_summary(self, result: Any) -> dict:
        # expect result to be a json object. Generate code to extract it's schema
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]
            return {
                "description" : f"Did {len(result)} api calls within tool call. Data was stored in {self.save_file_path}.",
                # "sample": first_result
            }
        raise Exception(f"Expected list of results, got {type(result)}")