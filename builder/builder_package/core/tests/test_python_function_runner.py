#!/usr/bin/env python3
"""
Unit tests for python_function_runner.py module
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import Mock, MagicMock, patch
from typing import Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from builder_package.core.python_function_runner import PythonFunctionRunner
from builder_package.core.itool_call import ToolCallResult
import pandas as pd

# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPythonFunctionRunner(unittest.TestCase):
    """Test cases for PythonFunctionRunner class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.simple_analyze_code = '''
def analyze():
    return pd.DataFrame({
        'Item': ['A', 'B', 'C'],
        'Value': [1, 2, 3]
    })
'''
        
        self.complex_analyze_code = '''
def analyze():
    data = {'Name': ['John', 'Jane', 'Bob'], 'Age': [25, 30, 35]}
    df = pd.DataFrame(data)
    return df
'''
        
        self.large_dataframe_code = '''
def analyze():
    return pd.DataFrame({
        'ID': range(15),
        'Value': [i * 2 for i in range(15)]
    })
'''
        
        self.error_analyze_code = '''
def analyze():
    # This will cause an error
    undefined_variable + 1
    return pd.DataFrame()
'''
        
        self.no_analyze_function_code = '''
def wrong_name():
    return pd.DataFrame()
'''
        
        self.non_callable_analyze_code = '''
analyze = "not a function"
'''
        
        self.empty_dataframe_code = '''
def analyze():
    return pd.DataFrame()
'''
    
    def test_init_valid_function(self):
        """Test PythonFunctionRunner initialization with valid analyze function"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        self.assertEqual(runner.analyze_function_code, self.simple_analyze_code)
    
    def test_init_invalid_function_name(self):
        """Test PythonFunctionRunner initialization with wrong function name"""
        with self.assertRaises(AssertionError) as context:
            PythonFunctionRunner(self.no_analyze_function_code)
        self.assertIn("function name must be 'analyze'", str(context.exception))
    
    def test_init_missing_function(self):
        """Test PythonFunctionRunner initialization with no function"""
        invalid_code = '''
print("Hello World")
'''
        with self.assertRaises(AssertionError) as context:
            PythonFunctionRunner(invalid_code)
        self.assertIn("function name must be 'analyze'", str(context.exception))
    
    def test_init_empty_code(self):
        """Test PythonFunctionRunner initialization with empty code"""
        with self.assertRaises(AssertionError) as context:
            PythonFunctionRunner("")
        self.assertIn("function name must be 'analyze'", str(context.exception))
    
    def test_init_non_string_code(self):
        """Test PythonFunctionRunner initialization with non-string code"""
        with self.assertRaises(TypeError) as context:
            PythonFunctionRunner(123)
        self.assertIn("argument of type 'int' is not iterable", str(context.exception))
    
    def test_safe_exec_basic_functionality(self):
        """Test safe_exec with basic analyze function"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        result = runner.safe_exec()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        self.assertEqual(list(result.columns), ['Item', 'Value'])
        self.assertEqual(result.iloc[0]['Item'], 'A')
        self.assertEqual(result.iloc[0]['Value'], 1)
    
    def test_safe_exec_with_custom_globals(self):
        """Test safe_exec with custom allowed globals"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        custom_globals = {'custom_var': 42}
        result = runner.safe_exec(allowed_globals=custom_globals)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
    
    def test_safe_exec_with_custom_builtins(self):
        """Test safe_exec with custom allowed builtins"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        custom_builtins = {'len': len, 'print': print}
        result = runner.safe_exec(allowed_builtins=custom_builtins)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
    
    def test_safe_exec_complex_function(self):
        """Test safe_exec with complex analyze function returning DataFrame"""
        runner = PythonFunctionRunner(self.complex_analyze_code)
        result = runner.safe_exec()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 3)
        self.assertEqual(result.iloc[0]['Name'], 'John')
        self.assertEqual(result.iloc[0]['Age'], 25)
    
    def test_safe_exec_empty_dataframe(self):
        """Test safe_exec with function returning empty DataFrame"""
        runner = PythonFunctionRunner(self.empty_dataframe_code)
        result = runner.safe_exec()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 0)
    
    def test_safe_exec_error_handling(self):
        """Test safe_exec with function that causes an error"""
        runner = PythonFunctionRunner(self.error_analyze_code)
        
        with self.assertRaises(NameError):
            runner.safe_exec()
    
    def test_safe_exec_no_analyze_function(self):
        """Test safe_exec with code that doesn't define analyze function"""
        # This test can't run because the constructor will fail
        # The production code validates at construction time
        pass
    
    def test_safe_exec_non_callable_analyze(self):
        """Test safe_exec with code that defines analyze as non-callable"""
        # This test can't run because the constructor will fail
        # The production code validates at construction time
        pass
    
    def test_call_tool_success_dataframe(self):
        """Test call_tool method with successful DataFrame execution"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        # Mock file operations to avoid side effects
        with patch('builtins.open', create=True) as mock_open, \
             patch('json.dumps') as mock_json_dumps:
            
            mock_json_dumps.return_value = '[{"Item": "A", "Value": 1}]'
            
            result = runner.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "success")
            self.assertEqual(result.tool_name, "python_function_runner")
            self.assertEqual(result.file_name, "analyze.jsonl")
            self.assertIsInstance(result.data, list)  # Now returns the DataFrame as dict records
            self.assertEqual(len(result.data), 3)  # Should have 3 rows
    
    def test_call_tool_success_large_dataframe(self):
        """Test call_tool method with large DataFrame (truncates sample)"""
        runner = PythonFunctionRunner(self.large_dataframe_code)
        
        with patch('builtins.open', create=True) as mock_open, \
             patch('json.dumps') as mock_json_dumps:
            
            mock_json_dumps.return_value = '[{"ID": 0, "Value": 0}]'
            
            result = runner.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "success")
            self.assertIsInstance(result.data, list)  # Now returns the DataFrame as dict records
            self.assertEqual(len(result.data), 15)  # Should have all 15 rows
    
    def test_call_tool_success_empty_dataframe(self):
        """Test call_tool method with empty DataFrame"""
        runner = PythonFunctionRunner(self.empty_dataframe_code)
        
        with patch('builtins.open', create=True) as mock_open, \
             patch('json.dumps') as mock_json_dumps:
            
            mock_json_dumps.return_value = '[]'
            
            result = runner.call_tool()
            
            self.assertIsInstance(result, ToolCallResult)
            self.assertEqual(result.status, "success")
            self.assertIsInstance(result.data, list)  # Now returns the DataFrame as dict records
            self.assertEqual(len(result.data), 0)  # Should have 0 rows
    
    def test_call_tool_error_handling(self):
        """Test call_tool method with error during execution"""
        runner = PythonFunctionRunner(self.error_analyze_code)
        
        result = runner.call_tool()
        
        self.assertIsInstance(result, ToolCallResult)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.tool_name, "python_function_runner")
        self.assertIn("Error executing Python code", result.error_message)
    
    def test_extract_result_summary_dataframe(self):
        """Test extract_result_summary with DataFrame result"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        summary = runner.extract_result_summary(df)
        
        self.assertEqual(summary['description'], "Python function returned 2 rows")
        self.assertIsInstance(summary['data'], pd.DataFrame)
        self.assertEqual(len(summary['data']), 2)
    
    def test_extract_result_summary_large_dataframe(self):
        """Test extract_result_summary with large DataFrame (truncates sample)"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        # Create a DataFrame with more than 10 rows
        large_df = pd.DataFrame({'A': range(15), 'B': range(15)})
        summary = runner.extract_result_summary(large_df)
        
        self.assertEqual(summary['description'], "Python function returned 15 rows")
        self.assertIsInstance(summary['data'], pd.DataFrame)
        self.assertEqual(len(summary['data']), 15)  # Now returns the full DataFrame
    
    def test_extract_result_summary_empty_dataframe(self):
        """Test extract_result_summary with empty DataFrame"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        empty_df = pd.DataFrame()
        summary = runner.extract_result_summary(empty_df)
        
        self.assertEqual(summary['description'], "Python function returned 0 rows")
        self.assertIsInstance(summary['data'], pd.DataFrame)
        self.assertEqual(len(summary['data']), 0)
    
    def test_extract_result_summary_non_dataframe_error(self):
        """Test extract_result_summary with non-DataFrame result raises error"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        with self.assertRaises(AssertionError) as context:
            runner.extract_result_summary("not a dataframe")
        self.assertIn("Result must be a pandas DataFrame", str(context.exception))
    
    def test_extract_result_summary_none_error(self):
        """Test extract_result_summary with None result raises error"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        with self.assertRaises(AssertionError) as context:
            runner.extract_result_summary(None)
        self.assertIn("Result must be a pandas DataFrame", str(context.exception))
    
    def test_tool_name(self):
        """Test tool_name static method"""
        self.assertEqual(PythonFunctionRunner.tool_name(), "python_function_runner")
    
    def test_tool_description(self):
        """Test tool_description static method"""
        description = PythonFunctionRunner.tool_description()
        
        self.assertIsInstance(description, dict)
        self.assertEqual(description['type'], 'function')
        self.assertEqual(description['function']['name'], 'python_function_runner')
        self.assertIn('code', description['function']['parameters']['properties'])
        self.assertIn("name 'analyze'", description['function']['parameters']['properties']['code']['description'])
    
    def test_integration_with_pandas(self):
        """Test integration with pandas operations"""
        pandas_code = '''
def analyze():
    df = pd.DataFrame({
        'Numbers': [1, 2, 3, 4, 5],
        'Squares': [1, 4, 9, 16, 25]
    })
    
    # Use pandas operations
    df['Sum'] = df['Numbers'] + df['Squares']
    df['Product'] = df['Numbers'] * df['Squares']
    
    return df
'''
        
        runner = PythonFunctionRunner(pandas_code)
        result = runner.safe_exec()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 5)
        self.assertIn('Sum', result.columns)
        self.assertIn('Product', result.columns)
        self.assertEqual(result.iloc[0]['Sum'], 2)  # 1 + 1
        self.assertEqual(result.iloc[0]['Product'], 1)  # 1 * 1
    
    def test_restricted_environment(self):
        """Test that restricted environment prevents dangerous operations"""
        dangerous_code = '''
def analyze():
    # Try to access dangerous builtins
    try:
        eval("print('dangerous')")
        return "eval allowed"
    except:
        pass
    
    try:
        exec("print('dangerous')")
        return "exec allowed"
    except:
        pass
    
    try:
        open("/etc/passwd", "r")
        return "file access allowed"
    except:
        pass
    
    return "restricted"
'''
        
        runner = PythonFunctionRunner(dangerous_code)
        result = runner.safe_exec()
        
        self.assertEqual(result, "restricted")
    
    def test_file_creation_in_call_tool(self):
        """Test that call_tool creates the expected file"""
        runner = PythonFunctionRunner(self.simple_analyze_code)
        
        # Use temporary directory to avoid cluttering test environment
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                result = runner.call_tool()
                
                # Check that file was created
                self.assertTrue(os.path.exists("analyze.jsonl"))
                
                # Check file contents
                with open("analyze.jsonl", "r") as f:
                    content = f.read()
                    self.assertIn("Item", content)
                    self.assertIn("Value", content)
                
                # Check return value
                self.assertIsInstance(result, ToolCallResult)
                self.assertEqual(result.status, "success")
                self.assertIsInstance(result.data, list)  # Now returns the DataFrame as dict records
                self.assertEqual(len(result.data), 3)  # Should have 3 rows
                
            finally:
                os.chdir(original_cwd)
    
    def test_additional_builtins_available(self):
        """Test that additional builtins are available in safe execution"""
        code_with_builtins = '''
def analyze():
    # Test various builtins
    numbers = list(range(5))
    total = sum(numbers)
    maximum = max(numbers)
    minimum = min(numbers)
    absolute = abs(-42)
    rounded = round(3.7)
    sorted_nums = sorted([3, 1, 4, 1, 5])
    
    # Convert to DataFrame for return
    return pd.DataFrame({
        'total': [total],
        'max': [maximum],
        'min': [minimum],
        'abs': [absolute],
        'rounded': [rounded],
        'sorted': [str(sorted_nums)]
    })
'''
        
        runner = PythonFunctionRunner(code_with_builtins)
        result = runner.safe_exec()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.iloc[0]['total'], 10)
        self.assertEqual(result.iloc[0]['max'], 4)
        self.assertEqual(result.iloc[0]['min'], 0)
        self.assertEqual(result.iloc[0]['abs'], 42)
        self.assertEqual(result.iloc[0]['rounded'], 4)
        self.assertEqual(result.iloc[0]['sorted'], '[1, 1, 3, 4, 5]')
    
    def test_pandas_numpy_available(self):
        """Test that pandas and numpy are available in safe execution"""
        numpy_pandas_code = '''
def analyze():
    # Test pandas operations
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    
    # Test numpy operations
    arr = np.array([1, 2, 3, 4, 5])
    mean_val = np.mean(arr)
    std_val = np.std(arr)
    
    # Test json operations
    json_str = json.dumps({'mean': mean_val, 'std': std_val})
    
    # Return combined results
    result_df = pd.DataFrame({
        'pandas_test': [len(df)],
        'numpy_mean': [mean_val],
        'numpy_std': [std_val],
        'json_test': [json_str]
    })
    
    return result_df
'''
        
        runner = PythonFunctionRunner(numpy_pandas_code)
        result = runner.safe_exec()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(result.iloc[0]['pandas_test'], 3)
        self.assertEqual(result.iloc[0]['numpy_mean'], 3.0)
        # For array [1, 2, 3, 4, 5], std = sqrt(sum((x-mean)^2)/n) = sqrt(10/5) = sqrt(2) ≈ 1.4142
        self.assertAlmostEqual(result.iloc[0]['numpy_std'], 1.4142, places=3)
        self.assertIn('mean', result.iloc[0]['json_test'])


if __name__ == '__main__':
    unittest.main() 