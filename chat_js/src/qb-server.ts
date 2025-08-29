import { 
  IModelProvider, 
  ModelIO, 
  TMessage,
  ModelOutputParser,
} from './types/modelio';
import { QBServerSuccessPrompt } from './qb-server-success-prompt';
import { IIntentServer, IntentServerInput } from './types/intent-server';
import { ChatIntentName, ChatSlotName, SenderType } from './types/enums';
import { GPTProvider } from './gpt-provider';
import { ChatCompletionMessage } from 'openai/resources/chat/completions';
import { ToolCallRunner } from './tool-call-runner';
import { ChatMessage } from "./types/implementations";
import { PrismaService, ToolCallResult } from 'coralbricks-common';
import { AssistantStream } from 'openai/lib/AssistantStream';

export class QBServer extends IIntentServer {
  private model_provider: IModelProvider;
  private cbId: bigint = BigInt("4611686018427387904");
  
  constructor(model_provider: IModelProvider) {
    super(ChatIntentName.QB);
    this.model_provider = model_provider;
  }

  static create_model_io(threadId: bigint, userId: bigint): ModelIO {
    return new ModelIO(
      new QBServerSuccessPrompt(),
      new ToolCallRunner(threadId, userId),
      ChatIntentName.QB
    );
  }
  /**
   * Create a QBServer with GPT provider
   */
  static withGPTProvider(apiKey: string, model: string = "gpt-4o"): QBServer {
    const gptProvider = new GPTProvider(apiKey, model);
    return new QBServer(gptProvider);
  }

  get_cbId(): bigint {
    return this.cbId;
  }

  // Abstract method implementations with correct signatures
  async runTools(input: IntentServerInput): Promise<any> {
    console.log(`Running tools for ${this.myIntent}: ${input.userId}`);
    return {};
  }

  async useToolOutput(toolsOutput: any, input: IntentServerInput): Promise<void> {
    console.log(`Using tool output: ${toolsOutput}`);
    
    // Convert IChatMessage[] to TMessage[]
    const convertToTMessage = (chatMessages: any[]): TMessage[] => {
      return chatMessages.map(msg => ({
        role: msg.senderType === 'user' ? 'user' : 'assistant',
        content: msg.body || msg.content || ''
      }));
    };
    
    // Create TMessage from userTurn
    const userTurn: TMessage = {
      role: input.userTurn.senderType === 'user' ? 'user' : 'assistant',
      content: input.userTurn.body || ''
    };
    
    input.modelIO.prompt.add_user_turn(userTurn);

    // Log initial conversation state
    console.log("Initial conversation state:");
    input.modelIO.prompt.pretty_print_conversation();
    
    let output = await this.run_model_once(input);
    
    while (output.should_loop_model) {
      output = await this.run_model_once(input);
      
      // Log conversation state after each iteration
      console.log(`Conversation state after iteration:`);
      input.modelIO.prompt.pretty_print_conversation();
    }    
  }

  async handleMissingSlots(missingSlots: ChatSlotName[], input: IntentServerInput): Promise<void> {
    console.log(`Handling missing slots:`, missingSlots);  
  }

  // Legacy methods for backward compatibility - remove if not needed
  async run_tools(input: any): Promise<any> {
    console.log(`Legacy run_tools called for ${this.myIntent}`);
    return {};
  }
  
  async saveModelEvent(
    input: IntentServerInput, 
    output: {
      tool_call_results?: Record<string, ToolCallResult>;
      response_content?: string;
      message?: ChatCompletionMessage;
      should_loop_model?: boolean;
  }, assistant_to_user_message_cbId: bigint | null): Promise<bigint | null> {
    try {
      // Use shared Prisma service
      const prisma_client = PrismaService.getInstance();
      const model_event = await prisma_client.modelEvent.create({
        data: {
          systemPrompt: input.modelIO.prompt.get_system_prompt(),
          toolCalls: output.tool_call_results ? Object.values(output.tool_call_results).map(tcr => tcr.to_json()) : "",
          responseContent: output.response_content,
          inputPrompt: input.modelIO.prompt.get_json_conversation_after_system_prompt(),
          threadId: input.threadId,
          senderId: this.get_cbId(),
          modelId: this.model_provider.get_model_id(),
          cbProfileId: input.userId,
          assistantMessageId: assistant_to_user_message_cbId || undefined,
        },
      });
      return model_event.cbId;
    } catch (error) {
      console.error('Failed to save model event:', error);
      // Don't throw error to avoid breaking the main flow
      return null;
    }
  }

  private async run_model_once(input: IntentServerInput): Promise<{
    tool_call_results?: any;
    response_content?: string;
    message?: ChatCompletionMessage;
    should_loop_model?: boolean;
  }> {
    const parser = await this.model_provider.get_response(input.modelIO);
    const output = await parser.get_output_with_should_loop_model();
    
    // send any response content to the user, if it exists
    let assistant_to_user_message_cbId: bigint | null = null;
    if (output.response_content) {
      assistant_to_user_message_cbId = await input.session.handleAssistantMessage(
        this.get_cbId(),
        output.response_content,
        SenderType.QB_BUILDER,
        ChatIntentName.QB,
        {} as Record<ChatSlotName, any>
      );
      console.log(`Assistant to user message cbId: ${assistant_to_user_message_cbId}`);
    }
    const model_event_id = await this.saveModelEvent(input, output, assistant_to_user_message_cbId || null);
    
    // add assistant turn to the intent server:model conversation
    if (output.message) {
      input.modelIO.prompt.add_chat_completion_message(output.message);
    } else {
      console.warn('Model response did not include a message');
    }
   
    // prepare for the next intent server to model message by 
    // adding tool call outputs to the intent server:model conversation
    if (output.tool_call_results) {
      input.modelIO.prompt.add_tool_outputs(output.tool_call_results);
    }
    return output;
  }

  private _handle_missing_slots(missing_slots: string[], input: any): Record<string, any> {
    return {};
  }
} 