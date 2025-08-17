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


