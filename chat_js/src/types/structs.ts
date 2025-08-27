import { 
  ChatIntentName, 
  ChatSlotName, 
  SenderType, 
} from './enums';

export interface IChatSlot {
  name: string;
  type: string;
  description: string;
  
  isReferredBy(anyStr: string): boolean;
}

export interface IChatIntent {
  name: string;
  description: string;
  requiredSlots: ChatSlotName[];
  requiredResultSlots: ChatSlotName[];
  optionalSlots?: ChatSlotName[];
  optionalResultSlots?: ChatSlotName[];
  
  isReferredBy(anyStr: string): boolean;
}

export interface IChatMessage {
  cbId: bigint;
  threadId: bigint;
  createdAt: number;
  body: string;
  intent: ChatIntentName;
  slots?: Record<ChatSlotName, any>;
  senderId: bigint;
  receiverId: bigint;
  senderType: SenderType;
}

export interface IErrorResponse {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
  requestId?: string;
}

export interface ISuccessResponse<T = any> {
  success: true;
  data: T;
  timestamp: Date;
  requestId?: string;
}

export interface IApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: IErrorResponse;
  timestamp: Date;
  requestId?: string;
}

// Utility types
export type ChatSlotValue = string | number | boolean | Date | object | null;
export type ChatSlots = Record<ChatSlotName, ChatSlotValue>;
export type MessageMetadata = Record<string, any>; 