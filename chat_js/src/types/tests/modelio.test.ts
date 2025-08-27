import { ModelIO, ModelOutputParser, IModelPrompt, IModelProvider, TMessage } from '../modelio';
import { ToolCallRunner } from '../../tool-call-runner';
import { ToolCallResult } from 'coralbricks-common';
import { ChatCompletionMessage, ChatCompletionMessageToolCall } from 'openai/resources/chat/completions';

// Mock dependencies
jest.mock('../../tool-call-runner');
jest.mock('coralbricks-common');

describe('ModelIO', () => {
  let mockPrompt: jest.Mocked<IModelPrompt>;
  let mockToolCallRunner: jest.Mocked<ToolCallRunner>;
  let modelIO: ModelIO;

  beforeEach(() => {
    mockPrompt = {
      get_system_prompt: jest.fn(),
      get_messages: jest.fn(),
      add_user_turn: jest.fn(),
      add_tool_outputs: jest.fn(),
      add_tool_output: jest.fn(),
      add_chat_completion_message: jest.fn(),
      pretty_print_conversation: jest.fn()
    };

    mockToolCallRunner = {
      run_tools: jest.fn(),
      run_tool: jest.fn()
    } as any;

    modelIO = new ModelIO(mockPrompt, mockToolCallRunner, 'test_intent');
  });

  describe('constructor', () => {
    it('should initialize with correct properties', () => {
      expect(modelIO.prompt).toBe(mockPrompt);
      expect(modelIO.tool_call_runner).toBe(mockToolCallRunner);
      expect(modelIO.intent).toBe('test_intent');
    });
  });

  describe('get_output_parser', () => {
    it('should return a ModelOutputParser instance', () => {
      const parser = modelIO.get_output_parser();
      expect(parser).toBeInstanceOf(ModelOutputParser);
    });

    it('should pass the tool call runner to the parser', () => {
      const parser = modelIO.get_output_parser();
      expect((parser as any).toolCallRunner).toBe(mockToolCallRunner);
    });
  });
});

