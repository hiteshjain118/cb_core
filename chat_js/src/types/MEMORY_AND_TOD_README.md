# Memory and Task-Oriented Dialogue (TOD) Types

This document describes the TypeScript implementation of memory management and task-oriented dialogue systems, inspired by the Python `builder_package.core.memory` and `builder_package.core.tod_types`.

## 🧠 Memory System

### Overview

The memory system provides conversation history tracking and slot management for individual users, similar to Python's `STMemory` class.

### Key Components

#### `IChatMemory` Interface & `ChatMemory` Class

```typescript
interface IChatMemory {
  userId: string;
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
```

**Key Methods:**
- `addMessage()`: Adds message to history and updates slots
- `conversationSummary()`: Returns formatted conversation history
- `lastUserTurn()`: Finds the last user message in conversation
- `conversationHistoryBeforeLastUserTurn()`: Gets context before last user input

#### `MemoryManager` Class

Manages multiple user memories with statistics and cleanup capabilities.

```typescript
class MemoryManager {
  getUserMemory(userId: string): ChatMemory;
  hasUserMemory(userId: string): boolean;
  removeUserMemory(userId: string): boolean;
  getAllUserIds(): string[];
  getMemoryCount(): number;
  clearAllMemories(): void;
  getMemoryStats(): MemoryStats;
  cleanupInactiveMemories(maxAge?: number): number;
}
```

### Memory Usage Example

```typescript
import { ChatMemory, MemoryManager } from '../types';

// Create user memory
const userMemory = new ChatMemory('user_123');

// Add messages
userMemory.addMessage(userMessage);
userMemory.addMessage(botResponse);

// Get conversation summary
console.log(userMemory.conversationSummary());

// Check last user turn
const { message, index } = userMemory.lastUserTurn();

// Manage multiple users
const memoryManager = new MemoryManager();
const aliceMemory = memoryManager.getUserMemory('alice');
const bobMemory = memoryManager.getUserMemory('bob');

// Get statistics
const stats = memoryManager.getMemoryStats();
```

## 🎯 Task-Oriented Dialogue (TOD) System

### Overview

The TOD system provides intent-based conversation handling with slot filling and validation, similar to Python's `IIntentServer` and `IntentRegistry`.

### Key Components

#### `IIntentServer` Abstract Class

Base class for all intent servers with slot management and validation.

```typescript
abstract class IIntentServer {
  protected gatheredSlots: Record<ChatSlotName, any>;
  protected collabServers: ChatIntentName[];
  
  abstract runTools(input: IIntentServerInput): any;
  abstract useToolOutput(toolsOutput: any, input: IIntentServerInput): any;
  abstract handleMissingSlots(missingSlots: ChatSlotName[], input: IIntentServerInput): any;
  
  updateSlots(slots: Record<ChatSlotName, any>): void;
  canContinueWithRequest(): { canContinue: boolean; missingSlots: ChatSlotName[] };
  missingSlots(): ChatSlotName[];
  serve(input: IIntentServerInput): any;
  gptToolSchema(): Record<string, any>;
}
```

#### `BaseIntentServer` Class

Provides common functionality and helper methods for intent servers.

```typescript
abstract class BaseIntentServer extends IIntentServer {
  protected validateSlotValue(slotName: ChatSlotName, value: any): boolean;
  protected createErrorResponse(message: string, code?: string): any;
  protected createSuccessResponse(data: any, message?: string): any;
  protected createMissingSlotsResponse(missingSlots: ChatSlotName[]): any;
}
```

#### `IntentRegistry` Class

Manages registration and retrieval of intent servers.

```typescript
class IntentRegistry {
  register(intent: ChatIntentName, server: IIntentServer): void;
  server(intent: ChatIntentName): IIntentServer | undefined;
  hasIntent(intent: ChatIntentName): boolean;
  getAllIntents(): ChatIntentName[];
  getIntentCount(): number;
  unregister(intent: ChatIntentName): boolean;
  clear(): void;
  getServers(): IIntentServer[];
}
```

#### `IntentServerFactory` Class

Factory pattern for creating intent server instances.

