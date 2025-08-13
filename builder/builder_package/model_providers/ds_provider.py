
import logging
from typing import List, Dict, Any
from builder_package.model_providers.imodel_provider import IModelProvider
from openai import OpenAI


class DSProvider(IModelProvider):
    """DeepSeek model provider implementation using Deep Infra via OpenAI client"""

    SETTINGS = {
        'deep_infra': {
            'base_url': 'https://api.deepinfra.com/v1/openai',
            'api_key': 'VvpenkKnZVXQZJfGeBFZYXks6sdBCF2Z',
            'model': 'deepseek-ai/DeepSeek-V3'
        },
        'together': {
            'base_url': 'https://api.together.xyz/v1',
            'api_key': '81639fc05868d3ee052fdce04a79e2ce77840e166d6eaef2e087b41a034438e0',
            'model': 'deepseek-ai/DeepSeek-V3'
        }
    }    
    def __init__(self, settings: dict):
        """
        Initialize the DeepSeek provider.
        
        Args:
            api_key: Deep Infra API key
            model: Model name to use (default: deepseek-coder-33b-instruct)
        """
        self.api_key = settings['api_key']
        self.model = settings['model']
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=settings['base_url']
        )

        logging.info(f"Initialized DSProvider with model: {self.model}")
    
    def get_response(
        self, 
        messages: List[Dict[str, Any]], 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Get a response from DeepSeek model via Deep Infra using OpenAI client.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional OpenAI-compatible parameters
            
        Returns:
            Generated response text
        """
        
        logging.info(f"about to call together api with model: {self.model}, #messages: {len(messages)}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        logging.info(f"Response: {response.choices[0].message.content.strip()}")
        return response.choices[0].message.content.strip()
    
    def get_model_name(self) -> str:
        """Get the name of the DeepSeek model being used"""
        return self.model 