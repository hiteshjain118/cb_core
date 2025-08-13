from abc import ABC, abstractmethod
from typing import Any

class IRetriever(ABC):
    @abstractmethod
    def retrieve(self) -> Any:
        # raises exception if retrieval fails
        pass

    @abstractmethod
    def api_summary(self) -> str:
        pass

    @abstractmethod
    def _cache_key(self) -> str:
        pass