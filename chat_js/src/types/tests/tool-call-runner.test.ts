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
  const mockCbProfileId = BigInt(456);
  const mockInternalApiUrl = 'http://localhost:3001';

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
    toolCallRunner = new ToolCallRunner(mockThreadId, mockCbProfileId);
  });

  afterEach(() => {
    jest.restoreAllMocks();
    delete process.env.INTERNAL_API_URL;
  });

  describe('constructor', () => {
    it('should initialize with correct properties', () => {
      const runner = new ToolCallRunner(mockThreadId, mockCbProfileId);
      
      expect(runner).toBeDefined();
      // Note: Properties are private, so we can't directly test them
      // We'll test their behavior through public methods
    });

    it('should use default internal API URL when not set', () => {
      delete process.env.INTERNAL_API_URL;
      const runner = new ToolCallRunner(mockThreadId, mockCbProfileId);
      
      expect(runner).toBeDefined();
    });
  });

  describe('run_tools', () => {
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

      expect(result['invalid_call']).toBeInstanceOf(ToolCallResult);
      expect(result['invalid_call']!.status).toBe('error');
      expect(result['invalid_call']!.error_type).toBe('InvalidToolType');
      expect(result['invalid_call']!.tool_name).toBe('unknown_tool');
      expect(result['invalid_call']!.error_message).toBe('Tool call type invalid is not supported');
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

      const result = await toolCallRunner.run_tools([toolCallWithBadArgs]);
      
      expect(result['bad_args_call']).toBeInstanceOf(ToolCallResult);
      expect(result['bad_args_call']!.status).toBe('error');
      expect(result['bad_args_call']!.error_type).toBe('ToolCallError');
    });

    it('should handle qb_data_schema_retriever via direct API call', async () => {
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

      const toolCalls = [
        createMockToolCall('schema_call', 'qb_data_schema_retriever', { table: 'customers' })
      ];

      const result = await toolCallRunner.run_tools(toolCalls);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${mockInternalApiUrl}/qb_data_schema_retriever`,
        {
          cbid: mockCbProfileId.toString(),
          thread_id: mockThreadId.toString(),
          tool_call_id: 'schema_call',
          validate: false,
          table: 'customers'
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'X-Internal-Service': 'chat_js'
          },
          timeout: 30000
        }
      );
      expect(result['schema_call']).toBeInstanceOf(ToolCallResult);
    });

    it('should handle qb_user_data_retriever with validate-then-retrieve flow', async () => {
      const validateResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'user_call',
          thread_id: mockThreadId,
          content: { validation: 'passed' }
        }
      };

      const retrieveResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'user_call',
          thread_id: mockThreadId,
          content: { data: 'user_data' }
        }
      };

      mockedAxios.post
        .mockResolvedValueOnce(validateResponse)  // First call (validate=true)
        .mockResolvedValueOnce(retrieveResponse); // Second call (validate=false)

      const toolCalls = [
        createMockToolCall('user_call', 'qb_user_data_retriever', { query: 'SELECT * FROM users' })
      ];

      const result = await toolCallRunner.run_tools(toolCalls);

      expect(mockedAxios.post).toHaveBeenCalledTimes(2);
      
      // First call should be validation
      expect(mockedAxios.post).toHaveBeenNthCalledWith(1,
        `${mockInternalApiUrl}/qb_user_data_retriever`,
        {
          cbid: mockCbProfileId.toString(),
          thread_id: mockThreadId.toString(),
          tool_call_id: 'user_call',
          validate: true,
          query: 'SELECT * FROM users'
        },
        expect.any(Object)
      );

      // Second call should be retrieval
      expect(mockedAxios.post).toHaveBeenNthCalledWith(2,
        `${mockInternalApiUrl}/qb_user_data_retriever`,
        {
          cbid: mockCbProfileId.toString(),
          thread_id: mockThreadId.toString(),
          tool_call_id: 'user_call',
          validate: false,
          query: 'SELECT * FROM users'
        },
        expect.any(Object)
      );

      expect(result['user_call']).toBeInstanceOf(ToolCallResult);
      expect(result['user_call']!.status).toBe('success');
    });
  });

  describe('run_tool', () => {
    it('should run python_function_runner tool', async () => {
      const result = await toolCallRunner.run_tool(
        'python_call',
        'python_function_runner', 
        '{"code": "print(\\"Hello World\\")"}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('success');
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Running tool call id:python_call name:python_function_runner')
      );
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Tool python_call succeeded:'),
        expect.any(String)
      );
    });

    it('should handle python_function_runner without code parameter', async () => {
      const result = await toolCallRunner.run_tool(
        'python_call',
        'python_function_runner',
        '{}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('error');
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Tool python_call failed:'),
        expect.any(String)
      );
    });

    it('should run qb_data_schema_retriever via direct API call', async () => {
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

      const result = await toolCallRunner.run_tool(
        'schema_call',
        'qb_data_schema_retriever',
        '{"table": "customers"}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${mockInternalApiUrl}/qb_data_schema_retriever`,
        expect.objectContaining({
          cbid: mockCbProfileId.toString(),
          thread_id: mockThreadId.toString(),
          tool_call_id: 'schema_call',
          validate: false,
          table: 'customers'
        }),
        expect.any(Object)
      );
    });

    it('should run qb_data_size_retriever via direct API call', async () => {
      const mockResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_data_size_retriever',
          tool_call_id: 'size_call',
          thread_id: mockThreadId,
          content: { count: 42 }
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await toolCallRunner.run_tool(
        'size_call',
        'qb_data_size_retriever',
        '{"query": "SELECT COUNT(*) FROM customers"}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${mockInternalApiUrl}/qb_data_size_retriever`,
        expect.objectContaining({
          cbid: mockCbProfileId.toString(),
          thread_id: mockThreadId.toString(),
          tool_call_id: 'size_call',
          validate: false,
          query: 'SELECT COUNT(*) FROM customers'
        }),
        expect.any(Object)
      );
    });

    it('should run qb_user_data_retriever with validate-then-retrieve', async () => {
      const validateResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'user_call',
          thread_id: mockThreadId,
          content: { validation: 'passed' }
        }
      };

      const retrieveResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'user_call',
          thread_id: mockThreadId,
          content: { data: 'user_data' }
        }
      };

      mockedAxios.post
        .mockResolvedValueOnce(validateResponse)
        .mockResolvedValueOnce(retrieveResponse);

      const result = await toolCallRunner.run_tool(
        'user_call',
        'qb_user_data_retriever',
        '{"query": "SELECT * FROM users"}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('success');
      expect(mockedAxios.post).toHaveBeenCalledTimes(2);
    });

    it('should handle validation failure for qb_user_data_retriever', async () => {
      const validateResponse = {
        data: {
          status: 'error',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'user_call',
          thread_id: mockThreadId,
          error_message: 'Validation failed'
        }
      };

      mockedAxios.post.mockResolvedValueOnce(validateResponse);

      const result = await toolCallRunner.run_tool(
        'user_call',
        'qb_user_data_retriever',
        '{"query": "INVALID SQL"}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('error');
      expect(mockedAxios.post).toHaveBeenCalledTimes(1); // Only validation call, no retrieval
    });

    it('should handle unknown tool names', async () => {
      const result = await toolCallRunner.run_tool(
        'unknown_call',
        'unknown_tool',
        '{}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('error');
      expect(result.error_type).toBe('InvalidToolName');
      expect(result.error_message).toBe('Tool unknown_tool not found');
    });

    it('should log success for successful tool calls', async () => {
      await toolCallRunner.run_tool(
        'python_call',
        'python_function_runner',
        '{"code": "print(\\"test\\")"}'
      );

      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Tool python_call succeeded:'),
        expect.any(String)
      );
    });

    it('should log errors for failed tool calls', async () => {
      await toolCallRunner.run_tool(
        'unknown_call',
        'unknown_tool',
        '{}'
      );

      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Tool unknown_call failed:'),
        expect.any(String)
      );
    });

    it('should handle JSON parsing errors in tool arguments', async () => {
      const result = await toolCallRunner.run_tool(
        'parse_error_call',
        'python_function_runner',
        '{"code": "print(\\"test\\"", invalid_json}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('error');
      expect(result.error_type).toBe('ToolCallError');
      expect(result.error_message).toMatch(/Expected double-quoted property name|Unexpected token/);
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Tool parse_error_call failed:'),
        expect.any(String)
      );
    });

    it('should call toLogMessage and toLoggableString for successful tools', async () => {
      const mockToLogMessage = jest.fn().mockReturnValue('Success log message');
      const mockToLoggableString = jest.fn().mockReturnValue('Success loggable string');
      
      // Mock ToolCallResult methods
      jest.spyOn(ToolCallResult.prototype, 'toLogMessage').mockImplementation(mockToLogMessage);
      jest.spyOn(ToolCallResult.prototype, 'toLoggableString').mockImplementation(mockToLoggableString);

      await toolCallRunner.run_tool(
        'success_call',
        'python_function_runner',
        '{"code": "print(\\"success\\")"}'
      );

      expect(mockToLogMessage).toHaveBeenCalled();
      expect(mockToLoggableString).toHaveBeenCalled();
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Tool success_call succeeded:'),
        'Success log message'
      );
      expect(console.debug).toHaveBeenCalledWith(
        expect.stringContaining('Detailed success info:'),
        'Success loggable string'
      );
    });

    it('should call toLogMessage and toLoggableString for failed tools', async () => {
      const mockToLogMessage = jest.fn().mockReturnValue('Error log message');
      const mockToLoggableString = jest.fn().mockReturnValue('Error loggable string');
      
      // Mock ToolCallResult methods
      jest.spyOn(ToolCallResult.prototype, 'toLogMessage').mockImplementation(mockToLogMessage);
      jest.spyOn(ToolCallResult.prototype, 'toLoggableString').mockImplementation(mockToLoggableString);

      await toolCallRunner.run_tool(
        'error_call',
        'unknown_tool',
        '{}'
      );

      expect(mockToLogMessage).toHaveBeenCalled();
      expect(mockToLoggableString).toHaveBeenCalled();
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Tool error_call failed:'),
        'Error log message'
      );
      expect(console.debug).toHaveBeenCalledWith(
        expect.stringContaining('Detailed error info:'),
        'Error loggable string'
      );
    });
  });

  describe('validateThenRetrieve', () => {
    it('should call validation first, then retrieval on success', async () => {
      const validateResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'test_call',
          thread_id: mockThreadId,
          content: { validation: 'passed' }
        }
      };

      const retrieveResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'test_call',
          thread_id: mockThreadId,
          content: { data: 'retrieved' }
        }
      };

      mockedAxios.post
        .mockResolvedValueOnce(validateResponse)
        .mockResolvedValueOnce(retrieveResponse);

      const result = await toolCallRunner.run_tool(
        'test_call',
        'qb_user_data_retriever',
        '{"query": "SELECT * FROM test"}'
      );

      expect(mockedAxios.post).toHaveBeenCalledTimes(2);
      expect(result.status).toBe('success');
    });

    it('should return validation error without calling retrieval', async () => {
      const validateResponse = {
        data: {
          status: 'error',
          tool_name: 'qb_user_data_retriever',
          tool_call_id: 'test_call',
          thread_id: mockThreadId,
          content: { error_type: 'ValidationError', error_message: 'Query too complex' }
        }
      };

      mockedAxios.post.mockResolvedValueOnce(validateResponse);

      const result = await toolCallRunner.run_tool(
        'test_call',
        'qb_user_data_retriever',
        '{"query": "COMPLEX QUERY"}'
      );

      expect(mockedAxios.post).toHaveBeenCalledTimes(1);
      expect(result.status).toBe('error');
    });
  });

  describe('callInternalAPI', () => {
    it('should handle API errors gracefully', async () => {
      mockedAxios.post.mockRejectedValue(new Error('Network error'));

      const result = await toolCallRunner.run_tool(
        'api_call',
        'qb_data_schema_retriever',
        '{"table": "test"}'
      );

      expect(result).toBeInstanceOf(ToolCallResult);
      expect(result.status).toBe('error');
      expect(result.tool_name).toBe('qb_data_schema_retriever');
      expect(result.error_type).toBe('ToolCallError');
    });

    it('should include validate parameter in request body', async () => {
      const mockResponse = {
        data: {
          status: 'success',
          tool_name: 'qb_data_schema_retriever',
          tool_call_id: 'validate_call',
          thread_id: mockThreadId,
          content: { schema: 'test' }
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      await toolCallRunner.run_tool(
        'validate_call',
        'qb_data_schema_retriever', 
        '{"table": "test_table"}'
      );

      expect(mockedAxios.post).toHaveBeenCalledWith(
        `${mockInternalApiUrl}/qb_data_schema_retriever`,
        expect.objectContaining({
          cbid: mockCbProfileId.toString(),
          thread_id: mockThreadId.toString(),
          tool_call_id: 'validate_call',
          validate: false,
          table: 'test_table'
        }),
        expect.any(Object)
      );
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

    it('should throw error on unsuccessful API response', async () => {
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

    it('should throw error on missing tools in API response', async () => {
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

  describe('python_function_runner', () => {
    it('should execute python code runner with valid code', async () => {
      const result = await toolCallRunner.run_tool(
        'python_test',
        'python_function_runner',
        '{"code": "import pandas as pd\\ndf = pd.DataFrame({\\"a\\": [1,2,3]})"}'
      );

      expect(result.status).toBe('success');
      expect(result.content).toHaveProperty('message');
      expect(result.content).toHaveProperty('code');
    });

    it('should handle missing code parameter', async () => {
      const result = await toolCallRunner.run_tool(
        'python_no_code',
        'python_function_runner',
        '{"name": "python_function_runner", "id": "python_no_code"}'
      );

      expect(result.status).toBe('error');
      expect(result.error_type).toBe('InvalidParameters');
      expect(result.error_message).toBe('Code is required');
    });
  });
}); 