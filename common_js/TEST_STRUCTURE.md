# Test Directory Structure

## Overview

The test directory structure now mirrors the source directory structure for better organization and maintainability.

## Directory Layout

```
common_js/
├── src/                    # Source code
│   ├── types/             # Type definitions
│   │   ├── tool-call-result.ts
│   │   └── index.ts
│   └── index.ts
├── tests/                  # Test files (mirrors src structure)
│   └── types/             # Tests for types
│       ├── tool-call-result.test.ts
│       └── index.ts
├── jest.config.js          # Jest configuration
├── jest.setup.js           # Jest setup file
└── package.json            # Package configuration
```

## Key Benefits

✅ **Mirrored Structure**: Tests follow the same organization as source code
✅ **Easy Navigation**: Find tests by following the same path structure
✅ **Maintainable**: Adding new source files means adding tests in the same relative location
✅ **Clear Separation**: Source and test code are completely separated

## Import Paths

### From tests/types/ to src/types/
```typescript
// In tests/types/tool-call-result.test.ts
import { ToolCallResult } from '../../src/types/tool-call-result';
```

### Adding New Tests

When adding a new source file at `src/new-feature/new-class.ts`:
1. Create the test directory: `tests/new-feature/`
2. Create the test file: `tests/new-feature/new-class.test.ts`
3. Use import path: `../../src/new-feature/new-class`

## Jest Configuration

- **Roots**: Both `src/` and `tests/` directories are included
- **Coverage**: Only source files are included in coverage reports
- **Setup**: `jest.setup.js` runs before each test file
- **Transform**: TypeScript files are properly transformed

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## Coverage Structure

Coverage reports will show:
- Source files in `src/` directory
- Test files are excluded from coverage
- Clear mapping between tests and source files

## Best Practices

1. **Keep Structure Mirrored**: Always maintain the parallel structure
2. **Consistent Naming**: Use `.test.ts` suffix for test files
3. **Relative Imports**: Use relative paths from test to source
4. **Index Files**: Create index files in test directories to match source structure 