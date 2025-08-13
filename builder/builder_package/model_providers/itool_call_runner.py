from abc import ABC, abstractmethod
from builder_package.core.itool_call import IToolCall, ToolCallResult
from openai.types.chat import ChatCompletionMessageToolCall


class IToolCallRunner(ABC):
    @abstractmethod
    def run_tool(self, tool_call: ChatCompletionMessageToolCall) -> ToolCallResult:
        pass
    
    @staticmethod
    def enabled_tools() -> list[IToolCall]:
        pass
    
    @staticmethod
    def enabled_tool_descriptions() -> list[dict]:
        pass
