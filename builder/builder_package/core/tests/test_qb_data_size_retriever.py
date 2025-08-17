#!/usr/bin/env python3
"""
Unit tests for QBDataSizeRetriever tool call functionality
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import HTTPError
from typing import Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qb_data_size_retriever import QBDataSizeRetriever
from itool_call import IToolCall, ToolCallResult
from iauthenticator import IHTTPConnection
from cb_user import CBUser
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress logging from specific modules during tests
logging.getLogger('builder_package.core.qb_data_size_retriever').setLevel(logging.ERROR)
logging.getLogger('builder_package.core.http_retriever').setLevel(logging.ERROR)


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


class TestQBDataSizeRetriever(unittest.TestCase):
    """Test cases for QBDataSizeRetriever tool call functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_connection = MockHTTPConnection()
        self.mock_cb_user = MockCBUser()
        self.query = "SELECT COUNT(*) FROM Customer"
        
        self.retriever = QBDataSizeRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            query=self.query
        )

    def test_init(self):
        """Test QBDataSizeRetriever initialization"""
        self.assertEqual(self.retriever.query, self.query)
        self.assertEqual(self.retriever.connection, self.mock_connection)
        self.assertEqual(self.retriever.cb_user, self.mock_cb_user)
        self.assertIsNone(self.retriever.save_file_path)

    def test_init_with_save_file_path(self):
        """Test QBDataSizeRetriever initialization with save_file_path"""
        save_path = "test_file.jsonl"
        retriever = QBDataSizeRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            query=self.query,
            save_file_path=save_path
        )
        self.assertEqual(retriever.save_file_path, save_path)

    def test_is_query_valid(self):
        """Test is_query_valid method"""
        # Currently always returns True, but test the method exists
        self.assertTrue(self.retriever.is_query_valid())
        
        # Test with different queries
        retriever2 = QBDataSizeRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            query="SELECT COUNT(*) FROM Invoice"
        )
        self.assertTrue(retriever2.is_query_valid())

    def test_get_endpoint(self):
        """Test _get_endpoint method"""
        endpoint = self.retriever._get_endpoint()
        self.assertEqual(endpoint, "/query")

    def test_get_params(self):
        """Test _get_params method"""
        params = self.retriever._get_params()
        expected_params = {"query": self.query}
        self.assertEqual(params, expected_params)

    def test_extract_query_response_key_simple(self):
        """Test extract_query_response_key with simple FROM clause"""
        # Test simple FROM clause
        self.retriever.query = "SELECT COUNT(*) FROM Customer"
        key = self.retriever.extract_query_response_key()
        self.assertEqual(key, "Customer")

    def test_extract_query_response_key_with_where(self):
        """Test extract_query_response_key with WHERE clause"""
        # Test FROM clause with WHERE
        self.retriever.query = "SELECT COUNT(*) FROM Customer WHERE Active = true"
        key = self.retriever.extract_query_response_key()
        self.assertEqual(key, "Customer")

    def test_extract_query_response_key_with_order_by(self):
        """Test extract_query_response_key with ORDER BY clause"""
        # Test FROM clause with ORDER BY
        self.retriever.query = "SELECT COUNT(*) FROM Customer ORDER BY DisplayName"
        key = self.retriever.extract_query_response_key()
        self.assertEqual(key, "Customer")

    def test_extract_query_response_key_case_insensitive(self):
        """Test extract_query_response_key with case insensitive FROM"""
        # Test case insensitive FROM
        self.retriever.query = "SELECT COUNT(*) from Customer"
        key = self.retriever.extract_query_response_key()
        self.assertEqual(key, "Customer")

    def test_extract_query_response_key_complex_query(self):
        """Test extract_query_response_key with complex query"""
        # Test complex query with multiple clauses
        self.retriever.query = "SELECT COUNT(*) FROM Customer WHERE Active = true ORDER BY DisplayName LIMIT 100"
        key = self.retriever.extract_query_response_key()
        self.assertEqual(key, "Customer")

    def test_cache_key(self):
        """Test _cache_key method"""
        cache_key = self.retriever._cache_key()
        
        # Should start with expected prefix
        self.assertTrue(cache_key.startswith("qb_data_size_retriever_Customer_"))
        
        # Should contain table name
        self.assertIn("Customer", cache_key)
        
        # Should contain hash suffix
        self.assertTrue(len(cache_key) > len("qb_data_size_retriever_Customer_"))

    def test_cache_key_different_queries(self):
        """Test _cache_key generates different keys for different queries"""
        retriever1 = QBDataSizeRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            query="SELECT * FROM Customer"
        )
        retriever2 = QBDataSizeRetriever(
            connection=self.mock_connection,
            cb_user=self.mock_cb_user,
            query="SELECT * FROM Invoice"
        )
        
        key1 = retriever1._cache_key()
        key2 = retriever2._cache_key()
        
        self.assertNotEqual(key1, key2)

    def test_api_summary(self):
        """Test api_summary method"""
        summary = self.retriever.api_summary()
        expected = "Makes HTTP calls to retrieve number of rows in a query"
        self.assertEqual(summary, expected)

    def test_tool_name(self):
        """Test tool_name static method"""
        tool_name = QBDataSizeRetriever.tool_name()
        self.assertEqual(tool_name, "qb_data_size_retriever")

    def test_tool_description(self):
        """Test tool_description static method"""
        description = QBDataSizeRetriever.tool_description()
        
        self.assertEqual(description["type"], "function")
        self.assertEqual(description["function"]["name"], "qb_data_size_retriever")
        self.assertIn("Retrieve number of rows in a query from Quickbooks", description["function"]["description"])
        self.assertIn("query", description["function"]["parameters"]["properties"])

    def test_extract_result_summary(self):
        """Test extract_result_summary method"""
        mock_result = [{"QueryResponse": {"Customer": [{"id": 1}, {"id": 2}]}}]
        summary = self.retriever.extract_result_summary(mock_result)
        
        expected = {
            "description": "Retrieved number of rows in a query",
            "sample": mock_result
        }
        self.assertEqual(summary, expected)

    @patch('qb_data_size_retriever.QBDataSizeRetriever.retrieve')
    def test_call_tool_success(self, mock_retrieve):
        """Test call_tool method with successful response"""
        # Mock successful response
        mock_response = [{"QueryResponse": {"Customer": [{"id": 1}, {"id": 2}, {"id": 3}]}}]
        mock_retrieve.return_value = mock_response
        
        result = self.retriever.call_tool()
        
        # Verify success result
        self.assertEqual(result.status, "success")
        self.assertEqual(result.tool_name, "qb_data_size_retriever")
        self.assertIsNotNone(result.file_name)
        self.assertIn("Customer", result.file_name)
        self.assertIsNotNone(result.sample)

    @patch('qb_data_size_retriever.QBDataSizeRetriever.retrieve')
    def test_call_tool_no_data(self, mock_retrieve):
        """Test call_tool method with no data response"""
        # Mock empty response
        mock_retrieve.return_value = []
        
        result = self.retriever.call_tool()
        
        # Verify error result
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "qb_data_size_retriever")
        self.assertEqual(result.error_type, "NoData")
        self.assertEqual(result.error_message, "No data found")

    @patch('qb_data_size_retriever.QBDataSizeRetriever.retrieve')
    def test_call_tool_empty_query_response(self, mock_retrieve):
        """Test call_tool method with empty QueryResponse"""
        # Mock response with empty QueryResponse
        mock_retrieve.return_value = [{"QueryResponse": {}}]
        
        result = self.retriever.call_tool()
        
        # Verify error result
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "qb_data_size_retriever")
        self.assertEqual(result.error_type, "NoData")
        self.assertEqual(result.error_message, "No data found")

    @patch('qb_data_size_retriever.QBDataSizeRetriever.retrieve')
    def test_call_tool_http_error(self, mock_retrieve):
        """Test call_tool method with HTTP error"""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 400
        http_error = HTTPError("400 Bad Request", response=mock_response)
        mock_retrieve.side_effect = http_error
        
        result = self.retriever.call_tool()
        
        # Verify error result
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "qb_data_size_retriever")
        self.assertEqual(result.error_type, "HTTPError")
        self.assertEqual(result.status_code, 400)

    @patch('qb_data_size_retriever.QBDataSizeRetriever.retrieve')
    def test_call_tool_general_exception(self, mock_retrieve):
        """Test call_tool method with general exception"""
        # Mock general exception
        mock_retrieve.side_effect = Exception("General error")
        
        result = self.retriever.call_tool()
        
        # Verify error result
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "qb_data_size_retriever")
        self.assertEqual(result.error_type, "Exception")
        self.assertEqual(result.error_message, "General error")

    @patch('qb_data_size_retriever.QBDataSizeRetriever.retrieve')
    def test_call_tool_unauthorized_connection(self, mock_retrieve):
        """Test call_tool method with unauthorized connection"""
        # Create retriever with unauthorized connection
        unauthorized_connection = MockHTTPConnection(is_authorized=False)
        retriever = QBDataSizeRetriever(
            connection=unauthorized_connection,
            cb_user=self.mock_cb_user,
            query=self.query
        )
        
        # Mock exception for unauthorized connection
        mock_retrieve.side_effect = Exception("Entity test_cb_id is no longer connected")
        
        result = retriever.call_tool()
        
        # Verify error result
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "qb_data_size_retriever")
        self.assertEqual(result.error_type, "Exception")

    def test_to_json_success(self):
        """Test _to_json method with successful response"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "QueryResponse": {
                "Customer": [{"id": 1}, {"id": 2}, {"id": 3}]
            }
        }
        
        result, count = self.retriever._to_json(mock_response)
        
        # Verify result
        self.assertEqual(result, mock_response.json.return_value)
        self.assertEqual(count, 3)

    def test_to_json_empty_table(self):
        """Test _to_json method with empty table response"""
        # Mock response with empty table
        mock_response = Mock()
        mock_response.json.return_value = {
            "QueryResponse": {
                "Customer": []
            }
        }
        
        result, count = self.retriever._to_json(mock_response)
        
        # Verify result
        self.assertEqual(result, mock_response.json.return_value)
        self.assertEqual(count, 0)

    def test_to_json_no_query_response(self):
        """Test _to_json method with no QueryResponse"""
        # Mock response without QueryResponse
        mock_response = Mock()
        mock_response.json.return_value = {
            "error": "Invalid query"
        }
        
        result, count = self.retriever._to_json(mock_response)
        
        # Verify result
        self.assertEqual(result, mock_response.json.return_value)
        self.assertEqual(count, 0)

    def test_inheritance(self):
        """Test that QBDataSizeRetriever inherits from correct classes"""
        # Import the classes to test inheritance using the correct paths
        from builder_package.core.http_retriever import HTTPRetriever
        from builder_package.core.itool_call import IToolCall
        
        # Test inheritance from HTTPRetriever
        self.assertIsInstance(self.retriever, HTTPRetriever)
        # Test inheritance from IToolCall
        self.assertIsInstance(self.retriever, IToolCall)


if __name__ == '__main__':
    unittest.main() 