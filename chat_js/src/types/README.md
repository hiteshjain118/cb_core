# Chat Types System

This directory contains the TypeScript type definitions and implementations for the chat system, inspired by the Python structs pattern from `builder_package.core.structs`.

## Structure

```
src/types/
├── enums.ts          # Enum definitions for chat system
├── structs.ts        # Interface definitions (similar to Python dataclasses)
├── implementations.ts # Concrete class implementations
├── index.ts          # Main export file
└── examples/         # Usage examples
    └── usage.ts      # Comprehensive usage examples
```

## Design Philosophy

The types system follows these principles:

1. **Interface-First**: Define contracts with interfaces, implement with classes
2. **Type Safety**: Full TypeScript support with strict typing
3. **Method Implementation**: Classes implement interface methods (similar to Python dataclasses)
4. **Enum-Based**: Use enums for constants and type-safe values
5. **Comprehensive Coverage**: Cover all aspects of a chat system

## Key Components

### Enums (`enums.ts`)

- **`ChatIntentName`**: Defines all possible chat intents (join_room, send_message, etc.)
- **`ChatSlotName`**: Defines all possible data slots (username, room_name, etc.)
- **`MessageRole`**: User roles in messages (user, system, bot, admin)
- **`UserStatus`**: User online status (online, offline, away, busy)
- **`UserRole`**: User permission levels (user, moderator, admin, owner)
- **`RoomType`**: Room types (public, private, direct, group)
- **`MessageType`**: Message content types (text, image, file, etc.)

### Interfaces (`structs.ts`)

- **`IChatSlot`**: Data slot definition with name, type, and description
- **`IChatIntent`**: Intent definition with required/optional slots
- **`IChatMessage`**: Message structure with role, content, and metadata
- **`IUser`**: User entity with permissions and status
- **`IRoom`**: Room entity with members and settings
- **`IConnection`**: WebSocket connection tracking
- **`IMessageHistory`**: Message storage and retrieval
- **`IChatSession`**: User session tracking

### Implementations (`implementations.ts`)

Concrete classes that implement the interfaces:

- **`ChatSlot`**: Slot implementation with `isReferredBy()` method
- **`ChatIntent`**: Intent implementation with slot management
- **`ChatMessage`**: Message with slot operations and ID generation
- **`User`**: User with permission checking and room management
- **`Room`**: Room with member management and role hierarchy
- **`Connection`**: Connection with activity tracking and user management
- **`MessageHistory`**: History with search and archival features
- **`ChatSession`**: Session with timing and message counting

## Usage Examples

### Basic Usage

```typescript
import { User, UserStatus, UserRole, Room, RoomType } from '../types';

// Create a user
const alice = new User('user_123', 'alice', UserStatus.ONLINE, UserRole.USER);

// Create a room
const generalRoom = new Room('room_456', 'General', RoomType.PUBLIC, 'user_123', 'user_123');

// Check permissions
console.log('Can send messages:', alice.hasPermission('send_messages'));
console.log('Is in room:', alice.isInRoom('room_456'));
```

### Intent and Slot Management

```typescript
import { ChatIntent, ChatSlot, ChatSlotName, ChatIntentName } from '../types';

// Create a slot
const usernameSlot = new ChatSlot('username', 'string', 'User identifier');

// Create an intent
const joinIntent = new ChatIntent(
  'join_room',
  'Join a chat room',
  [ChatSlotName.USERNAME, ChatSlotName.ROOM_NAME],
  [ChatSlotName.CLIENT_ID, ChatSlotName.TIMESTAMP]
);

// Check references
console.log('Intent matches:', joinIntent.isReferredBy('join'));
console.log('Slot matches:', usernameSlot.isReferredBy('username'));
```

### Message Handling

```typescript
import { ChatMessage, MessageRole, ChatIntentName, ChatSlotName } from '../types';

// Create a message
const message = new ChatMessage(
  MessageRole.USER,
  'Hello, world!',
  ChatIntentName.SEND_MESSAGE,
  Date.now()
);

// Add slots
message.addSlot(ChatSlotName.ROOM_NAME, 'General');
message.addSlot(ChatSlotName.USERNAME, 'alice');

// Check slots
console.log('Has room slot:', message.hasSlot(ChatSlotName.ROOM_NAME));
console.log('Room value:', message.getSlot(ChatSlotName.ROOM_NAME));
```

## Type Safety Features

### Strict Typing

- All enums provide type-safe constants
- Interfaces ensure method contracts
- Generic types for flexible data structures
- Union types for optional properties

### Method Implementation

- Classes implement all interface methods
- Type-safe method signatures
- Consistent error handling
- Immutable data where appropriate

### Validation

- Runtime type checking
- Required vs optional properties
- Enum value validation
- Slot existence checking

## Building and Development

### TypeScript Compilation

```bash
# Build the project
npm run build

# Watch mode for development
npm run build:watch

# Type checking only
npm run type-check
```

### Development Workflow

1. **Define interfaces** in `structs.ts`
2. **Implement classes** in `implementations.ts`
3. **Add enums** in `enums.ts` as needed
4. **Update examples** in `examples/usage.ts`
5. **Build and test** with TypeScript compiler

## Extending the System

### Adding New Types

1. **Add enum values** to appropriate enum files
2. **Define interface** in `structs.ts`
3. **Implement class** in `implementations.ts`
4. **Export** from `index.ts`
5. **Add examples** to usage files

### Adding New Methods

1. **Update interface** in `structs.ts`
2. **Implement method** in class
3. **Add tests** or examples
4. **Update documentation**

## Comparison with Python Structs

| Python Feature | TypeScript Equivalent |
|----------------|----------------------|
| `@dataclass` | `interface` + `class` |
| `field()` | Optional properties |
| `is_refered_by()` | `isReferredBy()` method |
| Enum values | TypeScript enums |
| Type hints | TypeScript types |
| Method definitions | Interface methods |

## Best Practices

1. **Use interfaces** for contracts, classes for implementation
2. **Leverage enums** for type-safe constants
3. **Implement all methods** defined in interfaces
4. **Use strict typing** for better error catching
5. **Provide examples** for complex usage patterns
6. **Maintain consistency** across similar types
7. **Document complex methods** with JSDoc comments

## Future Enhancements

- [ ] Add validation decorators
- [ ] Implement serialization methods
- [ ] Add database persistence types
- [ ] Create API response types
- [ ] Add WebSocket message types
- [ ] Implement caching interfaces
- [ ] Add event system types 