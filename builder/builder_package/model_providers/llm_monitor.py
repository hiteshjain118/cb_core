import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict
import json
from builder_package.core.enums import IntentName

# Import token utility functions
import sys
import os
from builder_package.model_providers.token_util import count_tokens


class LLMMonitor:
    """
    Monitors and tracks LLM usage including token counts and API calls.
    Provides aggregated statistics and breakdown by intent.
    """

    def __init__(self, model: str = "gpt-4o", name: str = "LLMMonitor"):
        """Initialize the LLM monitor with empty statistics"""
        # Model configuration
        self.model = model
        self.name = name
        self.tools_token_usage = {
            'input_tokens': 0,
            'output_tokens': 0
        }
        # Token usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_llm_calls = 0
        
        # Per-intent tracking
        self.intent_token_usage = defaultdict(lambda: {
            'input_tokens': 0,
            'output_tokens': 0,
            'llm_calls': 0
        })
        
        # Cost tracking (rough estimates)
        self.estimated_costs = {
            'gpt-4o-mini': {'input': 0.6 * 10e-6, 'output': 2.4 * 10e-6},  # per token
            'gpt-4o': {'input': 5 * 10e-6, 'output': 20 * 10e-6},  # per token
            'deepseek-ai/DeepSeek-R1-Distill-Llama-70B': {'input': 0.1 * 10e-6, 'output': 0.4 * 10e-6},  # per token
            'deepseek-ai/DeepSeek-V3': {'input': 0.38 * 10e-6, 'output': 0.89 * 10e-6}  # per token
        }
        
        logging.info(f"LLM Monitor '{name}' initialized with model: {model}")

    def calculate_input_tokens(
        self, messages: List[Dict[str, str]], intent: IntentName
    ) -> int:
        """
        Calculate token count for input messages only.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            intent: The intent being processed
            
        Returns:
            Number of input tokens
            
        Raises:
            ValueError: If the last message is from the assistant
        """
        if not messages:
            return 0
            
        # Validate that the last message is not from the assistant
        last_message = messages[-1]
        if last_message.get('role') == 'assistant':
            raise ValueError(
                f"Last message in input messages should not be from assistant. "
                f"Intent: {intent.value}, "
                f"Last message role: {last_message.get('role')}"
            )
        
        input_tokens = 0
        
        try:
            # Calculate input tokens (all messages since none should be from assistant)
            for message in messages:
                content = message.get('content', '')
                input_tokens += count_tokens(content, self.model)
            
            return input_tokens
            
        except Exception as e:
            logging.error(f"Error calculating input tokens: {e}")
            return 0

    def calculate_input_and_output_tokens(
        self, messages: List[Dict[str, str]], intent: IntentName
    ) -> Dict[str, int]:
        """
        Calculate token count for both input and output messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            intent: The intent being processed
            
        Returns:
            Dictionary with 'input_tokens' and 'output_tokens' counts
            
        Raises:
            ValueError: If the last message is not from the assistant
        """
        if not messages:
            return {'input_tokens': 0, 'output_tokens': 0}
        
        # Validate that the last message is from the assistant
        last_message = messages[-1]
        if last_message.get('role') != 'assistant':
            raise ValueError(
                f"Last message in input and output messages should be from assistant. "
                f"Intent: {intent.value}, "
                f"Last message role: {last_message.get('role')}"
            )
        
        try:
            # Get input messages (all except the last assistant message)
            input_messages = messages[:-1]
            
            # Calculate input tokens using the existing method
            input_tokens = self.calculate_input_tokens(input_messages, intent)
            
            # Calculate output tokens (last message from assistant)
            content = last_message.get('content', '')
            output_tokens = count_tokens(content, self.model)
            
            logging.debug(
                f"Token calculation for {intent.value}: "
                f"input={input_tokens}, output={output_tokens}"
            )
            
            return {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
            
        except Exception as e:
            logging.error(f"Error calculating input and output tokens: {e}")
            return {'input_tokens': 0, 'output_tokens': 0}

    def record_llm_call(
        self, 
        messages: List[Dict[str, str]], 
        intent: IntentName, 
        response_content: str, 
        tool_calls_in_response: List[Dict[str, Any]] = [], 
        tools_in_prompt: str = ""
    ):
        """
        Record an LLM call with token usage and metadata.
        
        Args:
            messages: Input messages sent to LLM
            intent: The intent being processed
            response_content: The response content from LLM
            tool_calls_in_response: Tool calls in the response
            tools_in_prompt: Tools available in the prompt
        """
        # Calculate input tokens
        input_tokens = self.calculate_input_tokens(messages, intent)
        output_tokens = count_tokens(response_content, self.model)
        
        # calculate output tokens for tool calls
        tools_output_tokens = 0
        if tool_calls_in_response is not None:
            for tool_call in tool_calls_in_response:
                tools_output_tokens += count_tokens(tool_call.function.name, self.model)
                tools_output_tokens += count_tokens(tool_call.function.arguments, self.model)
        tool_input_tokens = count_tokens(
            tools_in_prompt, self.model
        )        
        self.tools_token_usage['input_tokens'] += tool_input_tokens 
        self.tools_token_usage['output_tokens'] += tools_output_tokens

        # Update totals
        self.total_input_tokens += (input_tokens + tool_input_tokens)
        self.total_output_tokens += (output_tokens + tools_output_tokens)
        self.total_llm_calls += 1
            
        # Update per-intent statistics
        intent_key = intent.name if intent is not None else "Unknown"
        self.intent_token_usage[intent_key]['input_tokens'] += (input_tokens + tool_input_tokens)
        self.intent_token_usage[intent_key]['output_tokens'] += (
            output_tokens + tools_output_tokens
        )
        self.intent_token_usage[intent_key]['llm_calls'] += 1
        

    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics including totals and breakdown by intent.
        
        Returns:
            Dictionary with usage statistics
        """
        # Calculate total costs
        total_app_cost = self._calculate_app_cost()
        
        # Prepare per-intent breakdown
        intent_breakdown = {}
        for intent, stats in self.intent_token_usage.items():
            intent_cost = self._calculate_cost(
                stats['input_tokens'], stats['output_tokens']
            )
            intent_breakdown[intent] = {
                'input_tokens': stats['input_tokens'],
                'output_tokens': stats['output_tokens'],
                'total_tokens': stats['input_tokens'] + stats['output_tokens'],
                'llm_calls': stats['llm_calls'],
                'estimated_cost': intent_cost
            }
        
        return {
            'summary': {
                'total_input_tokens': self.total_input_tokens,
                'total_output_tokens': self.total_output_tokens,
                'total_tokens': self.total_input_tokens + self.total_output_tokens,
                'total_llm_calls': self.total_llm_calls,
                'estimated_app_cost': total_app_cost,
                'estimated_total_cost': self._calculate_tools_cost() + total_app_cost
            },
            'breakdown_by_intent': intent_breakdown,
            'tools_token_usage': {
                'input_tokens': self.tools_token_usage['input_tokens'],
                'output_tokens': self.tools_token_usage['output_tokens'],
                'estimated_cost': self._calculate_tools_cost()
            }
        }

    def reset_statistics(self):
        """Reset all statistics to zero"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_llm_calls = 0
        self.intent_token_usage.clear()
        self.tools_token_usage.clear()
        logging.info(f"LLM usage statistics reset for {self.name}")

    def print_usage_summary(self):
        """Print usage summary for this monitor"""
        stats = self.get_usage_statistics()
        summary = stats['summary']
        tools_token_usage = stats['tools_token_usage']
        
        if (tools_token_usage['input_tokens'] > 0 or 
            tools_token_usage['output_tokens'] > 0):
            overhead_cost_fraction = tools_token_usage['estimated_cost'] / (summary['estimated_total_cost'])
            tools_token_usage_str = (
                f"Tools input tokens: {tools_token_usage['input_tokens']}, "
                f"Tools output tokens: {tools_token_usage['output_tokens']}, "
                f"Overhead cost: ${tools_token_usage['estimated_cost']:.6f} ({overhead_cost_fraction:.2%})"
            )
        else:
            tools_token_usage_str = ""

        logging.debug(
            f"{self.name} Usage Summary: "
            f"Total calls: {summary['total_llm_calls']}, "
            f"Input tokens: {summary['total_input_tokens']}, "
            f"Output tokens: {summary['total_output_tokens']}, "
            f"Estimated cost: ${summary['estimated_total_cost']:.6f} "
            f"{tools_token_usage_str}"
        )
        
        # Log breakdown by intent if there are any
        if stats['breakdown_by_intent']:
            intent_details = []
            for intent_name, intent_stats in stats['breakdown_by_intent'].items():
                intent_details.append(
                    f"{intent_name}: {intent_stats['llm_calls']} calls, "
                    f"{intent_stats['total_tokens']} tokens, "
                    f"${intent_stats['estimated_cost']:.6f}"
                )
            logging.debug(
                f"{self.name} Breakdown: {', '.join(intent_details)}"
            )

    def export_statistics(self, filepath: str):
        """
        Export usage statistics to a JSON file.
        
        Args:
            filepath: Path to save the JSON file
        """
        try:
            stats = self.get_usage_statistics()
            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2)
            logging.info(f"Usage statistics exported to {filepath}")
        except Exception as e:
            logging.error(f"Error exporting statistics: {e}")

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate estimated cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        if self.model not in self.estimated_costs:
            model = "gpt-4o"  # Default to gpt-4o pricing
        else:
            model = self.model
            
        pricing = self.estimated_costs[model]
        input_cost = input_tokens * pricing['input']
        output_cost = output_tokens * pricing['output']
        
        return round(input_cost + output_cost, 6)

    def _calculate_app_cost(self) -> float:
        """Calculate total estimated cost across all calls"""
        total_cost = 0.0
        
        for intent, stats in self.intent_token_usage.items():
            cost = self._calculate_cost(
                stats['input_tokens'], stats['output_tokens']
            )
            total_cost += cost
            
        return round(total_cost, 6)

    def _calculate_tools_cost(self) -> float:
        """Calculate total estimated cost for tools"""
        cost  = self._calculate_cost(
            self.tools_token_usage['input_tokens'],
            self.tools_token_usage['output_tokens']
        )
        return round(cost, 6)


    def get_intent_usage(self, intent: IntentName) -> Dict[str, Any]:
        """
        Get usage statistics for a specific intent.
        
        Args:
            intent: The intent to get statistics for
            
        Returns:
            Dictionary with usage statistics for the intent
        """
        intent_key = intent.value
        stats = self.intent_token_usage.get(intent_key, {
            'input_tokens': 0,
            'output_tokens': 0,
            'llm_calls': 0
        })
        
        return {
            'intent': intent_key,
            'input_tokens': stats['input_tokens'],
            'output_tokens': stats['output_tokens'],
            'total_tokens': stats['input_tokens'] + stats['output_tokens'],
            'llm_calls': stats['llm_calls'],
            'estimated_cost': self._calculate_cost(
                stats['input_tokens'], stats['output_tokens']
            )
        } 