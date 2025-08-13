from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from builder_package.core.imodel_io import IModelOutputParser, ModelIO


class IModelProvider(ABC):
    """Interface for different model providers (OpenAI, TogetherAI, etc.)"""
    
    @abstractmethod
    def get_response(
        self, 
        model_io: ModelIO,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> IModelOutputParser:
        """
        Get a response from the model provider.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the model being used"""
        pass 