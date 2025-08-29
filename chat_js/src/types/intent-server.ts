import { IChatMessage } from './structs';
import { ChatSlotName, ChatIntentName, SenderType } from './enums';
import { ChatMemory } from './memory';
import { ChatMessage } from './implementations';
import { ModelIO } from './modelio';

export interface AssistantToUserMessageSender {
  handleAssistantMessage: (
    intent_server_cbid: bigint,
    body: string,
    sender_type: SenderType,
    intent_name: ChatIntentName,
    slots: Record<ChatSlotName, any>
  ) => Promise<bigint>;
}

export class IntentServerInput {
  constructor(
    public threadId: bigint,
    public userId: bigint,
    public userTurn: IChatMessage,
    public chatMemory: ChatMemory,
    public session: AssistantToUserMessageSender,
    public modelIO: ModelIO,
  ) {}
  toString(): string {
    return `IntentServerInput(threadId: ${this.threadId}, userId: ${this.userId}, userTurn: ${this.userTurn}, chatMemory: ${this.chatMemory})`;
  }
}

// Abstract Intent Server - similar to Python IIntentServer
export abstract class IIntentServer {
  protected gatheredSlots: Record<ChatSlotName, any> = {} as Record<ChatSlotName, any>;
  protected collabServers: ChatIntentName[] = [];
  protected myIntent: ChatIntentName;
  constructor(myIntent: ChatIntentName) {
    this.myIntent = myIntent;
  }

  updateSlots(slots: Record<ChatSlotName, any>): void {
    for (const [slotEnum, slotValue] of Object.entries(slots)) {
      const slotName = slotEnum as ChatSlotName;
      if (this.isRequiredSlot(slotName) || this.isOptionalSlot(slotName)) {
        this.gatheredSlots[slotName] = slotValue;
      } else {
        console.warn(`Slot ${slotName} is not a required or optional slot for intent ${this.myIntent}`);
      }
    }
  }

  canContinueWithRequest(): { canContinue: boolean; missingSlots: ChatSlotName[] } {
    const missingSlots = this.missingSlots();
    return { canContinue: missingSlots.length === 0, missingSlots };
  }

  missingSlots(): ChatSlotName[] {
    const requiredSlots = this.getRequiredSlots();
    return requiredSlots.filter(slot => !(slot in this.gatheredSlots));
  }

  async serve(input: IntentServerInput): Promise<void> {
    console.log(`Serving intent: ${this.myIntent} with input: ${input}`);
    this.updateSlots(input.userTurn.slots || {} as Record<ChatSlotName, any>);
    
    const { canContinue, missingSlots } = this.canContinueWithRequest();
    if (canContinue) {
      const toolsOutput = await this.runTools(input);
      await this.useToolOutput(toolsOutput, input);
    } else {
      await this.handleMissingSlots(missingSlots, input);
    }
  }

  collabGptToolSchemas(): Record<string, Record<string, any>> {
    // This would need an intent registry to work properly
    // For now, return empty object
    return {};
  }

  gptToolSchema(): Record<string, any> {
    const requiredSlots = this.getRequiredSlots();
    const optionalSlots = this.getOptionalSlots();
    
    return {
      type: "function",
      function: {
        name: this.myIntent,
        description: this.getIntentDescription(),
        parameters: {
          type: "object",
          properties: this.buildSlotProperties([...requiredSlots, ...optionalSlots]),
          required: requiredSlots.map(slot => slot)
        }
      }
    };
  }

  validateSlots(slots: Record<ChatSlotName, any>): boolean {
    // Not implemented right now
    // Use case is when user provides a bad value, that slot 
    // shouldn't be accepted by the server and assistant should respond right away 
    // with the error instead of waiting for all slots before invoking the 
    // intent server.
    return true;
  }

  // Abstract methods that must be implemented by subclasses
  abstract runTools(input: IntentServerInput): Promise<any>;
  abstract useToolOutput(toolsOutput: any, input: IntentServerInput): Promise<void>;
  abstract handleMissingSlots(missingSlots: ChatSlotName[], input: IntentServerInput): Promise<void>;
  abstract get_cbId(): bigint;

  // Helper methods
  protected isRequiredSlot(slotName: ChatSlotName): boolean {
    return this.getRequiredSlots().includes(slotName);
  }

  protected isOptionalSlot(slotName: ChatSlotName): boolean {
    return this.getOptionalSlots().includes(slotName);
  }

  protected getRequiredSlots(): ChatSlotName[] {
    // This would come from intent configuration
    // For now, return empty array
    return [];
  }

  protected getOptionalSlots(): ChatSlotName[] {
    // This would come from intent configuration
    // For now, return empty array
    return [];
  }

  protected getIntentDescription(): string {
    // This would come from intent configuration
    return `Handle ${this.myIntent} intent`;
  }

  private buildSlotProperties(slots: ChatSlotName[]): Record<string, any> {
    const properties: Record<string, any> = {};
    for (const slot of slots) {
      properties[slot] = { type: "string" }; // Default to string type
    }
    return properties;
  }
}