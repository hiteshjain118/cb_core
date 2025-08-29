# CoralBricks Common Package

This package contains common types and utilities used across CoralBricks projects.

## Features

- **ToolCallResult**: Comprehensive tool call result handling with BigInt support
- **Common interfaces**: Shared types for tool calls and descriptions
- **Type safety**: Full TypeScript support with proper type definitions

## Installation

```bash
npm install
```

## Development

```bash
# Build the package
npm run build

# Watch mode for development
npm run dev

# Clean build artifacts
npm run clean
```

## Testing

This package uses Jest for testing with TypeScript support.

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Test Coverage

The test suite covers:
- ✅ Constructor and factory methods
- ✅ Success and error result handling
- ✅ BigInt serialization (JSON compatibility)
- ✅ Dictionary conversions
- ✅ Logging methods
- ✅ Edge cases and error handling
- ✅ Interface compliance

### Test Structure

```
src/types/__tests__/
└── tool-call-result.test.ts  # Comprehensive ToolCallResult tests
```

## Key Classes

### ToolCallResult

The main class for handling tool call results with the following features:

- **Status handling**: Success, error, and scheduled states
- **BigInt support**: Proper JSON serialization of BigInt values
- **Factory methods**: Convenient static methods for common use cases
- **Logging**: Built-in methods for structured logging
- **Type safety**: Full TypeScript support

#### Example Usage

```typescript
import { ToolCallResult } from 'coralbricks-common';

// Create a success result
const successResult = ToolCallResult.success(
  'my_tool',
  { data: 'result' },
  'call-123',
  BigInt(456)
);

// Create an error result
const errorResult = ToolCallResult.error(
  'my_tool',
  'call-123',
  BigInt(456),
  'ValidationError',
  'Invalid input'
);

// Serialize to JSON (handles BigInt automatically)
const json = successResult.to_json();

// Get structured log message
const logMessage = successResult.toLogMessage();
```

## BigInt Handling

This package properly handles BigInt values in JSON serialization:

- **Automatic conversion**: BigInt values are converted to strings in JSON
- **Nested support**: Works with complex nested objects containing BigInt
- **Performance**: Efficient serialization without data loss

## Contributing

1. Write tests for new functionality
2. Ensure all tests pass: `npm test`
3. Maintain type safety
4. Update documentation as needed

## License

MIT 