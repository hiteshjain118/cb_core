import { ToolCallRunner } from '../../tool-call-runner';
import { ToolCallResult, IToolCallInput } from 'coralbricks-common';
import { ChatCompletionMessageToolCall } from 'openai/resources/chat/completions';
import axios from 'axios';

// Mock dependencies
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('ToolCallRunner', () => {
  let toolCallRunner: ToolCallRunner;
  const mockThreadId = BigInt(123);
  const mockUserId = BigInt(456);
  const mockInternalApiUrl = 'http://localhost:3001';

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();

    // Mock environment variable
    process.env.INTERNAL_API_URL = mockInternalApiUrl;

    // Mock console methods to avoid noise in tests
    jest.spyOn(console, 'log').mockImplementation();
    jest.spyOn(console, 'debug').mockImplementation();
    jest.spyOn(console, 'error').mockImplementation();

    // Create ToolCallRunner instance
    toolCallRunner = new ToolCallRunner(mockThreadId, mockUserId);
  });

  afterEach(() => {
    jest.restoreAllMocks();
    delete process.env.INTERNAL_API_URL;
  });

  describe('constructor', () => {
    it('should initialize with correct properties', () => {
      const runner = new ToolCallRunner(mockThreadId, mockUserId);
      
      expect(runner).toBeDefined();
      // Note: Properties are private, so we can't directly test them
      // We'll test their behavior through public methods
    });

    it('should use default internal API URL when not set', () => {
      delete process.env.INTERNAL_API_URL;
      const runner = new ToolCallRunner(mockThreadId, mockUserId);
      
      expect(runner).toBeDefined();
    });
  });

  describe('run_tools', () => {
    const createMockToolCall = (
      id: string,
      name: string,
      args: Record<string, any> = {}
    ): ChatCompletionMessageToolCall => ({
      id,
      type: 'function',
      function: {
        name,
        arguments: JSON.stringify(args)
      }
    });

    it('should run multiple tool calls in parallel', async () => {
      const toolCalls = [
        createMockToolCall('call_1', 'python_function_runner', { code: 'print("test1")' }),
        createMockToolCall('call_2', 'python_function_runner', { code: 'print("test2")' })
      ];

      const result = await toolCallRunner.run_tools(toolCalls);

      expect(Object.keys(result)).toHaveLength(2);
      expect(result['call_1']).toBeInstanceOf(ToolCallResult);
      expect(result['call_2']).toBeInstanceOf(ToolCallResult);
      expect(result['call_1']!.status).toBe('success');
      expect(result['call_2']!.status).toBe('success');
    });

    it('should handle empty tool calls array', async () => {
      const result = await toolCallRunner.run_tools([]);

      expect(result).toEqual({});
    });

    it('should handle tool calls with invalid type', async () => {
      const invalidToolCall = {
        id: 'invalid_call',
        type: 'invalid' as any,
        function: {
          name: 'test_tool',
          arguments: '{}'
        }
      };

      const result = await toolCallRunner.run_tools([invalidToolCall]);

      expect(result).toEqual({});
    });

    it('should handle tool calls with malformed JSON arguments', async () => {
      const toolCallWithBadArgs = {
        id: 'bad_args_call',
        type: 'function' as const,
        function: {
          name: 'python_function_runner',
          arguments: 'invalid json'
        }
      };

      await expect(toolCallRunner.run_tools([toolCallWithBadArgs])).rejects.toThrow();
    });

    it('should handle QB tools by calling internal API', async () => {
      const mockResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'qb_call',
          thread_id: mockThreadId,
          content: { data: 'test' }
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const toolCalls = [
        createMockToolCall('qb_call', 'qb_user_data_retriever', { param: 'value' })
      ];

      const result = await toolCallRunner.run_tools(toolCalls);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${mockInternalApiUrl}/qb_user_data_retriever`,
        {
          cbid: mockUserId.toString(),
          thread_id: mockThreadId.toString(),
          tool_call_id: 'qb_call',
          param: 'value'
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'X-Internal-Service': 'chat_js'
          },
          timeout: 30000
        }
      );
      expect(result['qb_call']).toBeInstanceOf(ToolCallResult);
    });
  });

  describe('run_tool', () => {
    it('should run python_function_runner tool', async () => {
      const toolCall: IToolCallInput = {
        id: 'python_call',
        name: 'python_function_runner',
        arguments: { code: 'print("Hello World")' }
      };

      const result = await toolCallRunner.run_tool(toolCall);

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('success');
      expect(result.tool_name).toBe(toolCall.arguments.name);
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Running tool call id:python_call name:python_function_runner')
      );
    });

    it('should handle python_function_runner without code parameter', async () => {
      const toolCall: IToolCallInput = {
        id: 'python_call',
        name: 'python_function_runner',
        arguments: {}
      };

      const result = await toolCallRunner.run_tool(toolCall);

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('error');
    });

    it('should run QB tools via internal API', async () => {
      const mockResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_data_schema_retriever',
          tool_call_id: 'schema_call',
          thread_id: mockThreadId,
          content: { schema: 'test_schema' }
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const toolCall: IToolCallInput = {
        id: 'schema_call',
        name: 'qb_data_schema_retriever',
        arguments: { table: 'customers' }
      };

      const result = await toolCallRunner.run_tool(toolCall);

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${mockInternalApiUrl}/qb_data_schema_retriever`,
        expect.objectContaining({
          cbid: mockUserId.toString(),
          thread_id: mockThreadId.toString(),
          tool_call_id: 'schema_call',
          table: 'customers'
        }),
        expect.any(Object)
      );
    });

    it('should handle unknown tool names', async () => {
      const toolCall: IToolCallInput = {
        id: 'unknown_call',
        name: 'unknown_tool',
        arguments: {}
      };

      await expect(toolCallRunner.run_tool(toolCall)).rejects.toThrow('Tool unknown_tool not found');
    });

    it('should log success for successful tool calls', async () => {
      const toolCall: IToolCallInput = {
        id: 'success_call',
        name: 'python_function_runner',
        arguments: { code: 'print("test")' }
      };

      await toolCallRunner.run_tool(toolCall);

      expect(console.log).toHaveBeenCalledWith(
        'Tool success_call succeeded:',
        expect.any(String)
      );
    });

    it('should log errors for failed tool calls', async () => {
      const toolCall: IToolCallInput = {
        id: 'error_call',
        name: 'python_function_runner',
        arguments: {} // Missing code parameter
      };

      await toolCallRunner.run_tool(toolCall);

      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Tool error_call failed:'),
        expect.any(String)
      );
    });

    
  });

  describe('callInternalAPI', () => {
    it('should handle API errors gracefully', async () => {
      const axiosError = new Error('Network error');
      mockedAxios.post.mockRejectedValue(axiosError);

      const toolCall: IToolCallInput = {
        id: 'api_error_call',
        name: 'qb_user_data_retriever',
        arguments: { param: 'value' }
      };

      const result = await toolCallRunner.run_tool(toolCall);

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('error');
      expect(result.tool_name).toBe('qb_user_data_retriever');
    });

    it('should handle non-Error exceptions', async () => {
      mockedAxios.post.mockRejectedValue('String error');

      const toolCall: IToolCallInput = {
        id: 'string_error_call',
        name: 'qb_data_size_retriever',
        arguments: {}
      };

      const result = await toolCallRunner.run_tool(toolCall);

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('error');
    });
  });

  describe('get_enabled_tools', () => {
    it('should return cached tools if available', async () => {
      // First call to populate cache
      const mockResponse = {
        data: {
          success: true,
          tools: [
            { function: { name: 'tool1' } },
            { function: { name: 'tool2' } }
          ]
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const firstResult = await toolCallRunner.get_enabled_tools();
      
      // Clear the mock to ensure cache is used
      mockedAxios.get.mockClear();
      
      const secondResult = await toolCallRunner.get_enabled_tools();

      expect(mockedAxios.get).not.toHaveBeenCalled();
      expect(firstResult).toEqual(secondResult);
      expect(firstResult).toContain('python_function_runner');
      expect(firstResult).toContain('tool1');
      expect(firstResult).toContain('tool2');
    });

    it('should fetch tools from API when cache is empty', async () => {
      const mockResponse = {
        data: {
          success: true,
          tools: [
            { function: { name: 'qb_user_data_retriever' } },
            { function: { name: 'qb_data_schema_retriever' } }
          ]
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await toolCallRunner.get_enabled_tools();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `${mockInternalApiUrl}/tools`,
        {
          headers: {
            'X-Internal-Service': 'chat_js'
          },
          timeout: 10000
        }
      );
      expect(result).toContain('python_function_runner');
      expect(result).toContain('qb_user_data_retriever');
      expect(result).toContain('qb_data_schema_retriever');
    });

    it('should handle API failure and throw error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('API Error'));

      await expect(toolCallRunner.get_enabled_tools()).rejects.toThrow('API Error');
    });

    it('should handle unsuccessful API response', async () => {
      const mockResponse = {
        data: {
          success: false
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      await expect(toolCallRunner.get_enabled_tools()).rejects.toThrow(
        'Failed to fetch tools from internal API, chat_js not available'
      );
    });

    it('should handle missing tools in API response', async () => {
      const mockResponse = {
        data: {
          success: true,
          tools: null
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      await expect(toolCallRunner.get_enabled_tools()).rejects.toThrow(
        'Failed to fetch tools from internal API, chat_js not available'
      );
    });
  });

  describe('get_enabled_tool_descriptions', () => {
    it('should return cached tool descriptions if available', async () => {
      // First call to populate cache
      const mockResponse = {
        data: {
          success: true,
          tools: [
            {
              type: "function",
              function: {
                name: "test_tool",
                description: "A test tool",
                parameters: {
                  type: "object",
                  properties: {},
                  required: []
                }
              }
            }
          ]
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const firstResult = await toolCallRunner.get_enabled_tool_descriptions();
      
      // Clear the mock to ensure cache is used
      mockedAxios.get.mockClear();
      
      const secondResult = await toolCallRunner.get_enabled_tool_descriptions();

      expect(mockedAxios.get).not.toHaveBeenCalled();
      expect(firstResult).toEqual(secondResult);
      expect(firstResult).toHaveLength(2); // backend tool + python_function_runner
    });

    it('should fetch tool descriptions from API', async () => {
      const mockResponse = {
        data: {
          success: true,
          tools: [
            {
              type: "function",
              function: {
                name: "qb_user_data_retriever",
                description: "Retrieves user data from QuickBooks",
                parameters: {
                  type: "object",
                  properties: {
                    query: { type: "string" }
                  },
                  required: ["query"]
                }
              }
            }
          ]
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await toolCallRunner.get_enabled_tool_descriptions();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `${mockInternalApiUrl}/tools`,
        {
          headers: {
            'X-Internal-Service': 'chat_js'
          },
          timeout: 10000
        }
      );
      expect(result).toHaveLength(2);
      expect(result[0]!.function.name).toBe('qb_user_data_retriever');
      expect(result[1]!.function.name).toBe('python_function_runner');
    });

    it('should handle API failure and throw error', async () => {
      mockedAxios.get.mockRejectedValue(new Error('API Error'));

      await expect(toolCallRunner.get_enabled_tool_descriptions()).rejects.toThrow('API Error');
    });

    it('should handle unsuccessful API response for descriptions', async () => {
      const mockResponse = {
        data: {
          success: false
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      await expect(toolCallRunner.get_enabled_tool_descriptions()).rejects.toThrow(
        'Failed to fetch tools from internal API, chat_js not available'
      );
    });

    it('should validate tool description structure', async () => {
      const mockResponse = {
        data: {
          success: true,
          tools: [
            {
              type: "function",
              function: {
                name: "test_tool",
                description: "Test description",
                parameters: {
                  type: "object",
                  properties: {
                    param1: { type: "string", description: "Parameter 1" },
                    param2: { type: "number", description: "Parameter 2" }
                  },
                  required: ["param1"]
                }
              }
            }
          ]
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await toolCallRunner.get_enabled_tool_descriptions();

      expect(result[0]).toMatchObject({
        type: "function",
        function: {
          name: "test_tool",
          description: "Test description",
          parameters: {
            type: "object",
            properties: expect.any(Object),
            required: ["param1"]
          }
        }
      });
    });
  });

  describe('Integration tests', () => {
    it('should handle complete workflow with QB tools', async () => {
      // Mock tools API response
      const toolsResponse = {
        data: {
          success: true,
          tools: [
            {
              type: "function",
              function: {
                name: "qb_user_data_retriever",
                description: "Retrieves QB data",
                parameters: {
                  type: "object",
                  properties: { query: { type: "string" } },
                  required: ["query"]
                }
              }
            }
          ]
        }
      };

      // Mock tool execution response
      const executionResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'integration_call',
          thread_id: mockThreadId,
          content: { data: 'integration_test' }
        }
      };

      mockedAxios.get.mockResolvedValue(toolsResponse);
      mockedAxios.post.mockResolvedValue(executionResponse);

      // First get tools
      const tools = await toolCallRunner.get_enabled_tools();
      expect(tools).toContain('qb_user_data_retriever');

      // Then execute a tool
      const toolCall: IToolCallInput = {
        id: 'integration_call',
        name: 'qb_user_data_retriever',
        arguments: { query: 'test query' }
      };

      const result = await toolCallRunner.run_tool(toolCall);
      expect(result.status).toBe('success');
    });

    it('should handle mixed tool types in run_tools', async () => {
      // Mock QB tool API response
      const qbResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_data_size_retriever',
          tool_call_id: 'qb_call',
          thread_id: mockThreadId,
          content: { size: 100 }
        }
      };

      mockedAxios.post.mockResolvedValue(qbResponse);

      const toolCalls = [
        {
          id: 'python_call',
          type: 'function' as const,
          function: {
            name: 'python_function_runner',
            arguments: JSON.stringify({ code: 'print("test")' })
          }
        },
        {
          id: 'qb_call',
          type: 'function' as const,
          function: {
            name: 'qb_data_size_retriever',
            arguments: JSON.stringify({ table: 'items' })
          }
        }
      ];

      const results = await toolCallRunner.run_tools(toolCalls);

      expect(Object.keys(results)).toHaveLength(2);
      expect(results['python_call']!.status).toBe('success');
      expect(results['qb_call']!.status).toBe('success');
    });
  });
}); 