import { ChatIntentName, ChatSlotName } from './enums';
import { IChatIntent } from './structs';

// Chat intents for the QB system
export const CHAT_INTENTS: Record<ChatIntentName, IChatIntent> = {
  [ChatIntentName.AGENT_BUILDING]: {
    name: ChatIntentName.AGENT_BUILDING,
    description: "build an agent",
    requiredSlots: [],
    optionalSlots: [],
    requiredResultSlots: [],
    optionalResultSlots: [],
    isReferredBy(anyStr: string): boolean {
      return anyStr.toLowerCase().includes('agent') && anyStr.toLowerCase().includes('build');
    }
  },
  
  [ChatIntentName.RETRIEVER_BUILDING]: {
    name: ChatIntentName.RETRIEVER_BUILDING,
    description: "build a retriever",
    requiredSlots: [],
    optionalSlots: [],
    requiredResultSlots: [],
    optionalResultSlots: [],
    isReferredBy(anyStr: string): boolean {
      return anyStr.toLowerCase().includes('retriever') && anyStr.toLowerCase().includes('build');
    }
  },
  
  [ChatIntentName.QB]: {
    name: ChatIntentName.QB,
    description: "query Quickbooks",
    requiredSlots: [],
    optionalSlots: [],
    requiredResultSlots: [],
    optionalResultSlots: [],
    isReferredBy(anyStr: string): boolean {
      return anyStr.toLowerCase().includes('quickbooks') || anyStr.toLowerCase().includes('qb');
    }
  },
  
  [ChatIntentName.OTHER]: {
    name: ChatIntentName.OTHER,
    description: "other or unrecognized intent",
    requiredSlots: [],
    optionalSlots: [],
    requiredResultSlots: [],
    optionalResultSlots: [],
    isReferredBy(anyStr: string): boolean {
      return false; // Other intent is never directly referred to
    }
  }
};

// Helper function to get intent by name
export function getIntent(intentName: ChatIntentName): IChatIntent | undefined {
  return CHAT_INTENTS[intentName];
}

// Helper function to get all intents
export function getAllIntents(): Record<ChatIntentName, IChatIntent> {
  return CHAT_INTENTS;
}

// Helper function to get intents by category
export function getIntentsByCategory(category: string): Record<ChatIntentName, IChatIntent> {
  const categoryIntents: Record<ChatIntentName, IChatIntent> = {} as Record<ChatIntentName, IChatIntent>;
  
  Object.entries(CHAT_INTENTS).forEach(([intentName, intent]) => {
    if (intent.description.includes(category.toLowerCase())) {
      categoryIntents[intentName as ChatIntentName] = intent;
    }
  });
  
  return categoryIntents;
}

// Helper function to validate intent slots
export function validateIntentSlots(intentName: ChatIntentName, providedSlots: Record<ChatSlotName, any>): {
  isValid: boolean;
  missingRequired: ChatSlotName[];
  missingOptional: ChatSlotName[];
} {
  const intent = CHAT_INTENTS[intentName];
  if (!intent) {
    return {
      isValid: false,
      missingRequired: [],
      missingOptional: []
    };
  }
  
  const missingRequired = intent.requiredSlots.filter(slot => !(slot in providedSlots));
  const missingOptional = intent.optionalSlots?.filter(slot => !(slot in providedSlots)) || [];
  
  return {
    isValid: missingRequired.length === 0,
    missingRequired,
    missingOptional
  };
} 