describe('ModelOutputParser', () => {
  let mockToolCallRunner: jest.Mocked<ToolCallRunner>;
  let parser: ModelOutputParser;

  beforeEach(() => {
    mockToolCallRunner = {
      run_tools: jest.fn(),
      run_tool: jest.fn()
    } as any;

    parser = new ModelOutputParser(mockToolCallRunner);
  });

  describe('constructor', () => {
    it('should initialize with tool call runner', () => {
      expect((parser as any).toolCallRunner).toBe(mockToolCallRunner);
    });

    it('should initialize with default empty values', () => {
      expect((parser as any).message).toBeUndefined();
      expect((parser as any).responseContent).toBeUndefined();
      expect((parser as any).toolCalls).toEqual([]);
      expect((parser as any).error).toBeUndefined();
      expect((parser as any).toolCallResults).toEqual({});
    });
  });

  describe('remove_json_header_if_present', () => {
    it('should remove json header and footer', () => {
      const content = '```json\n{"test": "value"}\n```';
      const result = parser.remove_json_header_if_present(content);
      expect(result).toBe('\n{"test": "value"}\n');
    });

    it('should remove only json header if no footer', () => {
      const content = '```json\n{"test": "value"}';
      const result = parser.remove_json_header_if_present(content);
      expect(result).toBe('\n{"test": "value"}');
    });

    it('should remove only footer if no header', () => {
      const content = '{"test": "value"}\n```';
      const result = parser.remove_json_header_if_present(content);
      expect(result).toBe('{"test": "value"}\n');
    });

    it('should return content unchanged if no json markers', () => {
      const content = '{"test": "value"}';
      const result = parser.remove_json_header_if_present(content);
      expect(result).toBe('{"test": "value"}');
    });

    it('should handle empty string', () => {
      const result = parser.remove_json_header_if_present('');
      expect(result).toBe('');
    });
  });

  describe('set_message', () => {
    it('should set message and process content', () => {
      const message: ChatCompletionMessage = {
        role: 'assistant',
        content: '```json\n{"response": "test"}\n```'
      };

      const result = parser.set_message(message);
      
      expect(result).toBe(parser);
      expect((parser as any).message).toBe(message);
      expect((parser as any).responseContent).toBe('\n{"response": "test"}\n');
    });

    it('should handle message with tool calls', () => {
      const toolCalls: ChatCompletionMessageToolCall[] = [
        {
          id: 'call_123',
          type: 'function',
          function: {
            name: 'test_function',
            arguments: '{"param": "value"}'
          }
        }
      ];

      const message: ChatCompletionMessage = {
        role: 'assistant',
        content: 'Using tool',
        tool_calls: toolCalls
      };

      parser.set_message(message);
      
      expect((parser as any).toolCalls).toBe(toolCalls);
      expect((parser as any).responseContent).toBe('Using tool');
    });

    it('should handle message without content', () => {
      const message: ChatCompletionMessage = {
        role: 'assistant',
        content: null
      };

      parser.set_message(message);
      
      expect((parser as any).message).toBe(message);
      expect((parser as any).responseContent).toBeUndefined();
    });
  });

  describe('set_error', () => {
    it('should set error from Error object', () => {
      const error = new Error('Test error message');
      const result = parser.set_error(error);
      
      expect(result).toBe(parser);
      expect((parser as any).error).toBe('Test error message');
    });

    it('should set error from string', () => {
      const result = parser.set_error('String error');
      
      expect(result).toBe(parser);
      expect((parser as any).error).toBe('String error');
    });

    it('should set error from other types', () => {
      const result = parser.set_error(404);
      
      expect(result).toBe(parser);
      expect((parser as any).error).toBe('404');
    });
  });

  describe('get_output', () => {
    it('should return tool call results when tool calls exist', async () => {
      const toolCalls: ChatCompletionMessageToolCall[] = [
        {
          id: 'call_123',
          type: 'function',
          function: { name: 'test_function', arguments: '{}' }
        }
      ];

      const mockResults = {
        'call_123': new ToolCallResult()
      };

      mockToolCallRunner.run_tools.mockResolvedValue(mockResults);

      // Set up parser state
      (parser as any).toolCalls = toolCalls;
      (parser as any).responseContent = 'test response';
      (parser as any).message = { role: 'assistant', content: 'test' };

      const result = await parser.get_output();

      expect(mockToolCallRunner.run_tools).toHaveBeenCalledWith(toolCalls);
      expect(result).toEqual({
        tool_call_results: mockResults,
        response_content: 'test response',
        message: { role: 'assistant', content: 'test' }
      });
    });

    it('should return response content when no tool calls', async () => {
      (parser as any).toolCalls = [];
      (parser as any).responseContent = 'test response';
      (parser as any).message = { role: 'assistant', content: 'test' };

      const result = await parser.get_output();

      expect(mockToolCallRunner.run_tools).not.toHaveBeenCalled();
      expect(result).toEqual({
        response_content: 'test response',
        message: { role: 'assistant', content: 'test' }
      });
    });

    it('should throw error when tool calls length is negative (edge case)', async () => {
      // This tests the final else condition which should never happen in practice
      (parser as any).toolCalls = { length: -1 }; // Force invalid state
      
      await expect(parser.get_output()).rejects.toThrow('Tool call results not ready');
    });
  });

  describe('get_output_with_should_retry', () => {
    it('should return error state when error is set', async () => {
      (parser as any).error = 'Test error';
      (parser as any).message = { role: 'assistant', content: 'test' };

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        should_retry: true,
        response_content: 'Test error',
        message: { role: 'assistant', content: 'test' }
      });
    });

    it('should return tool call results with retry flag when tool calls exist', async () => {
      const toolCalls: ChatCompletionMessageToolCall[] = [
        {
          id: 'call_123',
          type: 'function',
          function: { name: 'test_function', arguments: '{}' }
        }
      ];

      const mockSuccessResult = new ToolCallResult();
      mockSuccessResult.status = 'success';
      
      const mockErrorResult = new ToolCallResult();
      mockErrorResult.status = 'error';

      const mockResults = {
        'call_123': mockSuccessResult,
        'call_456': mockErrorResult
      };

      mockToolCallRunner.run_tools.mockResolvedValue(mockResults);

      (parser as any).toolCalls = toolCalls;
      (parser as any).responseContent = 'test response';
      (parser as any).message = { role: 'assistant', content: 'test' };

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        tool_call_results: mockResults,
        response_content: 'test response',
        message: { role: 'assistant', content: 'test' },
        should_retry: true // Always true in the current implementation
      });
    });

    it('should return should_retry false when response content exists and no tool calls', async () => {
      (parser as any).toolCalls = [];
      (parser as any).responseContent = 'test response';
      (parser as any).message = { role: 'assistant', content: 'test' };

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        response_content: 'test response',
        message: { role: 'assistant', content: 'test' },
        should_retry: false
      });
    });

    it('should return should_retry true when response content is undefined', async () => {
      (parser as any).toolCalls = [];
      (parser as any).responseContent = undefined;
      (parser as any).message = { role: 'assistant', content: 'test' };

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        response_content: undefined,
        message: { role: 'assistant', content: 'test' },
        should_retry: true
      });
    });

    it('should return should_retry true when response content is empty string', async () => {
      (parser as any).toolCalls = [];
      (parser as any).responseContent = '';
      (parser as any).message = { role: 'assistant', content: 'test' };

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        response_content: '',
        message: { role: 'assistant', content: 'test' },
        should_retry: true
      });
    });

    it('should detect error in tool call results and set should_retry', async () => {
      const toolCalls: ChatCompletionMessageToolCall[] = [
        {
          id: 'call_123',
          type: 'function',
          function: { name: 'test_function', arguments: '{}' }
        }
      ];

      const mockErrorResult = new ToolCallResult();
      mockErrorResult.status = 'error';

      const mockResults = {
        'call_123': mockErrorResult
      };

      mockToolCallRunner.run_tools.mockResolvedValue(mockResults);

      (parser as any).toolCalls = toolCalls;
      (parser as any).responseContent = 'test response';

      const result = await parser.get_output_with_should_retry();

      expect(result.should_retry).toBe(true);
    });
  });
});

describe('Integration Tests', () => {
  it('should work end-to-end with ModelIO and ModelOutputParser', () => {
    const mockPrompt: IModelPrompt = {
      get_system_prompt: jest.fn().mockReturnValue('System prompt'),
      get_messages: jest.fn().mockReturnValue([]),
      add_user_turn: jest.fn(),
      add_tool_outputs: jest.fn(),
      add_tool_output: jest.fn(),
      add_chat_completion_message: jest.fn(),
      pretty_print_conversation: jest.fn()
    };

    const mockToolCallRunner = {
      run_tools: jest.fn(),
      run_tool: jest.fn()
    } as any;

    const modelIO = new ModelIO(mockPrompt, mockToolCallRunner, 'test_intent');
    const parser = modelIO.get_output_parser();

    expect(parser).toBeInstanceOf(ModelOutputParser);
    expect(modelIO.intent).toBe('test_intent');
    expect(modelIO.prompt).toBe(mockPrompt);
  });
}); 