export interface IToolCall {
  call_tool(): Promise<ToolCallResult>;
  validate(): Promise<void>;
}

// Interface for tool call input (used by chat_js)
export interface IToolCallInput {
  id: string;
  name: string;
  arguments: Record<string, any>;
}

// Tool call result factory
export class ToolCallResult {
  constructor(
    public status: 'success' | 'error',
    public tool_name: string,
    public tool_call_id: string,
    public thread_id: bigint,
    public content?: any,
    public error_type?: string,
    public error_message?: string,
    public status_code?: number | null,
  ) {}

  static error(
    tool_name: string, 
    tool_call_id: string,
    thread_id: bigint,
    error_type: string, 
    error_message: string, 
    status_code?: number
  ): ToolCallResult {
    return new ToolCallResult(
      'error', 
      tool_name, 
      tool_call_id, 
      thread_id, 
      undefined, 
      error_type, 
      error_message, 
      status_code
    );
  }

  static success(tool_name: string, content: any, tool_call_id: string, thread_id: bigint): ToolCallResult {
    return new ToolCallResult('success', tool_name, tool_call_id, thread_id, content);
  }
  
  static scheduled(
    tool_name: string, 
    tool_call_id: string,
    thread_id: bigint,
    job_params: {job_id: bigint, handle: string}
  ): ToolCallResult {
    return new ToolCallResult('success', tool_name, tool_call_id, thread_id, job_params);
  }

  to_dict_w_truncated_content(): Record<string, any> {
    const dict_struct = this.to_dict();
    if (this.status === 'success') {
      dict_struct.content = this.content ? this.content.slice(0, 100) + (this.content.length > 100 ? '...' : '') : undefined;
    } 
    return dict_struct;
  }

  to_dict(): Record<string, any> {
    const common = {
      status: this.status,
      tool_name: this.tool_name,
      tool_call_id: this.tool_call_id,
      thread_id: this.thread_id
    };
    if (this.status === 'success') {
      return {
        ...common,
        content: this.content
      };
    } else {
      return {
        ...common,
        content: {
          error_type: this.error_type, 
          error_message: this.error_message,
          status_code: this.status_code
        }
      };
    }
  }

  to_json(): string {
    return JSON.stringify(this.to_dict(), (key, value) => {
      if (typeof value === 'bigint') {
        return value.toString();
      }
      return value;
    });
  }

  /**
   * Serializes the ToolCallResult for logging purposes
   * Handles BigInt serialization and provides a clean, readable format
   * @returns A string representation suitable for loggers
   */
  toLoggableString(): string {
    // Create a log-friendly version that handles BigInt
    const logData = {
      status: this.status,
      tool_name: this.tool_name,
      tool_call_id: this.tool_call_id,
      thread_id: this.thread_id.toString(), // Convert BigInt to string
      ...(this.status === 'success' 
        ? { content: this.content }
        : { 
            error_type: this.error_type, 
            error_message: this.error_message,
            status_code: this.status_code 
          }
      )
    };

    return JSON.stringify(logData, null, 2);
  }

  /**
   * Creates a compact log message for quick logging
   * @returns A short, single-line log message
   */
  toLogMessage(): string {
    const base = `${this.status.toUpperCase()} - ${this.tool_name} (${this.tool_call_id}) - Thread: ${this.thread_id}`;
    
    if (this.status === 'success') {
      return `${base} - Content: ${this.content ? 'Available' : 'None'}`;
    } else {
      return `${base} - Error: ${this.error_type} - ${this.error_message}`;
    }
  }

  static from_dict(dict: Record<string, any>): ToolCallResult {
    if (dict.status === 'success') {
      return ToolCallResult.success(
        dict.tool_name,
        dict.content,
        dict.tool_call_id,
        dict.thread_id
      );
    } else {
      return ToolCallResult.error(
        dict.tool_name,
        dict.tool_call_id,
        dict.thread_id,
        dict.content.error_type,
        dict.content.error_message,
        dict.content.status_code
      );
    }
  }
}

// Tool Description interface
export interface ToolDescription {
  type: string;
  function: {
    name: string;
    description: string;
    parameters: {
      type: string;
      properties: Record<string, any>;
    };
  };
} 