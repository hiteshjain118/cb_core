from abc import ABC, abstractmethod
from typing import Any
import json

class ToolCallResult:
    def __init__(self):
        self.status = None
        self.tool_name = None
        # error fields
        self.error_type = None
        self.error_message = None
        self.status_code = None

        # success fields
        self.handle_name = None
        self.content = None

    @staticmethod
    def success(
        tool_name: str,
        handle_name: str, 
        data: dict
    ) -> 'ToolCallResult':
        result = ToolCallResult()
        result.status = "success"
        result.tool_name = tool_name
        result.handle_name = handle_name
        result.content = data
        return result
    
    @staticmethod
    def error(
        tool_name: str,
        error_type: str, 
        error_message: str, 
        status_code: int = None
    ) -> 'ToolCallResult':
        result = ToolCallResult()
        result.tool_name = tool_name
        result.status = "error"
        result.error_type = error_type
        result.error_message = error_message
        result.status_code = status_code
        return result
    
    def to_json(self) -> dict:
        if self.status is None:
            raise Exception("Tool call result is not set")
        
        return {
            "status": self.status,
            "tool_name": self.tool_name,
            "content": {
                "error_type": self.error_type,
                "error_message": self.error_message,
                "status_code": self.status_code,
            } if self.status == "error" else {
                "handle_name": self.handle_name,
                "content": self.content,
            }
        }

    def to_json_wo_content(self) -> dict:
        return {
            "status": self.status,
            "tool_name": self.tool_name,
            "content": {
                "error_type": self.error_type,
                "error_message": self.error_message,
                "status_code": self.status_code,
            } if self.status == "error" else {
                "handle_name": self.handle_name,
            }
        }

    def __str__(self) -> str:
        if self.status == "error":
            content = {
                "error_type": self.error_type,
                "error_message": self.error_message,
                "status_code": self.status_code,
            }
        else:
            content_json = json.dumps(self.content)
            content = {
                "handle_name": self.handle_name,
                "content": f"{content_json[:100]}...{len(content_json)}" if len(content_json) > 100 else content_json,
            }
        return json.dumps({
            "status": self.status,
            "tool_name": self.tool_name,
            "content": content,
        })

    def __repr__(self) -> str:
        return self.to_json()

class IToolCall(ABC):
    @abstractmethod
    def call_tool(self) -> ToolCallResult:
        # returns a dict with the following keys:
        # {
        # 'status': 'success' | 'error',
        # 'content': json object {
        #    ?'error': 'error_type',
        #    ?'error_message': 'error_message',
        #    ?'handle': 'handle_name',
        #    ?'data': json object
        #  }
        #}
        raise NotImplementedError("call_tool is not implemented")

    @staticmethod
    def tool_name() -> str:
        pass

    @abstractmethod
    def extract_result_summary(self, result: Any) -> dict:
        pass

    @staticmethod
    def tool_description() -> dict:
        pass