```typescript
class IntentServerFactory {
  createIntentServer(intent: ChatIntentName): IIntentServer | null;
  registerIntentServer(intent: ChatIntentName, serverClass: new (intent: ChatIntentName) => IIntentServer): void;
  getAvailableIntents(): ChatIntentName[];
  hasServerClass(intent: ChatIntentName): boolean;
  unregisterIntentServer(intent: ChatIntentName): boolean;
  clear(): void;
}
```

### Intent Server Implementation Example

```typescript
import { BaseIntentServer, ChatIntentName, ChatSlotName } from '../types';

export class JoinRoomIntentServer extends BaseIntentServer {
  constructor() {
    super(ChatIntentName.JOIN_ROOM);
  }

  protected getRequiredSlots(): ChatSlotName[] {
    return [ChatSlotName.USERNAME, ChatSlotName.ROOM_NAME];
  }

  protected getOptionalSlots(): ChatSlotName[] {
    return [ChatSlotName.ROOM_PASSWORD];
  }

  runTools(input: IIntentServerInput): any {
    const { username, roomName, roomPassword } = this.extractSlots();
    return { action: 'join_room', username, roomName, roomPassword };
  }

  useToolOutput(toolsOutput: any, input: IIntentServerInput): any {
    // Handle successful room join
    return this.createSuccessResponse({
      message: `Successfully joined room: ${toolsOutput.roomName}`,
      action: 'room_joined'
    });
  }

  handleMissingSlots(missingSlots: ChatSlotName[], input: IIntentServerInput): any {
    return this.createMissingSlotsResponse(missingSlots);
  }
}
```

## 🔄 Complete System Integration

### Setting Up the System

```typescript
import { 
  MemoryManager, 
  IntentRegistry, 
  IntentServerFactory,
  JoinRoomIntentServer,
  SendMessageIntentServer 
} from '../types';

class ChatSystem {
  private memoryManager: MemoryManager;
  private intentRegistry: IntentRegistry;
  private intentFactory: IntentServerFactory;

  constructor() {
    this.memoryManager = new MemoryManager();
    this.intentRegistry = new IntentRegistry();
    this.intentFactory = new IntentServerFactory();
    
    this.setupIntentServers();
  }

  private setupIntentServers(): void {
    // Register intent servers
    const joinServer = new JoinRoomIntentServer();
    const sendServer = new SendMessageIntentServer();

    this.intentRegistry.register(ChatIntentName.JOIN_ROOM, joinServer);
    this.intentRegistry.register(ChatIntentName.SEND_MESSAGE, sendServer);
  }

  handleUserMessage(userId: string, message: IChatMessage): any {
    // Get user memory
    const userMemory = this.memoryManager.getUserMemory(userId);
    userMemory.addMessage(message);

    // Create intent input
    const input = new IntentServerInput(userId, message, userMemory);

    // Get and serve intent
    const intentServer = this.intentRegistry.server(message.intent);
    if (intentServer) {
      return intentServer.serve(input);
    }

    return { error: 'Intent not supported' };
  }
}
```

### Conversation Flow

1. **User Input**: User sends message with intent and slots
2. **Memory Update**: Message added to user's conversation history
3. **Intent Detection**: System identifies intent from message
4. **Slot Extraction**: Required and optional slots extracted
5. **Validation**: Check if all required slots are present
6. **Execution**: Run intent-specific logic (tools)
7. **Response**: Generate appropriate response based on result
8. **Memory Update**: Store response and update slots

### Slot Management

```typescript
// Slots are automatically extracted from messages
const message = new ChatMessage(
  MessageRole.USER,
  'I want to join room general',
  ChatIntentName.JOIN_ROOM,
  Date.now(),
  {
    [ChatSlotName.USERNAME]: 'alice',
    [ChatSlotName.ROOM_NAME]: 'general'
  } as Record<ChatSlotName, any>
);

// Intent server processes slots
intentServer.updateSlots(message.slots);
const { canContinue, missingSlots } = intentServer.canContinueWithRequest();

if (canContinue) {
  // Execute intent
  const result = intentServer.runTools(input);
  return intentServer.useToolOutput(result, input);
} else {
  // Request missing slots
  return intentServer.handleMissingSlots(missingSlots, input);
}
```

