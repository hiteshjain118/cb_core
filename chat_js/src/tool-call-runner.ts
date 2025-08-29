import { 
  ToolCallResult,
} from 'coralbricks-common';
import { ChatCompletionMessageCustomToolCall, ChatCompletionMessageToolCall } from 'openai/resources/chat/completions';
import axios from 'axios';
import { PrismaService, Task } from 'coralbricks-common';

export class ToolCallRunner {
  private threadId: bigint;
  private cbProfileId: bigint;
  private internalApiUrl: string;
  private enabledTools: string[];
  private enabledToolDescriptions: Array<{
    type: "function";
    function: {
      name: string;
      description: string;
      parameters: {
        type: string;
        properties: Record<string, any>;
        required: string[];
      };
    };
  }>;
  private tasks: Task[] = [];
  constructor(thread_id: bigint, cb_profile_id: bigint) {
    this.threadId = thread_id;
    this.cbProfileId = cb_profile_id;
    this.internalApiUrl = process.env.INTERNAL_API_URL || 'http://localhost:3001';
    this.enabledTools = [];
    this.enabledToolDescriptions = [];
  }

  async run_tools(toolCalls: ChatCompletionMessageToolCall[] | ChatCompletionMessageCustomToolCall[]): Promise<Record<string, ToolCallResult>> {
    const tool_calls: Record<string, ToolCallResult> = {};
    
    // Create an array of promises for parallel execution
    const toolCallPromises = toolCalls.map(async (tool_call) => {
      // Handle both standard and custom tool calls
      if (tool_call.type === 'function' && 'function' in tool_call) {
        const result = await this.run_tool(tool_call.id, tool_call.function.name, tool_call.function.arguments, null);
        return { id: tool_call.id, result };
      }
      // Return error for invalid tool calls instead of null
      const errorResult = ToolCallResult.error(
        'unknown_tool',
        tool_call.id,
        this.threadId,
        "InvalidToolType",
        `Tool call type ${tool_call.type} is not supported`
      );
      return { id: tool_call.id, result: errorResult };
    });

    // Wait for all tool calls to complete
    const results = await Promise.all(toolCallPromises);
    
    // Populate the results object
    results.forEach(item => {
      tool_calls[item.id] = item.result;
    });
    
    return tool_calls;
  }

  // use direct types of toolCall.id, toolCall.function.name, toolCall.function.arguments
  async run_tool(
    tool_call_id: string, 
    tool_name: string, 
    tool_arguments: string,
    requestModelEventId: bigint | null
  ): Promise<ToolCallResult> {
    let result: ToolCallResult;
   
    try {
      const tool_arguments_json = JSON.parse(tool_arguments);
      console.log(`Running tool call id:${tool_call_id} name:${tool_name} with arguments ${JSON.stringify(tool_arguments)}`);
      
      
      if (tool_name === 'python_function_runner') {
        result = await this.run_python_code_runner(tool_arguments_json);
      } else if (['qb_data_schema_retriever', 'qb_data_size_retriever'].includes(tool_name)) {
        result = await this.callInternalAPI(tool_name, tool_call_id, tool_arguments_json, false);
      } else if(tool_name === 'qb_user_data_retriever') {
        result = await this.validateThenRetrieve(tool_name, tool_call_id, tool_arguments_json, requestModelEventId);
      } else {
        result = ToolCallResult.error(
          tool_name,
          tool_call_id,
          this.threadId,
          "InvalidToolName",
          `Tool ${tool_name} not found`
        );
      }
    } catch (error) {
      result = ToolCallResult.error(
        tool_name,
        tool_call_id,
        this.threadId,
        "ToolCallError",
        error instanceof Error ? error.message : 'Unknown error occurred'
      );
    }
    if (result.status === "error") {
      console.error(`Tool ${tool_call_id} failed:`, result.toLogMessage());
      console.debug(`Detailed error info:`, result.toLoggableString());
    } else {
      console.log(`Tool ${tool_call_id} succeeded:`, result.toLogMessage());
      console.debug(`Detailed success info:`, result.toLoggableString());
    }
    
    return result;
  }
  
