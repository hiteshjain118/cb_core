from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IGPTTool(ABC):
    @abstractmethod
    def get_tool_schema(self) -> List[Dict[str, Any]]:
        pass 