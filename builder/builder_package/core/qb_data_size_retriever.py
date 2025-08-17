from typing import Any, Dict, Optional, Tuple
import hashlib
import json
import requests
from requests.exceptions import HTTPError
from builder_package.core.http_retriever import HTTPRetriever
from builder_package.core.itool_call import IToolCall, ToolCallResult
from builder_package.core.cb_user import CBUser
from builder_package.core.iauthenticator import IHTTPConnection
import logging

class QBDataSizeRetriever(HTTPRetriever, IToolCall):
    def __init__(
            self, 
            connection: IHTTPConnection,
            cb_user: CBUser,
            query: str,
            save_file_path: Optional[str] = None
        ):
        super().__init__(connection, cb_user, save_file_path)
        self.query = query
    
    def is_query_valid(self) -> bool:
        # generate code to reject malformed queries, subqueries, joins and aliases
        # and return False if the query is invalid
        # if query is valid, return True

        return 'COUNT(*)' in self.query
    
    def _get_endpoint(self) -> str:
        return "/query"
    
    def _get_params(self) -> Dict[str, Any]:
        return {
            "query": self.query
        }
    
    def _to_json(self, response: requests.Response) -> Tuple[Dict[str, Any], int]:
        response_json = response.json()
        return (
            response_json, 
            len(response_json.get('QueryResponse', {}).get(self.extract_query_response_key(), []))
        )
    
    def extract_query_response_key(self) -> str:
        # Find the position of FROM in the original query (case-insensitive)
        from_index = self.query.upper().find('FROM')
        if from_index != -1:
            # Extract everything after FROM
            from_part = self.query[from_index + 4:].strip()
            # Handle cases where there might be WHERE, ORDER BY, etc. after the table name
            table_name = from_part.split()[0].strip()
            return table_name
        return "Unknown"
    
    def _cache_key(self) -> str:
        params_hash_6chars = hashlib.sha256(json.dumps(self.query).encode()).hexdigest()[:6]
        return f"qb_data_size_retriever_{self.extract_query_response_key()}_{params_hash_6chars}"

    def api_summary(self) -> str:
        return f"Makes HTTP calls to retrieve number of rows in a query"
    
    def call_tool(self) -> ToolCallResult:
        try:
            assert self.is_query_valid(), "Query is invalid, should be like SELECT COUNT(*) FROM Bill WHERE TxnDate = '2025-01-01'"
            responses = self.retrieve()
            if len(responses) == 0 or len(responses[0].get('QueryResponse', {})) == 0:
                return ToolCallResult.error(
                    tool_name=QBDataSizeRetriever.tool_name(),
                    error_type="NoData",
                    error_message="No data found"
                )
            return ToolCallResult.success(
                tool_name=QBDataSizeRetriever.tool_name(),
                file_name=self._cache_key() + ".jsonl", 
                data=responses[0]
            )
        except HTTPError as e:
            logging.error(f"HTTP error: {e}")
            return ToolCallResult.error(
                tool_name=QBDataSizeRetriever.tool_name(),
                error_type=e.__class__.__name__, 
                error_message=str(e), 
                status_code=e.response.status_code
            )
        except Exception as e:
            logging.error(f"Error returning data from quickbooks api: {e}")
            return ToolCallResult.error(
                tool_name=QBDataSizeRetriever.tool_name(),
                error_type=e.__class__.__name__, 
                error_message=str(e)
            )
    
    @staticmethod
    def tool_name() -> str:
        return f"qb_data_size_retriever"
    
    @staticmethod
    def tool_description() -> dict:
        return {
            "type": "function",
            "function": {
                "name": QBDataSizeRetriever.tool_name(),
                "description": "Retrieve number of rows in a query from Quickbooks using Quickbooks HTTP platform API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to retrieve number of rows from Quickbooks"
                        }
                    }
                }
            }
        }
    
    def extract_result_summary(self, result: Any) -> dict:
        raise NotImplementedError("Not implemented")