import { ModelIO, ModelOutputParser, IModelPrompt } from '../modelio';
import { ToolCallRunner } from '../../tool-call-runner';
import { ToolCallResult } from 'coralbricks-common';
import { ChatCompletionMessage, ChatCompletionMessageToolCall } from 'openai/resources/chat/completions';
import { createMockToolCallResult, createMockChatMessage } from './test-helpers';

// Mock dependencies
jest.mock('../../tool-call-runner');

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
      const message = createMockChatMessage('```json\n{"response": "test"}\n```');
      const result = parser.set_message(message);
      
      expect(result).toBe(parser);
      expect((parser as any).message).toBe(message);
      expect((parser as any).responseContent).toBe('\n{"response": "test"}\n');
    });

    it('should handle message with tool calls', async () => {
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

      const message = createMockChatMessage('Using tool', 'assistant', toolCalls);
      parser.set_message(message);
      expect((parser as any).toolCalls).toEqual(toolCalls);
      expect((parser as any).responseContent).toBe('Using tool'); 
    });

    it('should handle message without content', () => {
      const message = createMockChatMessage(null);
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
        'call_123': createMockToolCallResult('success', 'test_tool', 'call_123', BigInt(1))
      };

      mockToolCallRunner.run_tools.mockResolvedValue(mockResults);

      // Set up parser state
      (parser as any).toolCalls = toolCalls;
      (parser as any).responseContent = 'test response';
      (parser as any).message = createMockChatMessage('test');

      const result = await parser.get_output();

      expect(mockToolCallRunner.run_tools).toHaveBeenCalledWith(toolCalls);
      expect(result).toEqual({
        tool_call_results: mockResults,
        response_content: 'test response',
        message: expect.any(Object)
      });
    });

    it('should return response content when no tool calls', async () => {
      (parser as any).toolCalls = [];
      (parser as any).responseContent = 'test response';
      (parser as any).message = createMockChatMessage('test');

      const result = await parser.get_output();

      expect(mockToolCallRunner.run_tools).not.toHaveBeenCalled();
      expect(result).toEqual({
        response_content: 'test response',
        message: expect.any(Object)
      });
    });
  });

  describe('get_output_with_should_retry', () => {
    it('should return error state when error is set', async () => {
      (parser as any).error = 'Test error';
      (parser as any).message = createMockChatMessage('test');

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        should_retry: true,
        response_content: 'Test error',
        message: expect.any(Object)
      });
    });

    it('should return should_retry false when response content exists and no tool calls', async () => {
      (parser as any).toolCalls = [];
      (parser as any).responseContent = 'test response';
      (parser as any).message = createMockChatMessage('test');

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        response_content: 'test response',
        message: expect.any(Object),
        should_retry: false
      });
    });

    it('should return should_retry true when response content is undefined', async () => {
      (parser as any).toolCalls = [];
      (parser as any).responseContent = undefined;
      (parser as any).message = createMockChatMessage('test');

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        response_content: undefined,
        message: expect.any(Object),
        should_retry: true
      });
    });

    it('should return should_retry true when response content is empty string', async () => {
      (parser as any).toolCalls = [];
      (parser as any).responseContent = '';
      (parser as any).message = createMockChatMessage('test');

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        response_content: '',
        message: expect.any(Object),
        should_retry: true
      });
    });

    it('should return should_retry true when tool call results are error', async () => {
      const toolCalls: ChatCompletionMessageToolCall[] = [
        {
          id: 'call_123',
          type: 'function',
          function: { name: 'test_function', arguments: '{}' }
        }
      ];
      const mockResults = {
        'call_123': createMockToolCallResult('error', 'test_function', 'call_123', BigInt(1))
      };
      mockToolCallRunner.run_tools.mockResolvedValue(mockResults);
      (parser as any).toolCalls = toolCalls;
      (parser as any).responseContent = 'test response';
      (parser as any).message = createMockChatMessage('test');

      const result = await parser.get_output_with_should_retry();

      expect(result).toEqual({
        tool_call_results: mockResults,
        response_content: 'test response',
        message: expect.any(Object),
        should_retry: true
      });
    });
  });
});