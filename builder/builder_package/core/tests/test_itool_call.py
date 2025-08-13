#!/usr/bin/env python3
"""
Unit tests for itool_call.py module
"""

import sys
import os
import json
import unittest
from unittest.mock import Mock, MagicMock
from typing import Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builder_package.core.itool_call import ToolCallResult, IToolCall
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockToolCall(IToolCall):
    """Mock implementation of IToolCall for testing"""
    
    def __init__(self, name="mock_tool", should_succeed=True):
        self._name = name
        self._should_succeed = should_succeed
    
    def call_tool(self) -> ToolCallResult:
        if self._should_succeed:
            return ToolCallResult.success(
                tool_name=self._name,
                file_name="mock_result.json",
                data={"result": "success", "value": 42}
            )
        else:
            return ToolCallResult.error(
                tool_name=self._name,
                error_type="MockError",
                error_message="This is a mock error"
            )
    
    def extract_result_summary(self, result: Any) -> dict:
        if isinstance(result, dict):
            return {
                "description": "Mock tool result summary",
                "result_type": type(result).__name__,
                "result_keys": list(result.keys()) if isinstance(result, dict) else None
            }
        return {"description": "Mock tool result", "result": str(result)}
    
    @staticmethod
    def tool_name() -> str:
        return "mock_tool"
    
    @staticmethod
    def tool_description() -> dict:
        return {
            "type": "function",
            "function": {
                "name": "mock_tool",
                "description": "A mock tool for testing"
            }
        }


