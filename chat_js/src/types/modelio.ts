// QuickBooks specific types and interfaces

import { ChatCompletionMessage, ChatCompletionMessageCustomToolCall, ChatCompletionMessageToolCall } from "openai/resources/chat/completions";
import { ToolCallRunner } from "../tool-call-runner";
import { ToolCallResult } from 'coralbricks-common';


export interface IModelPrompt {
  get_system_prompt(): string;
  get_messages(): Array<{
    role: 'system' | 'user' | 'assistant' | 'tool';
    content: string;
    tool_call_id?: string;
    name?: string;
  }>;
  add_user_turn(userTurn: TMessage): void;
  add_tool_outputs(toolCalls: Record<string, ToolCallResult>): void;
  add_tool_output(toolCallId: string, toolOutput: ToolCallResult): void;
  add_chat_completion_message(message: any): void;
  pretty_print_conversation(): void;
}

export interface IModelProvider {
  get_response(modelIO: ModelIO): ModelOutputParser | Promise<ModelOutputParser>;
}

export class ModelIO {
  constructor(
    public prompt: IModelPrompt,
    public tool_call_runner: ToolCallRunner,
    public intent: string,
  ) {}

  get_output_parser(): ModelOutputParser {
    return new ModelOutputParser(this.tool_call_runner);
  }
}

export interface TMessage {
  role: string;
  content: string;
}

export class ModelOutputParser {
  private message: ChatCompletionMessage | undefined;
  private responseContent: string | undefined;
  private toolCalls: ChatCompletionMessageToolCall[] | ChatCompletionMessageCustomToolCall[] = [];
  private error: string | undefined;
  private toolCallResults: Record<string, ToolCallResult> = {};
  private toolCallRunner: ToolCallRunner;
  constructor(
    toolCallRunner: ToolCallRunner
  ) {
    this.toolCallRunner = toolCallRunner;
  }

  remove_json_header_if_present(content: string): string {
    if (content.startsWith("```json")) {
      content = content.slice(7);
    }
    if (content.endsWith("```")) {
      content = content.slice(0, -3);
    }
    return content;
  }

  set_message(message: ChatCompletionMessage): ModelOutputParser {
    this.message = message;
    if (message.content) {
      this.responseContent = this.remove_json_header_if_present(message.content);
    }
    if (message.tool_calls && message.tool_calls.length > 0) {
      this.toolCalls = message.tool_calls as ChatCompletionMessageToolCall[] | ChatCompletionMessageCustomToolCall[];
    } 
    return this;
  }

  set_error(error: unknown): ModelOutputParser {
    this.error = error instanceof Error ? error.message : String(error);
    return this;
  }

  async get_output(): Promise<{
    tool_call_results?: any;
    response_content?: string;
    message?: ChatCompletionMessage;
  }> {
    if (this.toolCalls.length > 0) {
      this.toolCallResults = await this.toolCallRunner.run_tools(this.toolCalls);
      return {
        tool_call_results: this.toolCallResults,
        response_content: this.responseContent,
        message: this.message,
      };
    } else if (this.toolCalls.length === 0) {
      return {
        response_content: this.responseContent,
        message: this.message,
      };
    } else {
      throw new Error("Tool call results not ready");
    }
  }

  async get_output_with_should_retry(): Promise<{
    tool_call_results?: any;
    response_content?: string;
    should_retry?: boolean;
    message?: ChatCompletionMessage;
  }> {
    if (this.error) {
      return {
        should_retry: true,
        response_content: this.error,
        message: this.message,
      };
    }
    
    if (this.toolCalls.length > 0) {
      this.toolCallResults = await this.toolCallRunner.run_tools(this.toolCalls);
      let should_retry = false;
      for (const result of Object.values(this.toolCallResults)) {
        if (result.status === 'error') {
          should_retry = true;
        }
      }
      return {
        tool_call_results: this.toolCallResults,
        response_content: this.responseContent,
        message: this.message,
        should_retry: true,
      };
    } else {
      return {
        response_content: this.responseContent,
        message: this.message,
        should_retry: this.responseContent == undefined || this.responseContent.length === 0,
      };
    } 
  }
}