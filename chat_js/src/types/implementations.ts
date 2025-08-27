import { 
  IChatSlot, 
  IChatIntent, 
  IChatMessage, 
} from './structs';
import {
  ChatSlotName,
  ChatIntentName,
  SenderType,
} from './enums';

export class ChatSlot implements IChatSlot {
  constructor(
    public name: string,
    public type: string,
    public description: string
  ) {}

  isReferredBy(anyStr: string): boolean {
    return anyStr.toLowerCase() === this.name.toLowerCase();
  }
}

export class ChatIntent implements IChatIntent {
  constructor(
    public name: string,
    public description: string,
    public requiredSlots: ChatSlotName[],
    public requiredResultSlots: ChatSlotName[],
    public optionalSlots: ChatSlotName[] = [],
    public optionalResultSlots: ChatSlotName[] = []
  ) {}

  isReferredBy(anyStr: string): boolean {
    return anyStr.toLowerCase() === this.name.toLowerCase();
  }
}

export class ChatMessage implements IChatMessage {
  constructor(
    public cbId: bigint,
    public threadId: bigint,
    public createdAt: number,
    public senderId: bigint,
    public receiverId: bigint,
    public body: string,
    public senderType: SenderType,
    public intent: ChatIntentName,
    public slots?: Record<ChatSlotName, any>,
  ) {
    this.cbId = cbId;
    this.threadId = threadId;
    this.createdAt = createdAt;
    this.senderId = senderId;
    this.receiverId = receiverId;
    this.body = body;
    this.intent = intent;
    this.slots = slots;
    this.senderType = senderType;
  }

  addSlot(name: ChatSlotName, value: any): void {
    if (!this.slots) {
      this.slots = {} as Record<ChatSlotName, any>;
    }
    this.slots[name] = value;
  }

  getSlot(name: ChatSlotName): any {
    return this.slots?.[name];
  }

  hasSlot(name: ChatSlotName): boolean {
    return this.slots ? name in this.slots : false;
  }

  toString(): string {
    return `ChatMessage(cbId: ${this.cbId}, threadId: ${this.threadId}, createdAt: ${this.createdAt}, senderId: ${this.senderId}, receiverId: ${this.receiverId}, body: ${this.body}, senderType: ${this.senderType}, intent: ${this.intent}, slots: ${this.slots})`;
  }
}