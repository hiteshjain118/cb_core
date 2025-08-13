# ModelHTTPRetriever Unit Tests

This directory contains comprehensive unit tests for the `ModelHTTPRetriever` class and its tool call functionality.

## Test Coverage

The tests cover the following functionality:

### Core Methods
- **Initialization**: Constructor with endpoint and parameters
- **Endpoint handling**: Automatic forward slash addition
- **Parameter management**: Correct parameter retrieval
- **Cache key generation**: Unique cache key creation
- **API summary**: Method description generation

### Tool Call Interface
- **`tool_name()`**: Returns correct tool identifier
- **`extract_result_summary()`**: Processes API responses correctly
- **`call_tool()`**: Main tool execution method

### Success Scenarios
- Successful data retrieval
- Proper response parsing
- Result summary generation
- Cache key creation

### Error Handling
- HTTP errors (400, 500, etc.)
- No data found scenarios
- General exceptions
- Unauthorized connections
- Malformed responses

### Edge Cases
- Empty response lists
- Missing QueryResponse data
- Invalid response types
- Connection authorization failures

## Running the Tests

### Option 1: Run all tests
```bash
cd builder/builder_package/core/tests
python3 run_tests.py
```

### Option 2: Run specific test file
```bash
cd builder/builder_package/core/tests
python3 -m unittest test_model_http_retriever.py -v
```

### Option 3: Run specific test method
```bash
cd builder/builder_package/core/tests
python3 -m unittest test_model_http_retriever.TestModelHTTPRetriever.test_call_tool_success -v
```

## Test Dependencies

The tests use the following mocking and testing libraries:
- `unittest` (Python standard library)
- `unittest.mock` for mocking external dependencies
- Custom mock classes for `IHTTPConnection` and `CBUser`

## Mock Classes

### MockHTTPConnection
- Simulates HTTP connection behavior
- Configurable authorization status
- Mock access token management
- Mock CB ID handling

### MockCBUser
- Simulates CB user behavior
- Configurable base URL
- Used for testing URL construction

## Test Structure

Each test method follows the Arrange-Act-Assert pattern:
1. **Arrange**: Set up test data and mocks
2. **Act**: Execute the method under test
3. **Assert**: Verify the expected behavior

## Adding New Tests

When adding new tests:
1. Follow the existing naming convention (`test_method_name_scenario`)
2. Use descriptive test names that explain the scenario
3. Mock external dependencies appropriately
4. Test both success and failure cases
5. Include edge case testing

## Example Test Pattern

```python
def test_method_name_scenario(self):
    """Test description"""
    # Arrange
    mock_data = {...}
    
    # Act
    with patch.object(self.retriever, 'method', return_value=mock_data):
        result = self.retriever.method_under_test()
    
    # Assert
    self.assertEqual(result.expected_property, expected_value)
``` 