# Unit Tests for Types

This directory contains comprehensive unit tests for the type definitions and classes in the `types` directory.

## Test Coverage

### modelio.test.ts
Comprehensive tests for the ModelIO and ModelOutputParser classes:

- **ModelIO class**:
  - Constructor initialization
  - Output parser creation
  - Dependency injection verification

- **ModelOutputParser class**:
  - Constructor and initialization
  - JSON header/footer removal functionality
  - Message setting and processing
  - Error handling
  - Tool call result processing
  - Retry logic implementation

**Coverage**: 97.36% statement coverage, 91.66% branch coverage, 100% function coverage

### gpt-provider.test.ts
Comprehensive tests for the GPTProvider class:

- **GPTProvider class**:
  - Constructor initialization with different models
  - OpenAI client configuration
  - LLM Monitor integration
  - Model name retrieval
  - API response handling
  - Error handling (API errors, empty responses, null responses)
  - Tool call processing
  - Debug logging verification
  - Integration with ModelOutputParser

**Coverage**: 100% statement coverage, 100% branch coverage, 100% function coverage

### tool-call-runner.test.ts
Comprehensive tests for the ToolCallRunner class:

- **ToolCallRunner class**:
  - Constructor initialization with thread/user IDs and environment configuration
  - Multiple tool execution in parallel via `run_tools`
  - Individual tool execution via `run_tool`
  - Python function runner tool execution (mock implementation)
  - QuickBooks tools execution via internal API calls
  - Tool caching and retrieval (`get_enabled_tools`, `get_enabled_tool_descriptions`)
  - Error handling for unknown tools, API failures, malformed inputs
  - Axios HTTP client integration for internal API communication
  - Logging for successful and failed tool executions
  - Integration tests with mixed tool types

**Coverage**: Comprehensive coverage of all public methods and error scenarios

## Test Structure

### Helper Functions
- `test-helpers.ts` - Utility functions for creating mock objects:
  - `createMockToolCallResult()` - Creates mock ToolCallResult instances
  - `createMockChatMessage()` - Creates mock ChatCompletionMessage instances

### Test Categories
1. **Unit Tests** - Test individual methods and behaviors
2. **Integration Tests** - Test end-to-end functionality
3. **Edge Cases** - Test boundary conditions and error scenarios

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## Test Results Summary

- **66 test cases** all passing (23 for modelio.ts + 16 for gpt-provider.ts + 27 for tool-call-runner.ts)
- **100% code coverage** for gpt-provider.ts
- **97.36% code coverage** for modelio.ts  
- **Comprehensive coverage** for tool-call-runner.ts
- **Comprehensive error handling** testing
- **Mocking strategy** for external dependencies including OpenAI API and Axios HTTP client

## Key Test Features

1. **Dependency Mocking**: ToolCallRunner and external dependencies are mocked
2. **Edge Case Coverage**: Tests empty strings, null values, and error conditions
3. **Type Safety**: Full TypeScript support with proper type checking
4. **Helper Functions**: Reusable mock creators for consistent test data
5. **Integration Testing**: End-to-end workflow verification

## Uncovered Areas

The following lines are not covered by tests (edge cases that are difficult to trigger):
- Line 101: Error condition in get_output (tool call length negative)
- Lines 120-127: Specific error handling paths in get_output_with_should_retry

These represent edge cases that would require forcing invalid internal state to test. 