## 📊 Memory Statistics and Monitoring

### Memory Stats Interface

```typescript
interface MemoryStats {
  totalUsers: number;
  totalMessages: number;
  totalSlots: number;
  averageMessagesPerUser: number;
  averageSlotsPerUser: number;
}
```

### Monitoring and Cleanup

```typescript
const memoryManager = new MemoryManager();

// Get overall statistics
const stats = memoryManager.getMemoryStats();
console.log('Total users:', stats.totalUsers);
console.log('Average messages per user:', stats.averageMessagesPerUser);

// Find active users
const activeUsers = memoryManager.getUsersWithActiveMemory(5);

// Cleanup inactive memories
const cleanedCount = memoryManager.cleanupInactiveMemories(24 * 60 * 60 * 1000); // 24 hours
```

## 🚀 Advanced Features

### Collaborative Intent Servers

```typescript
class ComplexIntentServer extends BaseIntentServer {
  constructor() {
    super(ChatIntentName.COMPLEX_ACTION);
    this.collabServers = [ChatIntentName.JOIN_ROOM, ChatIntentName.SEND_MESSAGE];
  }

  runTools(input: IIntentServerInput): any {
    // Coordinate with other intent servers
    const collabSchemas = this.collabGptToolSchemas();
    // ... complex logic
  }
}
```

### Custom Slot Validation

```typescript
protected validateSlotValue(slotName: ChatSlotName, value: any): boolean {
  switch (slotName) {
    case ChatSlotName.USERNAME:
      return typeof value === 'string' && value.length >= 3;
    case ChatSlotName.ROOM_NAME:
      return typeof value === 'string' && /^[a-zA-Z0-9_-]+$/.test(value);
    default:
      return true;
  }
}
```

### Error Handling

```typescript
protected createErrorResponse(message: string, code: string = 'VALIDATION_ERROR'): any {
  return {
    success: false,
    error: {
      code,
      message,
      timestamp: new Date().toISOString(),
      details: { intent: this.myIntent }
    }
  };
}
```

## 🔧 Configuration and Customization

### Intent Configuration

```typescript
// Define intent requirements
const INTENT_CONFIG = {
  [ChatIntentName.JOIN_ROOM]: {
    requiredSlots: [ChatSlotName.USERNAME, ChatSlotName.ROOM_NAME],
    optionalSlots: [ChatSlotName.ROOM_PASSWORD],
    description: 'Join a specific chat room'
  },
  [ChatIntentName.SEND_MESSAGE]: {
    requiredSlots: [ChatSlotName.MESSAGE_CONTENT],
    optionalSlots: [ChatSlotName.ROOM_NAME, ChatSlotName.USERNAME],
    description: 'Send a message to a chat room'
  }
};
```

### Memory Configuration

```typescript
// Configure memory limits
const MEMORY_CONFIG = {
  maxMessagesPerUser: 1000,
  maxSlotsPerUser: 100,
  cleanupInterval: 24 * 60 * 60 * 1000, // 24 hours
  archiveThreshold: 10000
};
```

## 📝 Best Practices

1. **Memory Management**:
   - Regularly cleanup inactive memories
   - Monitor memory usage statistics
   - Implement memory size limits

2. **Intent Servers**:
   - Always validate slot values
   - Provide clear error messages
   - Handle missing slots gracefully

3. **Slot Management**:
   - Use type-safe slot names
   - Validate slot values before processing
   - Clear irrelevant slots when appropriate

4. **Error Handling**:
   - Provide meaningful error codes
   - Include context in error messages
   - Log errors for debugging

5. **Performance**:
   - Use efficient data structures (Map, Set)
   - Implement lazy loading for large memories
   - Cache frequently accessed data

## 🔮 Future Enhancements

- [ ] **Persistence**: Database storage for memories
- [ ] **Compression**: Memory compression for long conversations
- [ ] **Analytics**: Advanced conversation analytics
- [ ] **Machine Learning**: Intent prediction and slot filling
- [ ] **Multi-language**: Internationalization support
- [ ] **Real-time Sync**: WebSocket-based memory synchronization
- [ ] **Backup/Restore**: Memory backup and restoration
- [ ] **Versioning**: Memory version control and rollback 