class TestToolCallResult(unittest.TestCase):
    """Test cases for ToolCallResult class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.result = ToolCallResult()
    
    def test_init_default_values(self):
        """Test ToolCallResult initialization with default values"""
        self.assertIsNone(self.result.status)
        self.assertIsNone(self.result.tool_name)
        self.assertIsNone(self.result.error_type)
        self.assertIsNone(self.result.error_message)
        self.assertIsNone(self.result.status_code)
        self.assertIsNone(self.result.file_name)
        self.assertIsNone(self.result.data)
        self.assertIsNone(self.result.sample)
    
    def test_success_with_data(self):
        """Test ToolCallResult.success() with data parameter"""
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            data={"key": "value"}
        )
        
        self.assertEqual(result.status, "success")
        self.assertEqual(result.tool_name, "test_tool")
        self.assertEqual(result.file_name, "test.json")
        self.assertEqual(result.data, {"key": "value"})
        self.assertIsNone(result.sample)
    
    def test_success_with_sample(self):
        """Test ToolCallResult.success() with sample parameter"""
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            sample={"sample": "data"}
        )
        
        self.assertEqual(result.status, "success")
        self.assertEqual(result.tool_name, "test_tool")
        self.assertEqual(result.file_name, "test.json")
        self.assertIsNone(result.data)
        self.assertEqual(result.sample, {"sample": "data"})
    
    def test_success_with_both_data_and_sample_raises_error(self):
        """Test that providing both data and sample raises ValueError"""
        with self.assertRaises(ValueError) as context:
            ToolCallResult.success(
                tool_name="test_tool",
                file_name="test.json",
                data={"key": "value"},
                sample={"sample": "data"}
            )
        
        self.assertIn("data and sample cannot be provided together", str(context.exception))
    
    def test_success_without_data_or_sample_raises_error(self):
        """Test that providing neither data nor sample raises ValueError"""
        with self.assertRaises(ValueError) as context:
            ToolCallResult.success(
                tool_name="test_tool",
                file_name="test.json"
            )
        
        self.assertIn("data or sample must be provided", str(context.exception))
    
    def test_error(self):
        """Test ToolCallResult.error()"""
        result = ToolCallResult.error(
            tool_name="test_tool",
            error_type="TestError",
            error_message="Test error message",
            status_code=500
        )
        
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "test_tool")
        self.assertEqual(result.error_type, "TestError")
        self.assertEqual(result.error_message, "Test error message")
        self.assertEqual(result.status_code, 500)
    
    def test_error_without_status_code(self):
        """Test ToolCallResult.error() without status_code"""
        result = ToolCallResult.error(
            tool_name="test_tool",
            error_type="TestError",
            error_message="Test error message"
        )
        
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "test_tool")
        self.assertEqual(result.error_type, "TestError")
        self.assertEqual(result.error_message, "Test error message")
        self.assertIsNone(result.status_code)
    
    def test_to_json_wo_content_success(self):
        """Test to_json_wo_content() for success status"""
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            data={"key": "value"}
        )
        
        json_result = result.to_dict_wo_content()
        expected = {
            "status": "success",
            "tool_name": "test_tool",
            "content": {
                "file_name": "test.json"
            }
        }
        self.assertEqual(json_result, expected)
    
    def test_to_json_wo_content_error(self):
        """Test to_json_wo_content() for error status"""
        result = ToolCallResult.error(
            tool_name="test_tool",
            error_type="TestError",
            error_message="Test error message",
            status_code=500
        )
        
        json_result = result.to_dict_wo_content()
        expected = {
            "status": "error",
            "tool_name": "test_tool",
            "content": {
                "error_type": "TestError",
                "error_message": "Test error message",
                "status_code": 500
            }
        }
        self.assertEqual(json_result, expected)
    
    def test_to_json_wo_content_unset_status_raises_exception(self):
        """Test to_json_wo_content() with unset status raises Exception"""
        with self.assertRaises(Exception) as context:
            self.result.to_dict_wo_content()
        
        self.assertIn("Tool call result is not set", str(context.exception))
    
    def test_to_json_wo_content_invalid_status_raises_value_error(self):
        """Test to_json_wo_content() with invalid status raises ValueError"""
        self.result.status = "invalid"
        with self.assertRaises(ValueError) as context:
            self.result.to_dict_wo_content()
        
        self.assertIn("status must be success or error", str(context.exception))
    
    def test_to_dict_with_data(self):
        """Test to_dict() with data"""
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            data={"key": "value"}
        )
        
        json_result = result.to_dict()
        expected = {
            "status": "success",
            "tool_name": "test_tool",
            "content": {
                "file_name": "test.json",
                "data": {"key": "value"}
            }
        }
        self.assertEqual(json_result, expected)
    
    def test_to_dict_with_sample(self):
        """Test to_dict() with sample"""
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            sample={"sample": "data"}
        )
        
        json_result = result.to_dict()
        expected = {
            "status": "success",
            "tool_name": "test_tool",
            "content": {
                "file_name": "test.json",
                "sample": {"sample": "data"}
            }
        }
        self.assertEqual(json_result, expected)
    
    def test_to_dict_without_data_or_sample_raises_value_error(self):
        """Test to_dict() without data or sample raises ValueError"""
        # Create a result with data first, then manually clear it to test the error case
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            data={"key": "value"}
        )
        # Manually clear data and sample to test the error case
        result.data = None
        result.sample = None
        
        with self.assertRaises(ValueError) as context:
            result.to_dict()
        
        self.assertIn("data or sample must be provided", str(context.exception))
    
    def test_str_representation_with_data(self):
        """Test string representation of ToolCallResult with data"""
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            data={"key": "value"}
        )
        
        str_result = str(result)
        # Should be valid JSON
        parsed = json.loads(str_result)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["tool_name"], "test_tool")
        self.assertIn("data", parsed["content"])
    
    def test_str_representation_with_sample(self):
        """Test string representation of ToolCallResult with sample"""
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            sample={"sample": "data"}
        )
        
        str_result = str(result)
        # Should be valid JSON
        parsed = json.loads(str_result)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["tool_name"], "test_tool")
        self.assertIn("sample", parsed["content"])
    
    def test_str_representation_with_large_data(self):
        """Test string representation with large data that gets truncated"""
        large_data = {"long_string": "x" * 150}  # Data that will be > 100 chars when JSON serialized
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            data=large_data
        )
        
        str_result = str(result)
        parsed = json.loads(str_result)
        # Check that data is present and truncated
        self.assertIn("data", parsed["content"])
        data_content = parsed["content"]["data"]
        self.assertIsInstance(data_content, str)
        self.assertIn("...", data_content)
        # Check that it shows the actual length (which will be > 150 due to JSON formatting)
        self.assertGreater(len(data_content), 100)
    
    def test_str_representation_with_large_sample(self):
        """Test string representation with large sample that gets truncated"""
        large_sample = {"long_string": "x" * 150}  # Sample that will be > 100 chars when JSON serialized
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            sample=large_sample
        )
        
        str_result = str(result)
        parsed = json.loads(str_result)
        # Check that sample is present and truncated
        self.assertIn("sample", parsed["content"])
        sample_content = parsed["content"]["sample"]
        self.assertIsInstance(sample_content, str)
        self.assertIn("...", sample_content)
        # Check that it shows the actual length (which will be > 150 due to JSON formatting)
        self.assertGreater(len(sample_content), 100)
    
    def test_repr_representation(self):
        """Test repr representation of ToolCallResult"""
        result = ToolCallResult.success(
            tool_name="test_tool",
            file_name="test.json",
            data={"key": "value"}
        )
        
        repr_result = repr(result)
        # __repr__ returns a JSON string, not a dict
        self.assertIsInstance(repr_result, str)
        # Should be valid JSON
        parsed = json.loads(repr_result)
        self.assertEqual(parsed["status"], "success")
        self.assertEqual(parsed["tool_name"], "test_tool")


class TestIToolCall(unittest.TestCase):
    """Test cases for IToolCall abstract base class"""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that IToolCall cannot be instantiated directly"""
        with self.assertRaises(TypeError):
            IToolCall()
    
    def test_mock_implementation_works(self):
        """Test that MockToolCall properly implements IToolCall"""
        mock_tool = MockToolCall()
        
        # Test that it can be instantiated
        self.assertIsInstance(mock_tool, IToolCall)
        
        # Test tool_name
        self.assertEqual(mock_tool.tool_name(), "mock_tool")
        
        # Test tool_description
        description = mock_tool.tool_description()
        self.assertIsInstance(description, dict)
        self.assertEqual(description["function"]["name"], "mock_tool")
    
    def test_successful_tool_call(self):
        """Test successful tool call execution"""
        mock_tool = MockToolCall(should_succeed=True)
        result = mock_tool.call_tool()
        
        self.assertEqual(result.status, "success")
        self.assertEqual(result.tool_name, "mock_tool")
        self.assertEqual(result.file_name, "mock_result.json")
        self.assertEqual(result.data["result"], "success")
        self.assertEqual(result.data["value"], 42)
    
    def test_failed_tool_call(self):
        """Test failed tool call execution"""
        mock_tool = MockToolCall(should_succeed=False)
        result = mock_tool.call_tool()
        
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "mock_tool")
        self.assertEqual(result.error_type, "MockError")
        self.assertEqual(result.error_message, "This is a mock error")
    
    def test_extract_result_summary(self):
        """Test extract_result_summary method"""
        mock_tool = MockToolCall()
        test_data = {"key1": "value1", "key2": "value2"}
        
        summary = mock_tool.extract_result_summary(test_data)
        
        self.assertEqual(summary["description"], "Mock tool result summary")
        self.assertEqual(summary["result_type"], "dict")
        self.assertEqual(summary["result_keys"], ["key1", "key2"])
    
    def test_extract_result_summary_with_non_dict(self):
        """Test extract_result_summary with non-dict data"""
        mock_tool = MockToolCall()
        test_data = "simple string"
        
        summary = mock_tool.extract_result_summary(test_data)
        
        self.assertEqual(summary["description"], "Mock tool result")
        self.assertEqual(summary["result"], "simple string")


if __name__ == '__main__':
    unittest.main() 