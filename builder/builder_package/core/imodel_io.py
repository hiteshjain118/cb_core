from abc import ABC
import json
import logging
from typing import Any, Self

from openai.types.chat import ChatCompletionMessage
from builder_package.core.enums import IntentName
from builder_package.model_providers.itool_call_runner import IToolCallRunner
from builder_package.core.itool_call import ToolCallResult

class IModelPrompt(ABC):
    def get_messages(self) -> list[dict]:
        pass

    def get_system_prompt(self) -> str:
        pass

    @staticmethod
    def message_from_tool_call_result(
        tool_call_id: str, 
        tool_call_result: ToolCallResult
    ) -> dict:
        return {
            'role': 'tool',
            'tool_call_id': tool_call_id,
            'name': tool_call_result.tool_name,
            'content': json.dumps(tool_call_result.to_dict()),
        }
    
class IModelOutputParser(ABC):
    def set_success(self, response_content: str, tool_calls: list[dict] = []) -> Self:
        pass
    
    def set_error(self, error_reason: str) -> Self:
        pass

    def get_output(self) -> dict:
        pass

class DefaultModelOutputParser(IModelOutputParser):
    def __init__(self):
        self.response_content = None
        self.error_reason = None
        self.tool_calls = None

    def set_success(self, response_content: str, tool_calls: list[dict] = []) -> Self:
        self.response_content = response_content
        self.tool_calls = tool_calls
        return self

    def set_error(self, error_reason: str) -> Self:
        self.error_reason = error_reason
        return self
    
    def get_output(self) -> dict:
        return {
            "is_successful": (self.response_content is not None or self.tool_calls is not None) and self.error_reason is None,
            "response_content": self.response_content,
            "error_reason": self.error_reason,
            "tool_calls": self.tool_calls,
        }

class QBModelOutputParser(IModelOutputParser):
    def __init__(self, tool_call_runner: IToolCallRunner):
        self.response_content: str = None
        self.error_reason: str = None
        self.tool_calls: dict[str, ToolCallResult] = None
        self.message: ChatCompletionMessage = None
        self.tool_call_runner = tool_call_runner
        self.attachments = []

    def set_success(self, message: ChatCompletionMessage) -> Self:
        self.message = message
        self.response_content = message.content
        # self.response_content = message.content["response_content"]
        # self.attachments = message.content.get("attachments", [])
        if message.tool_calls is not None:
            self.tool_calls = {}
            for tool_call in message.tool_calls:
                result = self.tool_call_runner.run_tool(tool_call)
                self.tool_calls[tool_call.id] = result
        return self

    def set_error(self, error_reason: str) -> Self:
        self.error_reason = error_reason
        return self
    
    def get_output(self) -> dict:
        if self.tool_calls is not None:
            for tool_call_id, tool_call in self.tool_calls.items():
                if tool_call.status == "error":
                    self.error_reason = f"tool call {tool_call_id} failed"
                    break
        return {
            "is_successful": self.response_content is not None and len(self.response_content) > 0 and self.error_reason is None,
            "response_content": self.response_content,
            "attachments": self.attachments,
            "error_reason": self.error_reason,
            "tool_calls": self.tool_calls,
        }


class ModelIO:
    def __init__(
        self, 
        prompt: IModelPrompt, 
        output_parser: IModelOutputParser = None,
        output_parser_class: type[IModelOutputParser] = None, 
        intent: IntentName = None,
    ):
        self.prompt = prompt
        self.intent = intent
        if output_parser is None and output_parser_class is None:
            raise ValueError("Either output_parser or output_parser_class must be provided")
        if output_parser is not None and output_parser_class is not None:
            raise ValueError("Only one of output_parser or output_parser_class must be provided")
        if output_parser is not None:
            self.output_parser = output_parser
        else:
            self.output_parser = output_parser_class()
    