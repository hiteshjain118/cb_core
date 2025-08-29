import OpenAI from 'openai';
import { LLMMonitor } from './llm-monitor';
import { ModelIO, IModelProvider, ModelOutputParser } from './types/modelio';
import { ToolDescription } from 'coralbricks-common';

/**
 * OpenAI GPT model provider implementation
 */
export class GPTProvider implements IModelProvider {
  private apiKey: string;
  private model: string;
  private client: OpenAI;
  private llmMonitor: LLMMonitor;

  constructor(apiKey: string, model: string = "gpt-4o") {
    this.apiKey = apiKey;
    this.model = model;
    this.client = new OpenAI({ apiKey: apiKey });
    this.llmMonitor = new LLMMonitor(model, "GPTProvider");
    
    console.info(`Initialized GPTProvider with model: ${model}`);
  }

  async get_response(modelIO: ModelIO): Promise<ModelOutputParser> {
    const messages = modelIO.prompt.get_messages();

    console.debug(`Sending request to GPT: ${JSON.stringify(messages)}, from prompt_type: ${typeof modelIO.prompt}`);

    try {
      // Make the actual OpenAI API call
      const response = await this.client.chat.completions.create({
        model: this.model,
        messages: messages as OpenAI.Chat.Completions.ChatCompletionMessageParam[],
        max_tokens: 1000,
        temperature: 0.7,
        tools: await modelIO.tool_call_runner.get_enabled_tool_descriptions(),
      });

      console.debug(`GPT response: ${JSON.stringify(response)}`);

      // Get the response content
      const choice = response.choices[0];
      if (!choice) {
        throw new Error('No choices returned from OpenAI API');
      }
      const message = choice.message;

      // Record LLM call for monitoring
      // this.llmMonitor.recordLlmCall(
      //   messages,
      //   modelIO.intent,
      //   message.content || '',
      //   message.tool_calls || [],
      //   ''
      // );

      return modelIO.get_output_parser().set_message(message);

    } catch (error: unknown) {
      console.error(`Error in GPT response: ${error}`);
      console.error(`Stack trace: ${error instanceof Error ? error.stack : 'No stack trace'}`);
      
      // Return error response
      return modelIO.get_output_parser().set_error(error);
    }
  }

  get_model_id(): string {
    return this.model;
  }

  /**
   * Get the LLM monitor for this provider
   */
  getLlmMonitor(): LLMMonitor {
    return this.llmMonitor;
  }
}

// GPTModelOutputParser class removed - using direct object implementation instead 