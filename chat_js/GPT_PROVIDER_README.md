# GPT Provider Integration

This document explains how to use the newly added GPT provider functionality in the chat_js project.

## Overview

The following components have been ported from Python to TypeScript:

1. **Token Utility** (`src/token-util.ts`) - Token counting functionality for LLM models
2. **LLM Monitor** (`src/llm-monitor.ts`) - Usage tracking and statistics for LLM calls
3. **GPT Provider** (`src/gpt-provider.ts`) - OpenAI GPT model provider implementation
4. **Model Provider Interface** (`src/model-provider.ts`) - TypeScript interface for model providers

## Installation

✅ **COMPLETED**: The OpenAI package has been installed and integrated!

The following setup is already done:
- OpenAI package installed via `npm install openai`
- OpenAI imports enabled in `src/gpt-provider.ts`
- Async support added to the model interface
- Error handling and TypeScript compatibility implemented

## Usage

### Basic Usage with QBServer

```typescript
import { QBServer } from './src/qb-server';

// Method 1: Using static factory method
const qbServer = QBServer.withGPTProvider('your-openai-api-key', 'gpt-4o');

// Method 2: Creating provider manually
import { GPTProvider } from './src/gpt-provider';
const gptProvider = new GPTProvider('your-openai-api-key', 'gpt-4o');
const qbServer = new QBServer(gptProvider);

// Method 3: Using mock provider for testing
const mockQBServer = QBServer.withMockProvider();
```

### Using in JavaScript (Node.js)

```javascript
const { QBServer } = require('./dist/qb-server'); // After TypeScript compilation

// Use with environment variable
const qbServer = QBServer.withGPTProvider(process.env.OPENAI_API_KEY, 'gpt-4o');

// Or use mock for development
const qbServer = QBServer.withMockProvider();
```

### Token Counting

```typescript
import { countTokens, logTokenCount } from './src/token-util';

const text = "Hello, world!";
const tokenCount = countTokens(text, "gpt-4o");
console.log(`Token count: ${tokenCount}`);

// With logging
logTokenCount(text, "sample text");
```

### LLM Monitoring

```typescript
import { LLMMonitor } from './src/llm-monitor';
import { ChatIntentName } from './src/types/enums';

const monitor = new LLMMonitor("gpt-4o", "MyApp");

// Record an LLM call
monitor.recordLlmCall(
  [{ role: 'user', content: 'Hello' }],
  ChatIntentName.QB,
  'Hello! How can I help you?',
  [], // tool calls
  '' // tools in prompt
);

// Get usage statistics
const stats = monitor.getUsageStatistics();
console.log(stats);

// Print summary
monitor.printUsageSummary();
```

## Configuration

### Environment Variables

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY=your_api_key_here
```

### Model Selection

The GPT provider supports different OpenAI models:

- `gpt-4o` (default)
- `gpt-4o-mini`
- `gpt-3.5-turbo`

## Cost Monitoring

The LLM Monitor tracks estimated costs for different models:

- **gpt-4o**: $5/1M input tokens, $20/1M output tokens
- **gpt-4o-mini**: $0.6/1M input tokens, $2.4/1M output tokens
- **DeepSeek models**: Various pricing tiers

## Development Mode

For development and testing, use the mock provider:

```typescript
const qbServer = QBServer.withMockProvider();
```

This returns mock responses without making actual API calls.

## Error Handling

The GPT provider includes comprehensive error handling:

- Network failures
- API rate limits
- Invalid API keys
- Malformed responses

Errors are logged and gracefully handled by returning error responses.

## Testing

To test the GPT provider:

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your_api_key_here

# Compile TypeScript
npx tsc

# Run the test
node dist/examples/test-gpt-provider.js
```

## Next Steps

1. ✅ ~~Install the `openai` package~~ **DONE**
2. ✅ ~~Uncomment OpenAI imports in `gpt-provider.ts`~~ **DONE**
3. ✅ ~~Replace mock API calls with actual OpenAI client usage~~ **DONE**
4. **Add your OpenAI API key to environment variables**
5. **Update the server.js to use `QBServer.withGPTProvider()`**

## Examples

See the `src/examples/` directory for complete usage examples:

- `gpt-qb-server-demo.ts` - TypeScript usage example
- `qb-server-usage.js` - JavaScript/Node.js usage example 