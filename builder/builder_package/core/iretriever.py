from abc import ABC, abstractmethod
from typing import Any, List, Dict

class ICacheable(ABC):
    @abstractmethod
    def _cache_key(self) -> str:
        pass
    
    @abstractmethod
    def try_cache(self) -> Any:
        pass
    
    @abstractmethod
    def cache(self, responses: List[Dict[str, Any]]) -> None:
        pass
    
class IRetriever(ICacheable):
    @abstractmethod
    def retrieve(self) -> Any:
        # raises exception if retrieval fails
        pass

    @abstractmethod
    def api_summary(self) -> str:
        pass

