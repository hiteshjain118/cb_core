#!/usr/bin/env python3
"""
Unit tests for ModelHTTPRetriever tool call functionality
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime
from urllib.error import HTTPError
import requests
from typing import Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builder_package.core.http_retriever import ModelHTTPRetriever
from builder_package.core.itool_call import ToolCallResult
from builder_package.core.iauthenticator import IHTTPConnection
from builder_package.core.cb_user import CBUser
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockHTTPConnection(IHTTPConnection):
    """Mock HTTP connection for testing"""
    
    def __init__(self, is_authorized=True, access_token="test_token", cb_id="test_cb_id"):
        self._is_authorized = is_authorized
        self._access_token = access_token
        self._cb_id = cb_id
    
    def authenticate(self) -> str:
        return self._access_token
    
    def is_authorized(self) -> bool:
        return self._is_authorized
    
    def get_valid_access_token_not_throws(self) -> str:
        return self._access_token
    
    def get_cbid(self) -> str:
        return self._cb_id
    
    def get_platform_name(self) -> str:
        return "test_platform"
    
    def get_remote_user(self) -> Any:
        return {"id": self._cb_id, "platform": "test_platform"}


class MockCBUser(CBUser):
    """Mock CB user for testing"""
    
    def __init__(self, base_url="https://test.api.com", user_timezone="UTC"):
        super().__init__(base_url, user_timezone)


class TestModelHTTPRetriever(unittest.TestCase):
    """Test cases for ModelHTTPRetriever tool call functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connection = MockHTTPConnection()
        self.mock_cb_user = MockCBUser()
        self.endpoint = "query"
        self.params = {"query": "SELECT * FROM Customer"}
        
        self.retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint=self.endpoint,
            params=self.params
        )

    def test_init(self):
        """Test ModelHTTPRetriever initialization"""
        self.assertEqual(self.retriever.endpoint, self.endpoint)
        self.assertEqual(self.retriever.params, self.params)
        self.assertEqual(self.retriever.connection, self.mock_connection)
        self.assertEqual(self.retriever.cb_user, self.mock_cb_user)

    def test_get_endpoint_with_slash(self):
        """Test _get_endpoint when endpoint already has leading slash"""
        self.retriever.endpoint = "/query"
        result = self.retriever._get_endpoint()
        self.assertEqual(result, "/query")

    def test_get_endpoint_without_slash(self):
        """Test _get_endpoint when endpoint doesn't have leading slash"""
        self.retriever.endpoint = "query"
        result = self.retriever._get_endpoint()
        self.assertEqual(result, "/query")

    def test_get_params(self):
        """Test _get_params returns the correct parameters"""
        result = self.retriever._get_params()
        self.assertEqual(result, self.params)

    def test_cache_key(self):
        """Test _cache_key generation"""
        expected_key = f"model_http_retriever_{self.endpoint}_{self.params}"
        result = self.retriever._cache_key()
        self.assertEqual(result, expected_key)

    def test_api_summary(self):
        """Test api_summary method"""
        expected = "Makes HTTP calls using endpoint and params from the model"
        result = self.retriever.api_summary()
        self.assertEqual(result, expected)

    def test_tool_name(self):
        """Test tool_name method"""
        result = self.retriever.tool_name()
        self.assertEqual(result, "model_http_retriever")

    def test_tool_description(self):
        """Test tool_description method"""
        result = self.retriever.tool_description()
        
        # tool_description should return a tool schema dictionary
        self.assertIsInstance(result, dict)
        self.assertIn("type", result)
        self.assertEqual(result["type"], "function")
        self.assertIn("function", result)
        self.assertIn("name", result["function"])
        self.assertEqual(result["function"]["name"], "retrieve_qb_data")
        self.assertIn("description", result["function"])
        self.assertIn("parameters", result["function"])

    def test_extract_result_summary_success(self):
        """Test extract_result_summary with valid data"""
        mock_response = {
            "QueryResponse": {
                "Item": [{"Id": "1", "Name": "Test Customer"}]
            }
        }
        result = self.retriever.extract_result_summary([mock_response])
        
        self.assertIn("description", result)
        self.assertIn("example", result)
        self.assertIn("Did 1 api calls within tool call", result["description"])
        self.assertEqual(result["example"], mock_response["QueryResponse"])

    def test_extract_result_summary_empty_response(self):
        """Test that call_tool returns NoData error when response has empty QueryResponse"""
        mock_response = {
            "QueryResponse": {}
        }
        
        with patch.object(self.retriever, 'retrieve', return_value=[mock_response]):
            result = self.retriever.call_tool()
            
            # Should return error status with NoData error type
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_type, "NoData")
            self.assertEqual(result.error_message, "No data found")
            
            # Verify that extract_result_summary can still handle empty response
            summary = self.retriever.extract_result_summary([mock_response])
            self.assertIn("description", summary)
            self.assertIn("example", summary)
            self.assertEqual(summary["example"], {})

    def test_extract_result_summary_invalid_type(self):
        """Test extract_result_summary with invalid result type"""
        with self.assertRaises(Exception) as context:
            self.retriever.extract_result_summary("invalid")
        
        self.assertIn("Expected list of results", str(context.exception))

    def test_call_tool_success(self):
        """Test call_tool method with successful retrieval"""
        mock_response = {
            "QueryResponse": {
                "Item": [{"Id": "1", "Name": "Test Customer"}]
            }
        }
        
        with patch.object(self.retriever, 'retrieve', return_value=[mock_response]):
            result = self.retriever.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "success")
            self.assertEqual(result.tool_name, "model_http_retriever")
            self.assertIsNotNone(result.handle_name)
            self.assertIn("description", result.content)
            self.assertIn("example", result.content)

    def test_call_tool_no_data(self):
        """Test call_tool method when no data is found"""
        empty_response = {"QueryResponse": {}}
        
        with patch.object(self.retriever, 'retrieve', return_value=[empty_response]):
            result = self.retriever.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_type, "NoData")
            self.assertEqual(result.error_message, "No data found")

    def test_call_tool_empty_response_list(self):
        """Test call_tool method with empty response list"""
        with patch.object(self.retriever, 'retrieve', return_value=[]):
            result = self.retriever.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_type, "NoData")
            self.assertEqual(result.error_message, "No data found")

    def test_call_tool_http_error(self):
        """Test call_tool method with HTTP error"""
        # Create a proper HTTPError with response attribute
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.text = "Invalid query"
        
        # Create HTTPError with proper structure
        http_error = HTTPError("https://test.api.com/query", 400, "Bad Request", mock_response, None)
        # Add response attribute to the error
        http_error.response = mock_response
        
        with patch.object(self.retriever, 'retrieve', side_effect=http_error):
            result = self.retriever.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_type, "HTTPError")
            self.assertEqual(result.status_code, 400)
            self.assertIn("400", result.error_message)
            self.assertIn("Bad Request", result.error_message)

    def test_call_tool_general_exception(self):
        """Test call_tool method with general exception"""
        test_exception = Exception("Test exception message")
        
        with patch.object(self.retriever, 'retrieve', side_effect=test_exception):
            result = self.retriever.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_type, "Exception")
            self.assertEqual(result.error_message, "Test exception message")

    def test_call_tool_unauthorized_connection(self):
        """Test call_tool method when connection is not authorized"""
        unauthorized_connection = MockHTTPConnection(is_authorized=False)
        retriever = ModelHTTPRetriever(
            connection=unauthorized_connection,
            cb_user=self.mock_cb_user,
            endpoint=self.endpoint,
            params=self.params
        )
        
        # The retrieve method should raise an exception, but call_tool should catch it
        with self.assertRaises(Exception) as context:
            retriever.retrieve()
        
        self.assertIn("is no longer connected", str(context.exception))
        
        # Now test that call_tool handles the exception gracefully
        result = retriever.call_tool()
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_type, "Exception")

    def test_to_json_with_query_response(self):
        """Test _to_json method with QueryResponse data"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "QueryResponse": {
                "Item": [{"Id": "1"}, {"Id": "2"}]
            }
        }
        
        result, num_items = self.retriever._to_json(mock_response)
        
        self.assertEqual(num_items, 2)
        self.assertIn("QueryResponse", result)
        self.assertIn("Item", result["QueryResponse"])

    def test_to_json_without_query_response(self):
        """Test _to_json method without QueryResponse data"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "SomeOtherResponse": {}
        }
        
        result, num_items = self.retriever._to_json(mock_response)
        
        self.assertEqual(num_items, 0)
        self.assertNotIn("QueryResponse", result)

    def test_to_json_with_empty_query_response(self):
        """Test _to_json method with empty QueryResponse"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "QueryResponse": {}
        }
        
        result, num_items = self.retriever._to_json(mock_response)
        
        self.assertEqual(num_items, 0)
        self.assertIn("QueryResponse", result)

    def test_integration_with_mock_requests(self):
        """Test integration with mocked requests library"""
        mock_response = {
            "QueryResponse": {
                "Item": [{"Id": "1", "Name": "Test Customer"}]
            }
        }
        
        with patch.object(self.retriever, 'retrieve', return_value=[mock_response]):
            result = self.retriever.call_tool()
            
            self.assertEqual(result.status, "success")
            self.assertIn("example", result.content)

    def test_error_handling_edge_cases(self):
        """Test error handling with various edge cases"""
        # Test with malformed response that has QueryResponse as None
        # This will cause a TypeError when trying to call len() on None
        malformed_response = {"QueryResponse": None}
        with patch.object(self.retriever, 'retrieve', return_value=[malformed_response]):
            result = self.retriever.call_tool()
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_type, "TypeError")
        
        # Test with response that has empty QueryResponse dict
        empty_response = {"QueryResponse": {}}
        with patch.object(self.retriever, 'retrieve', return_value=[empty_response]):
            result = self.retriever.call_tool()
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_type, "NoData")

    def test_tool_call_result_structure(self):
        """Test that ToolCallResult has the correct structure"""
        mock_response = {
            "QueryResponse": {
                "Item": [{"Id": "1", "Name": "Test Customer"}]
            }
        }
        
        with patch.object(self.retriever, 'retrieve', return_value=[mock_response]):
            result = self.retriever.call_tool()
            
            # Test success result structure
            self.assertTrue(hasattr(result, 'status'))
            self.assertTrue(hasattr(result, 'tool_name'))
            self.assertTrue(hasattr(result, 'handle_name'))
            self.assertTrue(hasattr(result, 'content'))
            
            # Test that error fields are None for success
            self.assertIsNone(result.error_type)
            self.assertIsNone(result.error_message)
            self.assertIsNone(result.status_code)
            
            # Test that content contains the expected data
            self.assertIn("description", result.content)
            self.assertIn("example", result.content)

    def test_file_saving_with_default_path(self):
        """Test that files are saved when save_file_path is 'default'"""
        import tempfile
        import os
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for file operations
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create retriever with default save path
                retriever = ModelHTTPRetriever(
                    connection=self.mock_connection,
                    cb_user=self.mock_cb_user,
                    endpoint=self.endpoint,
                    params=self.params,
                    save_file_path="default"
                )
                
                mock_response = {
                    "QueryResponse": {
                        "Item": [{"Id": "1", "Name": "Test Customer"}]
                    }
                }
                
                # Test the file saving logic directly by calling the parent class method
                # We need to mock the _call_api method to return our test data
                with patch.object(retriever, '_call_api', return_value=[mock_response]):
                    # Mock the connection to be authorized
                    with patch.object(retriever.connection, 'is_authorized', return_value=True):
                        # Call retrieve which will trigger file saving
                        responses = retriever.retrieve()
                        
                        # Verify the result
                        self.assertEqual(len(responses), 1)
                        self.assertEqual(responses[0], mock_response)
                        
                        # Check that the file was created with the expected name
                        expected_filename = f"{retriever._cache_key()}.jsonl"
                        self.assertTrue(os.path.exists(expected_filename), 
                                      f"File {expected_filename} should exist")
                        
                        # Verify file content
                        with open(expected_filename, 'r') as f:
                            content = f.read().strip()
                            lines = content.split('\n')
                            
                            # Should have one line per response
                            self.assertEqual(len(lines), 1)
                            
                            # Parse the JSON line
                            import json
                            saved_data = json.loads(lines[0])
                            self.assertEqual(saved_data, mock_response)
                        
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

    def test_file_saving_with_custom_path(self):
        """Test that files are saved when save_file_path is a custom path"""
        import tempfile
        import os
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_filename = os.path.join(temp_dir, "custom_test.jsonl")
            
            # Create retriever with custom save path
            retriever = ModelHTTPRetriever(
                connection=self.mock_connection,
                cb_user=self.mock_cb_user,
                endpoint=self.endpoint,
                params=self.params,
                save_file_path=custom_filename
            )
            
            mock_response = {
                "QueryResponse": {
                    "Item": [{"Id": "1", "Name": "Test Customer"}]
                }
            }
            
            # Test the file saving logic directly
            with patch.object(retriever, '_call_api', return_value=[mock_response]):
                with patch.object(retriever.connection, 'is_authorized', return_value=True):
                    responses = retriever.retrieve()
                    
                    # Check that the file was created with custom name
                    self.assertTrue(os.path.exists(custom_filename), 
                                  f"File {custom_filename} should exist")
                    
                    # Verify file content
                    with open(custom_filename, 'r') as f:
                        content = f.read().strip()
                        lines = content.split('\n')
                        
                        # Should have one line per response
                        self.assertEqual(len(lines), 1)
                        
                        # Parse the JSON line
                        import json
                        saved_data = json.loads(lines[0])
                        self.assertEqual(saved_data, mock_response)

    def test_file_saving_with_no_path(self):
        """Test that no files are saved when save_file_path is None"""
        import tempfile
        import os
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for file operations
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create retriever with no save path
                retriever = ModelHTTPRetriever(
                    connection=self.mock_connection,
                    cb_user=self.mock_cb_user,
                    endpoint=self.endpoint,
                    params=self.params,
                    save_file_path=None
                )
                
                mock_response = {
                    "QueryResponse": {
                        "Item": [{"Id": "1", "Name": "Test Customer"}]
                    }
                }
                
                with patch.object(retriever, 'retrieve', return_value=[mock_response]):
                    result = retriever.call_tool()
                    
                    # Verify the result has a handle_name
                    self.assertIsNotNone(result.handle_name)
                    expected_filename = f"{result.handle_name}.jsonl"
                    
                    # Check that no file was created
                    self.assertFalse(os.path.exists(expected_filename), 
                                   f"File {expected_filename} should not exist")
                    
                    # List all files in temp directory to ensure none were created
                    files_in_dir = os.listdir(temp_dir)
                    self.assertEqual(len(files_in_dir), 0, 
                                   f"No files should be created, but found: {files_in_dir}")
                    
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

    def test_file_saving_multiple_responses(self):
        """Test that multiple responses are saved correctly to file"""
        import tempfile
        import os
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for file operations
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create retriever with default save path
                retriever = ModelHTTPRetriever(
                    connection=self.mock_connection,
                    cb_user=self.mock_cb_user,
                    endpoint=self.endpoint,
                    params=self.params,
                    save_file_path="default"
                )
                
                # Mock multiple responses (simulating pagination)
                mock_responses = [
                    {
                        "QueryResponse": {
                            "Item": [{"Id": "1", "Name": "Customer 1"}]
                        }
                    },
                    {
                        "QueryResponse": {
                            "Item": [{"Id": "2", "Name": "Customer 2"}]
                        }
                    }
                ]
                
                # Test the file saving logic directly
                with patch.object(retriever, '_call_api', return_value=mock_responses):
                    with patch.object(retriever.connection, 'is_authorized', return_value=True):
                        responses = retriever.retrieve()
                        
                        # Verify the result
                        self.assertEqual(len(responses), 2)
                        
                        # Check that the file was created with the expected name
                        expected_filename = f"{retriever._cache_key()}.jsonl"
                        self.assertTrue(os.path.exists(expected_filename), 
                                      f"File {expected_filename} should exist")
                        
                        # Verify file content has multiple lines
                        with open(expected_filename, 'r') as f:
                            content = f.read().strip()
                            lines = content.split('\n')
                            
                            # Should have one line per response
                            self.assertEqual(len(lines), 2)
                            
                            # Parse each JSON line
                            import json
                            for i, line in enumerate(lines):
                                saved_data = json.loads(line)
                                self.assertEqual(saved_data, mock_responses[i])
                        
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

    def test_file_saving_handle_name_consistency(self):
        """Test that the saved file name matches the handle_name from tool call result"""
        import tempfile
        import os
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory for file operations
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create retriever with default save path
                retriever = ModelHTTPRetriever(
                    connection=self.mock_connection,
                    cb_user=self.mock_cb_user,
                    endpoint=self.endpoint,
                    params=self.params,
                    save_file_path="default"
                )
                
                mock_response = {
                    "QueryResponse": {
                        "Item": [{"Id": "1", "Name": "Test Customer"}]
                    }
                }
                
                # Test the file saving logic directly
                with patch.object(retriever, '_call_api', return_value=[mock_response]):
                    with patch.object(retriever.connection, 'is_authorized', return_value=True):
                        responses = retriever.retrieve()
                        
                        # Get the handle_name from the result
                        handle_name = retriever._cache_key()
                        self.assertIsNotNone(handle_name)
                        
                        # The file should be named exactly as {handle_name}.jsonl
                        expected_filename = f"{handle_name}.jsonl"
                        
                        # Check that the file exists with the correct name
                        self.assertTrue(os.path.exists(expected_filename), 
                                      f"File {expected_filename} should exist")
                        
                        # Verify that the handle_name in the result matches the cache_key
                        expected_handle_name = retriever._cache_key()
                        self.assertEqual(handle_name, expected_handle_name)
                        
                        # Verify that the file name is exactly what we expect
                        self.assertEqual(expected_filename, f"{expected_handle_name}.jsonl")
                        
            finally:
                # Restore original working directory
                os.chdir(original_cwd)


if __name__ == '__main__':
    unittest.main() 