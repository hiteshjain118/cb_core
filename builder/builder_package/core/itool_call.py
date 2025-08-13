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
        self.file_name = None
        self.data = None
        #if the output is too large, we can provide an sample of the output
        self.sample = None

    @staticmethod
    def success(
        tool_name: str,
        file_name: str, 
        data: dict = None,
        sample: dict = None
    ) -> 'ToolCallResult':
        result = ToolCallResult()
        result.status = "success"
        result.tool_name = tool_name
        result.file_name = file_name
        
        if data is not None and sample is not None:
            raise ValueError("data and sample cannot be provided together")
        elif data is not None:
            result.data = data
        elif sample is not None:
            result.sample = sample 
        else:
            raise ValueError("data or sample must be provided")
        
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
    
    def to_dict(self) -> dict:
        json_wo_content = self.to_dict_wo_content()

        if self.status == "success":
            if self.data is not None:
                json_wo_content["content"]["data"] = self.data
            elif self.sample is not None:
                json_wo_content["content"]["sample"] = self.sample
            else:
                raise ValueError("data or sample must be provided")

        return json_wo_content

    def to_dict_wo_content(self) -> dict:
        if self.status is None:
            raise Exception("Tool call result is not set")
        elif self.status == "success":
            content = {
                "file_name": self.file_name,
            }
        elif self.status == "error":
            content = {
                "error_type": self.error_type,
                "error_message": self.error_message,
                "status_code": self.status_code,
            }
        else:
            raise ValueError("status must be success or error")
        return {
            "status": self.status,
            "tool_name": self.tool_name,
            "content": content,
        }


    def __str__(self) -> str:
        content_json = self.to_dict_wo_content()
        if self.status == "success":
            # Handle data truncation - convert to string and truncate if too long
            if self.data is not None:
                data_str = json.dumps(self.data)
                if len(data_str) > 100:
                    content_json['content']["data"] = f"{data_str[:100]}...{len(data_str)}"
                else:
                    content_json['content']["data"] = self.data
            
            # Handle sample truncation - convert to string and truncate if too long
            if self.sample is not None:
                sample_str = json.dumps(self.sample)
                if len(sample_str) > 100:
                    content_json['content']["sample"] = f"{sample_str[:100]}...{len(sample_str)}"
                else:
                    content_json['content']["sample"] = self.sample
        return json.dumps(content_json)

    def __repr__(self) -> str:
        return json.dumps(self.to_dict())

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