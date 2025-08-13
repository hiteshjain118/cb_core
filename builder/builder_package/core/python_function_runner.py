import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from builder_package.core.itool_call import IToolCall, ToolCallResult
from typing import Any, Union
import builtins
import pandas as pd
import numpy as np
import json
import logging

logger = logging.getLogger(__name__)

class PythonFunctionRunner(IToolCall):
    def __init__(
            self, 
            analyze_function_code: str,
            # argument_handles: dict[str, str]
        ):
        assert ('def analyze' in analyze_function_code), "function name must be 'analyze'"
        self.analyze_function_code = analyze_function_code
        # self.argument_handles = argument_handles

    def safe_exec(self, allowed_globals=None, allowed_builtins=None):
        """
        Safely execute Python code in a restricted namespace.

        :param allowed_globals: Modules and variables allowed in global scope.
        :param allowed_builtins: Built-in functions to expose (optional).
        :return: Result from the analyze function execution.
        """
        safe_builtins = {
            "print": print,
            "range": range,
            "len": len,
            "min": min,
            "max": max,
            "sum": sum,
            "isinstance": isinstance,
            "enumerate": enumerate,
            "__import__": __import__,
            "open": open,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "sorted": sorted,
            "abs": abs,
            "round": round,
            "zip": zip,
            "filter": filter,
            "map": map,
            "any": any,
            "all": all,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
            "delattr": delattr,
            "callable": callable,
            "issubclass": issubclass,
            "super": super,
            "property": property,
            "staticmethod": staticmethod,
            "classmethod": classmethod
        }
        namespace_globals = {
            "__builtins__": safe_builtins,
            "pd": pd,
            "np": np,
            "json": json,
        }
        namespace_locals = {}

        # if allowed_globals is None:
        #     allowed_globals = {}

        # if allowed_builtins is None:
        #     allowed_builtins = {
        #         "len": len,
        #         "sum": sum,
        #         "min": min,
        #         "max": max,
        #         "range": range,
        #         "print": print,
        #         "sorted": sorted,
        #         "abs": abs,
        #         "round": round,
        #         "str": str,
        #         "int": int,
        #         "float": float,
        #         "bool": bool,
        #         "list": list,
        #         "dict": dict,
        #         "tuple": tuple,
        #         "set": set
        #     }

        # # Add pandas and numpy to allowed globals
        # safe_globals = {
        #     "pd": pd,
        #     "np": np,
        #     "json": json,
        #     **allowed_globals
        # }

        # # Construct the safe global namespace
        # globals_dict = {
        #     "__builtins__": allowed_builtins,
        #     **safe_globals,
        # }

        # # Local namespace to capture definitions like analyze()
        # locals_dict = {}

        # Execute the code in restricted environment
        # Replace deprecated import with current pandas method
        modified_code = self.analyze_function_code.replace(
            "from pandas.io.json import json_normalize",
            "# from pandas.io.json import json_normalize  # deprecated, using pd.json_normalize instead"
        )
        modified_code = modified_code.replace(
            "json_normalize(",
            "pd.json_normalize("
        )
        
        # Fix any double pd.pd issues
        modified_code = modified_code.replace("pd.pd.json_normalize", "pd.json_normalize")
        
        logger.info(f"Original code:\n{self.analyze_function_code}")
        logger.info(f"Modified code:\n{modified_code}")
        
        exec(modified_code, namespace_globals, namespace_locals)

        # Get the analyze function
        analyze_func = namespace_locals.get('analyze')
        if analyze_func is None:
            raise RuntimeError("No 'analyze' function found in the provided code")
        
        if not callable(analyze_func):
            raise RuntimeError("The 'analyze' variable is not callable")
        
        # Execute the analyze function
        result = analyze_func()
        logger.info(f"Successfully executed analyze function, result type: {type(result)}")
        return result
        
    def call_tool(self) -> ToolCallResult:
        """Execute the Python code and return the result""" 
        try:
            result = self.safe_exec() # returns dataframe
            result_summary = self.extract_result_summary(result)
            
            result = result.to_dict(orient='records')
            file_name = "analyze.jsonl"
            with open(file_name, "w") as f:
                f.write(json.dumps(result))
            return ToolCallResult.success(
                tool_name=self.tool_name(),
                file_name=file_name,
                data=result,
            )
        except Exception as e:
            return ToolCallResult.error(
                tool_name=self.tool_name(),
                error_type="InternalError",
                error_message=f"Error executing Python code: {str(e)}"
            )
        
    def extract_result_summary(self, result: Any) -> dict:
        """Extract a summary from the execution result"""

        assert isinstance(result, pd.DataFrame), "Result must be a pandas DataFrame"
        return {
            "description": f"Python function returned {len(result)} rows",
            "data": result
        }
    
    @staticmethod
    def tool_name() -> str:
        return "python_function_runner"
    
    @staticmethod
    def tool_description() -> dict:
        return {
            "type": "function",
            "function": {
                "name": "python_function_runner",
                "description": "Run Python function for data analysis and processing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python function with name 'analyze' to execute"
                        }
                    },
                    "required": ["code"]
                }
            }
        }