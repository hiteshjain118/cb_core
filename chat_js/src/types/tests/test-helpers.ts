import { ToolCallResult } from 'coralbricks-common';
import { ChatCompletionMessage } from 'openai/resources/chat/completions';

export function createMockToolCallResult(
  status: 'success' | 'error' = 'success',
  toolName: string = 'test_tool',
  toolCallId: string = 'call_123',
  threadId: bigint = BigInt(1),
  content?: any
): ToolCallResult {
  return new ToolCallResult(status, toolName, toolCallId, threadId, content);
}

export function createMockChatMessage(
  content: string | null = 'test content',
  role: 'assistant' | 'user' | 'system' | 'tool' = 'assistant',
  toolCalls?: any[]
): ChatCompletionMessage {
  const message: ChatCompletionMessage = {
    role: role as any,
    content,
    refusal: null
  };
  
  if (toolCalls) {
    message.tool_calls = toolCalls;
  }
  
  return message;
} 