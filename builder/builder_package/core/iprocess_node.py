from abc import ABC, abstractmethod
from typing import Any

class IProcessNode (ABC):
    @abstractmethod
    def process(self) -> Any:
        pass
    
    @abstractmethod
    def empty_value_reason(self) -> str:
        pass

    @abstractmethod
    def _describe_for_logging(self, output: Any) -> str:
        pass


class RetrievalProcessNode (IProcessNode):
    @abstractmethod
    def process(self) -> Any:
        pass
    
    @abstractmethod
    def empty_value_reason(self) -> str:
        pass

    @abstractmethod
    def _describe_for_logging(self, output: Any) -> str:
        pass

    @abstractmethod
    def _process_one_response(self, response: Any) -> Any:
        pass
    