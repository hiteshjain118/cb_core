import { IChatMessage } from './structs';
import { ChatSlotName, SenderType } from './enums';
import { PrismaService } from 'coralbricks-common';

export interface IChatMemory {
  userId: bigint;
  conversationHistory: IChatMessage[];
  slots: Record<ChatSlotName, any>;
  
  addMessage(message: IChatMessage): void;
  getConversationHistory(): IChatMessage[];
  conversationSummary(): string;
  lastUserTurn(): { message: IChatMessage | null; index: number };
  lastUserTurnIndex(): number;
  conversationHistoryBeforeLastUserTurn(): string;
  clearMemory(): void;
  getSlotValue(slotName: ChatSlotName): any;
  setSlotValue(slotName: ChatSlotName, value: any): void;
  hasSlot(slotName: ChatSlotName): boolean;
  getMemorySize(): number;
  isMemoryFull(maxSize?: number): boolean;
}

export class ChatMemory implements IChatMemory {
  public conversationHistory: IChatMessage[] = [];
  public slots: Record<ChatSlotName, any> = {} as Record<ChatSlotName, any>;

  constructor(public userId: bigint) {}

  async addMessage(message: IChatMessage): Promise<bigint>   {
    message.cbId = await this.set_message_in_db(message);
    this.conversationHistory.push(message);
    
    // Update slots from message if they exist
    if (message.slots) {
      this.slots = { ...this.slots, ...message.slots };
    }
    return message.cbId;
  }

  getConversationHistory(): IChatMessage[] {
    return [...this.conversationHistory];
  }

  conversationSummary(): string {
    return this.conversationHistory
      .map(message => `${message.senderId || 'Unknown'}: ${message.body}`)
      .join('\n');
  }

  lastUserTurn(): { message: IChatMessage | null; index: number } {
    for (let index = this.conversationHistory.length - 1; index >= 0; index--) {
      const message = this.conversationHistory[index];
      if (message && message.senderId) {
        return { message, index };
      }
    }
    return { message: null, index: -1 };
  }

  lastUserTurnIndex(): number {
    return this.lastUserTurn().index;
  }

  conversationHistoryBeforeLastUserTurn(): string {
    const lastUserIdx = this.lastUserTurnIndex();
    if (lastUserIdx <= 0) {
      return '';
    }

    // Find the last bot message before the last user turn
    for (let idx = lastUserIdx - 1; idx >= 0; idx--) {
      const message = this.conversationHistory[idx];
      if (message && !message.senderId) {
                  return this.conversationHistory
            .slice(0, idx + 1)
            .map(m => `${m.senderId || 'System'}: ${m.body}`)
            .join('\n');
      }
    }

    // If no bot message, return up to before last user turn
    return this.conversationHistory
      .slice(0, lastUserIdx)
      .map(m => `${m.senderId || 'System'}: ${m.body}`)
      .join('\n');
  }

  clearMemory(): void {
    this.conversationHistory = [];
    this.slots = {} as Record<ChatSlotName, any>;
  }

  getSlotValue(slotName: ChatSlotName): any {
    return this.slots[slotName];
  }

  setSlotValue(slotName: ChatSlotName, value: any): void {
    this.slots[slotName] = value;
  }

  hasSlot(slotName: ChatSlotName): boolean {
    return slotName in this.slots;
  }

  getMemorySize(): number {
    return this.conversationHistory.length;
  }

  isMemoryFull(maxSize: number = 1000): boolean {
    return this.conversationHistory.length >= maxSize;
  }

  // Additional utility methods
  getRecentMessages(count: number = 10): IChatMessage[] {
    return this.conversationHistory.slice(-count);
  }

  getMessagesBySenderType(senderType: SenderType): IChatMessage[] {
    return this.conversationHistory.filter(message => message.senderType === senderType);
  }

  getMessagesByIntent(intent: string): IChatMessage[] {
    return this.conversationHistory.filter(message => message.intent === intent);
  }

  getSlotsSummary(): string {
    const slotEntries = Object.entries(this.slots);
    if (slotEntries.length === 0) return 'No slots stored';
    
    return slotEntries
      .map(([slot, value]) => `${slot}: ${value}`)
      .join(', ');
  }

  toString(): string {
    const slotsStr = Object.entries(this.slots)
      .map(([slot, value]) => `${slot}: ${value}`)
      .join(', ');
    
    return `User ID: ${this.userId} messages: ${this.conversationHistory.length} slots: {${slotsStr}}`;
  }
  async set_message_in_db(message: IChatMessage): Promise<bigint> {
    const prisma_client = PrismaService.getInstance();
    const message_in_db = await prisma_client.message.create({
      data: {
        threadId: message.threadId,
        senderId: message.senderId,
        receiverId: message.receiverId,
        body: message.body,
      },
    });
    return message_in_db.cbId;
  }
}