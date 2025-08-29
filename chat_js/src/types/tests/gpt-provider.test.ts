import { GPTProvider } from '../../gpt-provider';
import { ModelIO, IModelPrompt, ModelOutputParser } from '../modelio';
import { ToolCallRunner } from '../../tool-call-runner';
import { LLMMonitor } from '../../llm-monitor';
import { createMockChatMessage } from './test-helpers';

// Mock dependencies
jest.mock('openai', () => {
  return {
    __esModule: true,
    default: jest.fn().mockImplementation(() => ({
      chat: {
        completions: {
          create: jest.fn()
        }
      }
    }))
  };
});

jest.mock('../../llm-monitor', () => ({
  LLMMonitor: jest.fn().mockImplementation(() => ({
    recordLlmCall: jest.fn()
  }))
}));

jest.mock('../../tool-call-runner');

describe('GPTProvider', () => {
  let gptProvider: GPTProvider;
  let mockOpenAICreate: jest.Mock;
  let mockModelIO: Partial<ModelIO>;
  let mockPrompt: Partial<IModelPrompt>;
  let mockToolCallRunner: Partial<ToolCallRunner>;
  let mockOutputParser: Partial<ModelOutputParser>;

  const mockApiKey = 'test-api-key';
  const mockModel = 'gpt-4o';

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();

    // Mock console methods to avoid noise in tests
    jest.spyOn(console, 'info').mockImplementation();
    jest.spyOn(console, 'debug').mockImplementation();
    jest.spyOn(console, 'error').mockImplementation();

    // Create mock objects
    mockOutputParser = {
      set_message: jest.fn().mockReturnThis(),
      set_error: jest.fn().mockReturnThis()
    };

    mockToolCallRunner = {
      get_enabled_tool_descriptions: jest.fn().mockResolvedValue([])
    };

    mockPrompt = {
      get_messages: jest.fn().mockReturnValue([
        { role: 'user' as const, content: 'Hello' },
        { role: 'assistant' as const, content: 'Hi there!' }
      ])
    };

    mockModelIO = {
      prompt: mockPrompt as IModelPrompt,
      tool_call_runner: mockToolCallRunner as ToolCallRunner,
      intent: 'test_intent',
      get_output_parser: jest.fn().mockReturnValue(mockOutputParser)
    };

    // Create GPTProvider instance
    gptProvider = new GPTProvider(mockApiKey, mockModel);
    
    // Get the mock OpenAI create function
    const OpenAI = require('openai').default;
    const mockClient = OpenAI.mock.results[0].value;
    mockOpenAICreate = mockClient.chat.completions.create;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('constructor', () => {
    it('should initialize with correct properties', () => {
      const OpenAI = require('openai').default;
      
      expect(OpenAI).toHaveBeenCalledWith({ apiKey: mockApiKey });
      expect(LLMMonitor).toHaveBeenCalledWith(mockModel, "GPTProvider");
      expect(console.info).toHaveBeenCalledWith(`Initialized GPTProvider with model: ${mockModel}`);
    });

    it('should use default model when not specified', () => {
      const provider = new GPTProvider(mockApiKey);
      
      expect(LLMMonitor).toHaveBeenCalledWith("gpt-4o", "GPTProvider");
      expect(console.info).toHaveBeenCalledWith(`Initialized GPTProvider with model: gpt-4o`);
    });

    it('should initialize with custom model', () => {
      const customModel = 'gpt-3.5-turbo';
      const provider = new GPTProvider(mockApiKey, customModel);
      
      expect(LLMMonitor).toHaveBeenCalledWith(customModel, "GPTProvider");
      expect(console.info).toHaveBeenCalledWith(`Initialized GPTProvider with model: ${customModel}`);
    });
  });

  describe('get_model_id', () => {
    it('should return the correct model id', () => {
      expect(gptProvider.get_model_id()).toBe(mockModel);
    });

    it('should return custom model id when specified', () => {
      const customModel = 'gpt-3.5-turbo';
      const customProvider = new GPTProvider(mockApiKey, customModel);
      
      expect(customProvider.get_model_id()).toBe(customModel);
    });
  });

  describe('getLlmMonitor', () => {
    it('should return the LLM monitor instance', () => {
      const monitor = gptProvider.getLlmMonitor();
      
      expect(monitor).toBeDefined();
    });
  });

  describe('get_response', () => {
    const mockToolDescriptions = [
      {
        type: "function" as const,
        function: {
          name: "test_function",
          description: "A test function",
          parameters: {
            type: "object",
            properties: {},
            required: []
          }
        }
      }
    ];

    beforeEach(() => {
      (mockToolCallRunner.get_enabled_tool_descriptions as jest.Mock)
        .mockResolvedValue(mockToolDescriptions);
    });

    it('should successfully call OpenAI API and return parsed response', async () => {
      const mockResponse = {
        choices: [
          {
            message: createMockChatMessage('Hello! How can I help you?')
          }
        ]
      };

      mockOpenAICreate.mockResolvedValue(mockResponse);

      const result = await gptProvider.get_response(mockModelIO as ModelIO);

      expect(mockPrompt.get_messages).toHaveBeenCalled();
      expect(mockToolCallRunner.get_enabled_tool_descriptions).toHaveBeenCalled();
      expect(mockOpenAICreate).toHaveBeenCalledWith({
        model: mockModel,
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there!' }
        ],
        max_tokens: 1000,
        temperature: 0.7,
        tools: mockToolDescriptions
      });
      expect(mockModelIO.get_output_parser).toHaveBeenCalled();
      expect(mockOutputParser.set_message).toHaveBeenCalledWith(mockResponse.choices[0]!.message);
      expect(result).toBe(mockOutputParser);
    });

    it('should handle response with tool calls', async () => {
      const mockMessageWithTools = createMockChatMessage(
        'I need to use a tool',
        'assistant',
        [
          {
            id: 'call_123',
            type: 'function',
            function: { name: 'test_function', arguments: '{}' }
          }
        ]
      );

      const mockResponse = {
        choices: [{ message: mockMessageWithTools }]
      };

      mockOpenAICreate.mockResolvedValue(mockResponse);

      const result = await gptProvider.get_response(mockModelIO as ModelIO);

      expect(mockOutputParser.set_message).toHaveBeenCalledWith(mockMessageWithTools);
      expect(result).toBe(mockOutputParser);
    });

    it('should handle empty response choices gracefully', async () => {
      const mockResponse = {
        choices: []
      };

      mockOpenAICreate.mockResolvedValue(mockResponse);

      const result = await gptProvider.get_response(mockModelIO as ModelIO);

      expect(mockOutputParser.set_error).toHaveBeenCalledWith(
        expect.any(Error)
      );
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Error in GPT response')
      );
      expect(result).toBe(mockOutputParser);
    });

    it('should handle null response choices', async () => {
      const mockResponse = {
        choices: [null]
      };

      mockOpenAICreate.mockResolvedValue(mockResponse);

      const result = await gptProvider.get_response(mockModelIO as ModelIO);

      expect(mockOutputParser.set_error).toHaveBeenCalledWith(
        expect.any(Error)
      );
      expect(result).toBe(mockOutputParser);
    });

    it('should handle OpenAI API errors', async () => {
      const mockError = new Error('OpenAI API Error');
      mockOpenAICreate.mockRejectedValue(mockError);

      const result = await gptProvider.get_response(mockModelIO as ModelIO);

      expect(mockOutputParser.set_error).toHaveBeenCalledWith(mockError);
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Error in GPT response')
      );
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('Stack trace')
      );
      expect(result).toBe(mockOutputParser);
    });

    it('should handle non-Error exceptions', async () => {
      const mockError = 'String error';
      mockOpenAICreate.mockRejectedValue(mockError);

      const result = await gptProvider.get_response(mockModelIO as ModelIO);

      expect(mockOutputParser.set_error).toHaveBeenCalledWith(mockError);
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('No stack trace')
      );
      expect(result).toBe(mockOutputParser);
    });

    it('should log debug information for requests and responses', async () => {
      const mockResponse = {
        choices: [
          {
            message: createMockChatMessage('Response')
          }
        ]
      };

      mockOpenAICreate.mockResolvedValue(mockResponse);

      await gptProvider.get_response(mockModelIO as ModelIO);

      expect(console.debug).toHaveBeenCalledWith(
        expect.stringContaining('Sending request to GPT')
      );
      expect(console.debug).toHaveBeenCalledWith(
        expect.stringContaining('GPT response')
      );
    });

    it('should pass correct parameters to OpenAI API', async () => {
      const mockResponse = {
        choices: [{ message: createMockChatMessage('Test') }]
      };

      mockOpenAICreate.mockResolvedValue(mockResponse);

      await gptProvider.get_response(mockModelIO as ModelIO);

      expect(mockOpenAICreate).toHaveBeenCalledWith({
        model: mockModel,
        messages: expect.any(Array),
        max_tokens: 1000,
        temperature: 0.7,
        tools: mockToolDescriptions
      });
    });

    it('should handle tool descriptions correctly', async () => {
      const customToolDescriptions = [
        {
          type: "function" as const,
          function: {
            name: "custom_function",
            description: "A custom function",
            parameters: {
              type: "object",
              properties: { param: { type: "string" } },
              required: ["param"]
            }
          }
        }
      ];

      (mockToolCallRunner.get_enabled_tool_descriptions as jest.Mock)
        .mockResolvedValue(customToolDescriptions);

      const mockResponse = {
        choices: [{ message: createMockChatMessage('Test') }]
      };

      mockOpenAICreate.mockResolvedValue(mockResponse);

      await gptProvider.get_response(mockModelIO as ModelIO);

      expect(mockOpenAICreate).toHaveBeenCalledWith(
        expect.objectContaining({
          tools: customToolDescriptions
        })
      );
    });
  });

  describe('Integration tests', () => {
    it('should work end-to-end with real ModelOutputParser', async () => {
      const realOutputParser = new ModelOutputParser(mockToolCallRunner as ToolCallRunner);
      (mockModelIO.get_output_parser as jest.Mock).mockReturnValue(realOutputParser);

      const mockResponse = {
        choices: [
          {
            message: createMockChatMessage('Integration test response')
          }
        ]
      };

      mockOpenAICreate.mockResolvedValue(mockResponse);

      const result = await gptProvider.get_response(mockModelIO as ModelIO);

      expect(result).toBeInstanceOf(ModelOutputParser);
      expect(result).toBe(realOutputParser);
    });
  });
}); 