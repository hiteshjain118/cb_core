from urllib.error import HTTPError
from builder_package.core.http_retriever import HTTPRetriever
from builder_package.core.itool_call import IToolCall, ToolCallResult
from builder_package.core.cb_user import CBUser
from builder_package.core.iauthenticator import IHTTPConnection
from builder_package.core.logging_config import setup_logging
import logging
from typing import Any, Dict, Optional, Tuple

# Setup logging for this module
setup_logging()
import hashlib
import json
import requests


class QBDataSchemaRetriever(HTTPRetriever, IToolCall):
    def __init__(
            self, 
            connection: IHTTPConnection,
            cb_user: CBUser,
            table_name: str,
            save_file_path: Optional[str] = None
        ):
        super().__init__(connection, cb_user, save_file_path)
        self.table_name = table_name
    
    def is_query_valid(self) -> bool:
        return True
    
    def _get_endpoint(self) -> str:
        return "/query"
    
    def _get_params(self) -> Dict[str, Any]:
        return {
            "query": f"SELECT * FROM {self.table_name} MAXRESULTS 1"
        }
    
    def _to_json(self, response: requests.Response) -> Tuple[Dict[str, Any], int]:
        response_json = response.json()
        return (
            response_json, 
            len(response_json.get('QueryResponse', {}).get(self.extract_query_response_key(), []))
        )
    
    def extract_query_response_key(self) -> str:
        return self.table_name
    
    def _cache_key(self) -> str:
        return f"qb_data_schema_retriever_{self.table_name}"

    def api_summary(self) -> str:
        return f"Makes HTTP calls to retrieve data schema from Quickbooks"
    
    def call_tool(self) -> ToolCallResult:
        try:
            responses = self.retrieve()
            if len(responses) == 0 or len(responses[0].get('QueryResponse', {})) == 0:
                return ToolCallResult.error(
                    tool_name=QBDataSchemaRetriever.tool_name(),
                    error_type="NoData",
                    error_message="No data found"
                )
            return ToolCallResult.success(
                tool_name=QBDataSchemaRetriever.tool_name(),
                file_name=self._cache_key() + ".jsonl",     
                data=responses[0]
            )
        except HTTPError as e:
            logging.error(f"HTTP error: {e}")
            return ToolCallResult.error(
                tool_name=QBDataSchemaRetriever.tool_name(),
                error_type=e.__class__.__name__, 
                error_message=str(e), 
                status_code=e.response.status_code
            )
        except Exception as e:
            logging.error(f"Error returning data from quickbooks api: {e}")
            return ToolCallResult.error(
                tool_name=QBDataSchemaRetriever.tool_name(),
                error_type=e.__class__.__name__, 
                error_message=str(e)
            )
    
    @staticmethod
    def tool_name() -> str:
        return f"qb_data_schema_retriever"
    
    @staticmethod
    def tool_description() -> dict:
        return {
            "type": "function",
            "function": {
                "name": QBDataSchemaRetriever.tool_name(),
                "description": "Retrieve data schema from Quickbooks using Quickbooks HTTP platform API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "The name of the table to retrieve data schema for"
                        }
                    }
                }
            }
        }
    
    def extract_result_summary(self, result: Any) -> dict:
        # expect result to be a json object. Generate code to extract it's schema
        raise NotImplementedError("Not implemented")