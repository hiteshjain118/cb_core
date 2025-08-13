import hashlib
import os
import sys
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

from builder_package.core.cb_user import CBUser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builder_package.core.iauthenticator import IHTTPConnection
from builder_package.core.itool_call import IToolCall, ToolCallResult
from builder_package.core.iretriever import IRetriever
from builder_package.core.logging_config import setup_logging
import logging
import requests
from requests.exceptions import HTTPError

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class HTTPRetriever(IRetriever):
    def __init__(
            self, 
            connection: IHTTPConnection,
            cb_user: CBUser,
            # None for no persistance
            # 'default' to use the cachekey as the file name in configured directory
            # 'complete_file_name' to save to filepath of choice
            save_file_path: Optional[str] = None
        ):
        self.connection = connection
        self.cb_user = cb_user
        self.save_file_path = save_file_path
        self.page_size = 100
        self.start_pos = 1

    def try_cache(self) -> Any:
        if self.save_file_path == 'default':
            self.save_file_path = f"{self._cache_key()}.jsonl"
        if self.save_file_path:
            if os.path.exists(self.save_file_path):
                with open(self.save_file_path, 'r') as f:
                    responses = [json.loads(line) for line in f]
                    return responses
        return None
        
    def cache(self, responses: List[Dict[str, Any]]) -> None:
        if self.save_file_path == 'default':
            self.save_file_path = f"{self._cache_key()}.jsonl"
        if self.save_file_path:
            logger.info(f"Saving {len(responses)} responses to {self.save_file_path}")
            with open(self.save_file_path, 'a') as f:
                for response in responses:
                    # Convert JSON object to string for file storage
                    f.write(json.dumps(response) + '\n')
     
    def retrieve(self) -> Any:
        if not self.connection.is_authorized():
            logger.error(f"Entity {self.connection.get_cbid()} is no longer connected")
            raise Exception(f"Entity {self.connection.get_cbid()} is no longer connected")
        
        responses = self.try_cache()
        if responses is None:
            responses = self._call_api()
            self.cache(responses)
        else:
            logger.info(f"Retrieved {len(responses)} responses from cache for cache key {self._cache_key()}")
            
        return responses

    def get_headers(self)-> Dict[str, str]:
        access_token = self.connection.get_valid_access_token_not_throws()
        if not access_token:
            raise Exception(f"No valid access token for entity {self.connection.get_cbid()}")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    
    def _call_api(self) -> List[Dict[str, Any]]:
        # handle paginated queries and response 
        responses = []
        while True:
            paginated_response, num_items = self._call_api_once()
            responses.append(paginated_response)
            if num_items < self.page_size:
                break
            self.start_pos += self.page_size    

        return responses

    def _call_api_once(self) -> Tuple[Dict[str, Any], int]:
        url = f"{self.cb_user.base_url}{self._get_endpoint()}"
        params = self._get_params()
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        response.raise_for_status()
        to_return = self._to_json(response)

        logger.info(
            f"{self.api_summary()} call for key {self._cache_key()} returned {to_return[1]} items"
            + f" url: {url}"
            + f" params: {params}"
            + f" start_pos: {self.start_pos}"
            + f" page_size: {self.page_size}"
        )

        return to_return

        
    @abstractmethod
    def _get_endpoint(self) -> str:
        """
        Get the url for the API call
        """
        pass
    
    @abstractmethod
    def _get_params(self) -> Dict[str, Any]:
        """
        Get the params for the API call
        """
        pass
    
    @abstractmethod
    def _to_json(self, response: requests.Response) -> Tuple[Dict[str, Any], int]:
        pass
    
    @abstractmethod
    def _cache_key(self) -> str:
        pass
    
    def api_summary(self) -> str:
        return f"Base class to handle auth and batching logic for CB HTTP API"


class ModelHTTPRetriever(HTTPRetriever, IToolCall):
    def __init__(
            self, 
            connection: IHTTPConnection,
            cb_user: CBUser,
            endpoint: str,
            params: Dict[str, Any],
            save_file_path: Optional[str] = None
        ):
        super().__init__(connection, cb_user, save_file_path)
        self.endpoint = endpoint
        self.params = params
    
    def is_query_valid(self) -> bool:
        query = self.params.get('query')
        # generate code to reject malformed queries, subqueries, joins and aliases
        # and return False if the query is invalid
        return True
    
    def _get_endpoint(self) -> str:
        # Ensure endpoint starts with a forward slash for proper URL construction
        if not self.endpoint.startswith('/'):
            return f"/{self.endpoint}"
        return self.endpoint
    
    def _get_params(self) -> Dict[str, Any]:
        return self.params
    
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
        return f"model_http_retriever_{self.endpoint}_{self.extract_query_response_key()}_{params_hash_6chars}"

    def api_summary(self) -> str:
        return f"Makes HTTP calls using endpoint and params from the model"
    
    def call_tool(self) -> ToolCallResult:
        try:
            responses = self.retrieve()
            if len(responses) == 0 or len(responses[0].get('QueryResponse', {})) == 0:
                return ToolCallResult.error(
                    tool_name=ModelHTTPRetriever.tool_name(),
                    error_type="NoData",
                    error_message="No data found"
                )
            return ToolCallResult.success(
                tool_name=ModelHTTPRetriever.tool_name(),
                file_name=self._cache_key() + ".jsonl", 
                sample=self.extract_result_summary(responses)
            )
        except HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return ToolCallResult.error(
                tool_name=ModelHTTPRetriever.tool_name(),
                error_type=e.__class__.__name__, 
                error_message=str(e), 
                status_code=e.response.status_code
            )
        except Exception as e:
            logger.error(f"Error returning data from quickbooks api: {e}")
            return ToolCallResult.error(
                tool_name=ModelHTTPRetriever.tool_name(),
                error_type=e.__class__.__name__, 
                error_message=str(e)
            )
    
    @staticmethod
    def tool_name() -> str:
        return f"qb_http_retriever"
    
    @staticmethod
    def tool_description() -> dict:
        return {
            "type": "function",
            "function": {
                "name": ModelHTTPRetriever.tool_name(),
                "description": "Retrieve data from Quickbooks using Quickbooks HTTP platform API",
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
                "description" : f"Did {len(result)} api calls within tool call. Sample result shown below.",
                "sample": first_result
            }
        raise Exception(f"Expected list of results, got {type(result)}")