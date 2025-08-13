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

# Suppress logging from specific modules during tests
logging.getLogger('builder_package.core.http_retriever').setLevel(logging.ERROR)
logging.getLogger('builder_package.model_providers').setLevel(logging.ERROR)
logging.getLogger('openai').setLevel(logging.ERROR)


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
        result = self.retriever._cache_key()
        
        # The new format is: model_http_retriever_{endpoint}_{table_name}_{params_hash}
        expected_prefix = f"model_http_retriever_{self.endpoint}"
        
        # Should start with the expected prefix
        self.assertTrue(result.startswith(expected_prefix))
        
        # Should contain the table name from the query
        self.assertIn("Customer", result)
        
        # Should have the expected structure with hash at the end
        parts = result.split('_')
        self.assertGreaterEqual(len(parts), 4)  # At least 4 parts
        
        # The last part should be a hash (6 characters)
        self.assertEqual(len(parts[-1]), 6)  # hash should be 6 characters
        
        # Should be consistent for the same parameters
        result2 = self.retriever._cache_key()
        self.assertEqual(result, result2)
       
    def test_api_summary(self):
        """Test api_summary method"""
        expected = "Makes HTTP calls using endpoint and params from the model"
        result = self.retriever.api_summary()
        self.assertEqual(result, expected)

    def test_tool_name(self):
        """Test tool_name method"""
        result = self.retriever.tool_name()
        self.assertEqual(result, "qb_http_retriever")

    def test_tool_description(self):
        """Test tool_description method"""
        result = self.retriever.tool_description()
        
        # tool_description should return a tool schema dictionary
        self.assertIsInstance(result, dict)
        self.assertIn("type", result)
        self.assertEqual(result["type"], "function")
        self.assertIn("function", result)
        self.assertIn("name", result["function"])
        self.assertEqual(result["function"]["name"], "qb_http_retriever")
        self.assertIn("description", result["function"])
        self.assertIn("parameters", result["function"])

    def test_extract_result_summary_success(self):
        """Test extract_result_summary with valid data"""
        mock_response = {
            "QueryResponse": {
                "Customer": [{"Id": "1", "Name": "Test Customer"}]
            }
        }
        result = self.retriever.extract_result_summary([mock_response])
        
        self.assertIn("description", result)
        self.assertIn("sample", result)
        self.assertIn("Did 1 api calls within tool call", result["description"])
        self.assertEqual(result["sample"], mock_response)

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
            self.assertIn("sample", summary)
            self.assertEqual(summary["sample"], mock_response)

    def test_extract_result_summary_invalid_type(self):
        """Test extract_result_summary with invalid result type"""
        with self.assertRaises(Exception) as context:
            self.retriever.extract_result_summary("invalid")
        
        self.assertIn("Expected list of results", str(context.exception))

    def test_call_tool_success(self):
        """Test call_tool method with successful retrieval"""
        mock_response = {
            "QueryResponse": {
                "Customer": [{"Id": "1", "Name": "Test Customer"}]
            }
        }
        
        with patch.object(self.retriever, 'retrieve', return_value=[mock_response]):
            result = self.retriever.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "success")
            self.assertEqual(result.tool_name, "qb_http_retriever")
            self.assertIsNotNone(result.file_name)
            self.assertIn("description", result.sample)
            self.assertIn("sample", result.sample)

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
        from requests.exceptions import HTTPError
        from unittest.mock import Mock
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.text = "Invalid query"
        
        # Create HTTPError with proper structure for requests library
        http_error = HTTPError("400 Bad Request", response=mock_response)
        
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
                "Customer": [{"Id": "1"}, {"Id": "2"}]
            }
        }
        
        result, num_items = self.retriever._to_json(mock_response)
        
        self.assertEqual(num_items, 2)
        self.assertIn("QueryResponse", result)
        self.assertIn("Customer", result["QueryResponse"])

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
                "Customer": [{"Id": "1", "Name": "Test Customer"}]
            }
        }
        
        with patch.object(self.retriever, 'retrieve', return_value=[mock_response]):
            result = self.retriever.call_tool()
            
            self.assertEqual(result.status, "success")
            self.assertIn("sample", result.sample)

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
                "Customer": [{"Id": "1", "Name": "Test Customer"}]
            }
        }
        
        with patch.object(self.retriever, 'retrieve', return_value=[mock_response]):
            result = self.retriever.call_tool()
            
            # Test success result structure
            self.assertTrue(hasattr(result, 'status'))
            self.assertTrue(hasattr(result, 'tool_name'))
            self.assertTrue(hasattr(result, 'file_name'))
            self.assertTrue(hasattr(result, 'sample'))
            
            # Test that error fields are None for success
            self.assertIsNone(result.error_type)
            self.assertIsNone(result.error_message)
            self.assertIsNone(result.status_code)
            
            # Test that sample contains the expected fields
            self.assertIn("description", result.sample)
            self.assertIn("sample", result.sample)

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
                    save_file_path='default'
                )
                
                mock_response = {
                    "QueryResponse": {
                        "Customer": [{"Id": "1", "Name": "Test Customer"}]
                    }
                }
                
                # Test the file saving logic directly by calling the parent class method
                # We need to mock the _call_api method to return our test data
                with patch.object(retriever, '_call_api', return_value=[mock_response]):
                    # Mock the connection to be authorized
                    with patch.object(retriever.connection, 'is_authorized', return_value=True):
                        # Mock try_cache to return None (no cache hit)
                        with patch.object(retriever, 'try_cache', return_value=None):
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
                    "Customer": [{"Id": "1", "Name": "Test Customer"}]
                }
            }
            
            # Test the file saving logic directly
            with patch.object(retriever, '_call_api', return_value=[mock_response]):
                with patch.object(retriever.connection, 'is_authorized', return_value=True):
                    # Mock try_cache to return None (no cache hit)
                    with patch.object(retriever, 'try_cache', return_value=None):
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
                        "Customer": [{"Id": "1", "Name": "Test Customer"}]
                    }
                }
                
                with patch.object(retriever, 'retrieve', return_value=[mock_response]):
                    result = retriever.call_tool()
                    
                    # Verify the result has a handle_name
                    self.assertIsNotNone(result.file_name)
                    expected_filename = f"{result.file_name}.jsonl"
                    
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
                    save_file_path='default'
                )
                
                mock_responses = [
                    {"QueryResponse": {"Customer": [{"Id": "1", "Name": "Customer 1"}]}},
                    {"QueryResponse": {"Customer": [{"Id": "2", "Name": "Customer 2"}]}}
                ]
                
                # Test the file saving logic directly by calling the parent class method
                # We need to mock the _call_api method to return our test data
                with patch.object(retriever, '_call_api', return_value=mock_responses):
                    # Mock the connection to be authorized
                    with patch.object(retriever.connection, 'is_authorized', return_value=True):
                        # Mock try_cache to return None (no cache hit)
                        with patch.object(retriever, 'try_cache', return_value=None):
                            # Call retrieve which will trigger file saving
                            responses = retriever.retrieve()
                            
                            # Verify the result
                            self.assertEqual(len(responses), 2)
                            self.assertEqual(responses, mock_responses)
                            
                            # Check that the file was created with the expected name
                            expected_filename = f"{retriever._cache_key()}.jsonl"
                            self.assertTrue(os.path.exists(expected_filename), 
                                          f"File {expected_filename} should exist")
                            
                            # Verify file content
                            with open(expected_filename, 'r') as f:
                                content = f.read().strip()
                                lines = content.split('\n')
                                
                                # Should have one line per response
                                self.assertEqual(len(lines), 2)
                                
                                # Parse the JSON lines
                                import json
                                for i, line in enumerate(lines):
                                    saved_data = json.loads(line)
                                    self.assertEqual(saved_data, mock_responses[i])
                        
            finally:
                # Restore original working directory
                os.chdir(original_cwd)

    def test_extract_query_response_key_simple_select(self):
        """Test extract_query_response_key with simple SELECT * FROM Table query"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": "SELECT * FROM Customer"}
        )
        
        result = retriever.extract_query_response_key()
        self.assertEqual(result, "Customer")

    def test_extract_query_response_key_specific_columns(self):
        """Test extract_query_response_key with SELECT specific columns FROM Table query"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": "SELECT Id, Name, Email FROM Customer"}
        )
        
        result = retriever.extract_query_response_key()
        self.assertEqual(result, "Customer")

    def test_extract_query_response_key_with_where_clause(self):
        """Test extract_query_response_key with SELECT query containing WHERE clause"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": "SELECT * FROM Invoice WHERE TxnDate = '2025-08-08'"}
        )
        
        result = retriever.extract_query_response_key()
        self.assertEqual(result, "Invoice")

    def test_extract_query_response_key_with_complex_select(self):
        """Test extract_query_response_key with complex SELECT statement"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": "SELECT ItemRef.FullName, Line.Amount FROM InvoiceLineDetail"}
        )
        
        result = retriever.extract_query_response_key()
        self.assertEqual(result, "InvoiceLineDetail")


    def test_extract_query_response_key_no_query_param(self):
        """Test extract_query_response_key when query parameter is missing"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={}
        )
        
        result = retriever.extract_query_response_key()
        self.assertEqual(result, "Unknown")

    def test_extract_query_response_key_none_query_param(self):
        """Test extract_query_response_key when query parameter is None"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": None}
        )
        
        result = retriever.extract_query_response_key()
        self.assertEqual(result, "Unknown")

    def test_extract_query_response_key_empty_query(self):
        """Test extract_query_response_key when query parameter is empty string"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": ""}
        )
        
        result = retriever.extract_query_response_key()
        self.assertEqual(result, "Unknown")

    def test_extract_query_response_key_with_whitespace(self):
        """Test extract_query_response_key with query containing extra whitespace"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": "  SELECT   *   FROM   Customer   "}
        )
        
        result = retriever.extract_query_response_key()
        self.assertEqual(result, "Customer")



    def test_extract_query_response_key_integration_with_cache_key(self):
        """Test that extract_query_response_key integrates properly with _cache_key method"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": "SELECT * FROM Invoice"}
        )
        
        # Extract the query response key
        response_key = retriever.extract_query_response_key()
        self.assertEqual(response_key, "Invoice")
        
        # Generate cache key which uses the response key
        cache_key = retriever._cache_key()
        
        # Verify cache key contains the response key
        self.assertIn(response_key, cache_key)
        self.assertIn("Invoice", cache_key)

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
                    save_file_path='default'
                )
                
                mock_response = {
                    "QueryResponse": {
                        "Customer": [{"Id": "1", "Name": "Test Customer"}]
                    }
                }
                
                # Test the file saving logic directly by calling the parent class method
                # We need to mock the _call_api method to return our test data
                with patch.object(retriever, '_call_api', return_value=[mock_response]):
                    # Mock the connection to be authorized
                    with patch.object(retriever.connection, 'is_authorized', return_value=True):
                        # Mock try_cache to return None (no cache hit)
                        with patch.object(retriever, 'try_cache', return_value=None):
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

    def test_extract_query_response_key_with_whitespace(self):
        """Test extract_query_response_key handles various whitespace patterns"""
        test_cases = [
            ("SELECT * FROM Customer", "Customer"),
            ("SELECT * FROM   Customer   ", "Customer"),
            ("SELECT * FROM\nCustomer", "Customer"),
            ("SELECT * FROM\tCustomer", "Customer"),
            ("SELECT * FROM Customer WHERE Active = true", "Customer"),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                retriever = ModelHTTPRetriever(
                    connection=self.mock_connection,
                    cb_user=self.mock_cb_user,
                    endpoint="query",
                    params={"query": query}
                )
                result = retriever.extract_query_response_key()
                self.assertEqual(result, expected)

    def test_extract_query_response_key_case_insensitive(self):
        """Test extract_query_response_key is case insensitive for FROM keyword"""
        test_cases = [
            ("SELECT * FROM Customer", "Customer"),
            ("SELECT * from Customer", "Customer"),
            ("SELECT * From Customer", "Customer"),
            ("SELECT * FROM customer", "customer"),  # Table name case is preserved
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                retriever = ModelHTTPRetriever(
                    connection=self.mock_connection,
                    cb_user=self.mock_cb_user,
                    endpoint="query",
                    params={"query": query}
                )
                result = retriever.extract_query_response_key()
                self.assertEqual(result, expected)



    def test_cache_key_format_consistency(self):
        """Test that cache key follows the expected format consistently"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint="query",
            params={"query": "SELECT * FROM Customer"}
        )
        
        cache_key = retriever._cache_key()
        
        # Should follow the pattern: model_http_retriever_{endpoint}_{table}_{hash}
        parts = cache_key.split('_')
        self.assertGreaterEqual(len(parts), 4)
        self.assertEqual(parts[0], "model")
        self.assertEqual(parts[1], "http")
        self.assertEqual(parts[2], "retriever")
        self.assertEqual(parts[3], "query")
        self.assertEqual(parts[4], "Customer")
        self.assertEqual(len(parts[-1]), 6)  # 6-character hash

    def test_extract_result_summary_with_empty_list(self):
        """Test extract_result_summary handles empty result list"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint=self.endpoint,
            params=self.params
        )
        
        with self.assertRaises(Exception) as context:
            retriever.extract_result_summary([])
        
        self.assertIn("Expected list of results", str(context.exception))

    def test_extract_result_summary_with_non_list(self):
        """Test extract_result_summary handles non-list results"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint=self.endpoint,
            params=self.params
        )
        
        with self.assertRaises(Exception) as context:
            retriever.extract_result_summary("not a list")
        
        self.assertIn("Expected list of results", str(context.exception))

    def test_tool_description_consistency(self):
        """Test that tool_description returns consistent structure"""
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint=self.endpoint,
            params=self.params
        )
        
        description = retriever.tool_description()
        
        # Check structure
        self.assertIn("type", description)
        self.assertIn("function", description)
        self.assertEqual(description["type"], "function")
        
        function = description["function"]
        self.assertIn("name", function)
        self.assertIn("description", function)
        self.assertIn("parameters", function)
        
        # Check name consistency
        self.assertEqual(function["name"], retriever.tool_name())
        
        # Check parameters structure
        params = function["parameters"]
        self.assertIn("type", params)
        self.assertIn("properties", params)
        self.assertEqual(params["type"], "object")

    def test_error_handling_with_status_code(self):
        """Test that HTTP errors include status codes in error results"""
        from requests.exceptions import HTTPError
        from unittest.mock import Mock
        
        retriever = ModelHTTPRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            endpoint=self.endpoint,
            params=self.params
        )
        
        # Mock an HTTP error with status code
        mock_response = Mock()
        mock_response.status_code = 429  # Too Many Requests
        
        # Create a proper HTTPError that matches what requests library raises
        # requests.HTTPError has a different constructor than urllib.error.HTTPError
        http_error = HTTPError("429 Too Many Requests", response=mock_response)
        
        with patch.object(retriever, 'retrieve', side_effect=http_error):
            result = retriever.call_tool()
            
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_type, "HTTPError")
            self.assertEqual(result.status_code, 429)
            self.assertIn("429", result.error_message)


if __name__ == '__main__':
    unittest.main() 