import { 
  IModelProvider, 
  ModelIO, 
  TMessage,
  ModelOutputParser,
} from './types/modelio';
import { QBServerSuccessPrompt } from './qb-server-success-prompt';
import { IIntentServer, IntentServerInput, IntentServerOutput } from './types/intent-server';
import { ChatIntentName, ChatSlotName, SenderType } from './types/enums';
import { GPTProvider } from './gpt-provider';
import { ChatCompletionMessage } from 'openai/resources/chat/completions';
import { ToolCallRunner } from './tool-call-runner';
import { ChatMessage } from "./types/implementations";

export class QBServer extends IIntentServer {
  private model_provider: IModelProvider;
  // private prompt: QBServerSuccessPrompt | null = null;
  private modelIO: ModelIO | null = null;
  private cbId: bigint = BigInt("4611686018427387904");

  constructor(model_provider: IModelProvider) {
    super(ChatIntentName.QB);
    this.model_provider = model_provider;
  }

  /**
   * Create a QBServer with GPT provider
   */
  static withGPTProvider(apiKey: string, model: string = "gpt-4o"): QBServer {
    const gptProvider = new GPTProvider(apiKey, model);
    return new QBServer(gptProvider);
  }

  get_cbId(): bigint {
    console.log(`getting cbId for ${this.myIntent}: ${this.cbId}`);
    return this.cbId;
  }

  // Abstract method implementations with correct signatures
  async runTools(input: IntentServerInput): Promise<any> {
    console.log(`Running tools for ${this.myIntent}: ${input.userId}`);
    return {};
  }

  async useToolOutput(toolsOutput: any, input: IntentServerInput): Promise<IntentServerOutput> {
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
    
    if (this.modelIO === null) {
      const toolCallRunner = new ToolCallRunner(input.threadId, input.userId);
      this.modelIO = new ModelIO(
        new QBServerSuccessPrompt(),
        toolCallRunner,
        this.myIntent
      );
    } else {
      this.modelIO.prompt.add_user_turn(userTurn);
    }

    // Log initial conversation state
    console.log("Initial conversation state:");
    this.modelIO.prompt.pretty_print_conversation();
    
    let output = await this.run_model_once();
    
    while (output.should_retry) {
      // prepare to send tool calls output to the model 
      if (output.tool_call_results) {
        this.modelIO.prompt.add_tool_outputs(output.tool_call_results);
      }
      output = await this.run_model_once();
      
      // Log conversation state after each iteration
      console.log(`Conversation state after iteration:`);
      this.modelIO.prompt.pretty_print_conversation();
    }
    
    return new IntentServerOutput(input.threadId, input.userId, this.createAssistantTurn(output.response_content || '', input));
  }

  async handleMissingSlots(missingSlots: ChatSlotName[], input: IntentServerInput): Promise<IntentServerOutput> {
    console.log(`Handling missing slots:`, missingSlots);  
    return new IntentServerOutput(input.threadId, input.userId, this.createAssistantTurn(`Please provide the following missing information: ${missingSlots.join(', ')}`, input));
  }

  // Legacy methods for backward compatibility - remove if not needed
  async run_tools(input: any): Promise<any> {
    console.log(`Legacy run_tools called for ${this.myIntent}`);
    return {};
  }
  
  createAssistantTurn(content: string, input: IntentServerInput): ChatMessage {
    const assitant_turn_cbid = 456;
    return new ChatMessage(
      BigInt(assitant_turn_cbid),
      input.threadId,
      Date.now(),
      this.get_cbId(),
      input.userId,
      content,
      SenderType.QB_BUILDER,
      ChatIntentName.QB,
      {} as Record<ChatSlotName, any>
    );
  }

  private async run_model_once(): Promise<{
    tool_call_results?: any;
    response_content?: string;
    message?: ChatCompletionMessage;
    should_retry?: boolean;
  }> {
    if (!this.modelIO) {
      throw new Error('ModelIO not initialized');
    }

    if (!this.model_provider) {
      throw new Error('Model provider not initialized');
    }

    const parser = await this.model_provider.get_response(this.modelIO);
    const output = await parser.get_output();
    this.modelIO.prompt.add_chat_completion_message(output.message);
    return output;
  }

  private _handle_missing_slots(missing_slots: string[], input: any): Record<string, any> {
    return {};
  }
} 