  public async validateThenRetrieve(toolName: string, toolCallId: string, toolArguments: Record<string, any>, requestModelEventId: bigint | null): Promise<ToolCallResult> {
    const result = await this.callInternalAPI(toolName, toolCallId, toolArguments, true);
    if (result.status === "success") {
      // create a task handle and create new ToolCallResult object to be returned 
      // Schedule the retrieval task to run in the background
      const prisma_client = PrismaService.getInstance()
      const handleForModel = toolName + "_" + toolCallId;
      const task = await prisma_client.task.create({
        data: {
          threadId: this.threadId,
          toolCallId: toolCallId,
          toolCallName: toolName,
          toolCallArgs: toolArguments,
          handleForModel: handleForModel,
          requestModelEventId: requestModelEventId || undefined,
          deps: this.tasks.length > 0 ? { connect: this.tasks.map(task => ({ cbId: task.cbId })) } : undefined
        }
      })
      console.log(`Created task ${task.cbId} for tool call ${toolCallId}`);
      this.tasks.push(task);
      return await this.callInternalAPI(toolName, toolCallId, toolArguments, false);
    }
    return result;
  }

  /**
   * Call the internal backend API for QB tools
   */
  private async callInternalAPI(
    toolName: string, 
    toolCallId: string, 
    toolArguments: Record<string, any>,
    validate: boolean = false
  ): Promise<ToolCallResult> {
    try {
      const requestBody = {
        cbid: this.cbProfileId.toString(),
        thread_id: this.threadId.toString(),
        tool_call_id: toolCallId,
        validate: validate,
        ...toolArguments
      };

      console.log(
        `Making tool call ${toolName} to ${this.internalApiUrl}`,
        `with body ${JSON.stringify(requestBody)}`
      );
      
      const response = await axios.post(`${this.internalApiUrl}/${toolName}`, requestBody, {
        headers: {
          'Content-Type': 'application/json',
          'X-Internal-Service': 'chat_js'
        },
        timeout: 30000 // 30 second timeout
      });

      return ToolCallResult.from_dict(response.data);

    } catch (error) {
      return ToolCallResult.error(
        toolName, 
        toolCallId, 
        this.threadId, 
        "ToolCallError", 
        error instanceof Error ? error.message : 'Unknown error occurred'
      );
    }
  }

  private async run_python_code_runner(args: Record<string, any>): Promise<ToolCallResult> {
    const code = args.code;
    if (code === undefined) {
      return ToolCallResult.error(
        args.name,
        args.id,
        this.threadId,
        "InvalidParameters", 
        "Code is required"
      );
    }
    
    // For now, return a mock success result
    // In a real implementation, you would execute Python code here
    return ToolCallResult.success(
      args.name,
      {
        message: 'Python code execution not implemented in TypeScript version',
        code: code
      },
      args.id,
      this.threadId
    );
  }


  async get_enabled_tools(): Promise<string[]> {
    if (this.enabledTools.length > 0) {
      return this.enabledTools;
    }
    
    const enabledToolDescriptions = await this.get_enabled_tool_descriptions();
    this.enabledTools = enabledToolDescriptions.map((tool) => tool.function.name);
    return this.enabledTools;
  }
  
  async get_enabled_tool_descriptions(): Promise<Array<{
    type: "function";
    function: {
      name: string;
      description: string;
      parameters: {
        type: string;
        properties: Record<string, any>;
        required: string[];
      };
    };
  }>> {
    if (this.enabledToolDescriptions.length > 0) {
      return this.enabledToolDescriptions;
    }
    
    const response = await axios.get(`${this.internalApiUrl}/tools`, {
      headers: {
        'X-Internal-Service': 'chat_js'
      },
      timeout: 10000
    });

    if (response.data.success && response.data.tools) {
      // Backend now returns proper OpenAI tool format
      const backendTools = response.data.tools;
      
      // Add python_function_runner manually since backend doesn't implement it yet
      const pythonTool = {
        type: "function" as const,
        function: {
          name: "python_function_runner",
          description: "Executes Python code for data analysis",
          parameters: {
            type: "object",
            properties: {
              code: {
                type: "string",
                description: "Python code to execute"
              }
            },
            required: ["code"]
          }
        }
      };

      // Cache the tool descriptions
      this.enabledToolDescriptions = [...backendTools, pythonTool];
      return this.enabledToolDescriptions;
    }

    throw new Error('Failed to fetch tools from internal API, chat_js not available');
  }
} 