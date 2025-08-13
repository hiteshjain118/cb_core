import traceback
import openai
import logging
from typing import List, Dict, Any
from builder_package.model_providers.llm_monitor import LLMMonitor
from builder_package.core.imodel_io import IModelOutputParser, ModelIO  
from builder_package.model_providers.imodel_provider import IModelProvider

# Create module-specific logger
logger = logging.getLogger(__name__)
# Ensure debug logging is turned off for this module
logger.setLevel(logging.INFO)
# Also disable debug logging for the parent logger to be extra sure
logging.getLogger('builder_package.model_providers').setLevel(logging.INFO)
# Additional safeguard - disable debug logging for the entire openai module
logging.getLogger('openai').setLevel(logging.WARNING)


class GPTProvider(IModelProvider):
    """OpenAI GPT model provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the GPT provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use (default: gpt-4o)
        """
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        self.llm_monitor = LLMMonitor(model=model, name="GPTProvider")
        
        logger.info(f"Initialized GPTProvider with model: {model}")
    
    def get_response(
        self, 
        model_io: ModelIO,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        tools: List[Dict[str, Any]] = [],
    ) -> IModelOutputParser:
        messages = model_io.prompt.get_messages()

        # try:
        logger.debug(f"Sending request to GPT: {messages}, tools: {tools}, from prompt_type: {type(model_io.prompt)}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            # max_completion_tokens=max_tokens,
            # temperature=temperature,
            tools=tools,
        )
        logger.debug(f"GPT response content: '{response}'")

        # Get the response content
        choice = response.choices[0]
        message = choice.message

        # Record LLM call if monitor is available
        # self.llm_monitor.record_llm_call(
        #     messages=messages,
        #     intent=model_io.intent,
        #     response_content=message.content,
        #     tool_calls_in_response=message.tool_calls,
        #     tools_in_prompt=tools
        # )
        return model_io.output_parser.set_success(choice.message)
        # except Exception as e:
        #     logger.error(f"Error in GPT response: {e}")
        #     logger.error(f"Stack trace: {traceback.format_exc()}")
        #     return model_io.output_parser.set_error(error_reason="Error in GPT response")


    def get_model_name(self) -> str:
        """Get the name of the GPT model being used"""
        return self.model 