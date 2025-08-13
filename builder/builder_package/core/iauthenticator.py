from abc import ABC, abstractmethod
from typing import Any

class IHTTPConnection(ABC):
    @abstractmethod
    def authenticate(self) -> str:
        pass

    @abstractmethod
    def is_authorized(self) -> bool:
        pass

    @abstractmethod
    def get_cbid(self) -> str:
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        pass

    @abstractmethod
    def get_valid_access_token_not_throws(self) -> str:
        pass

    @abstractmethod
    def get_remote_user(self) -> Any:
        pass