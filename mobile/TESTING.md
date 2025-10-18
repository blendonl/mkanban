# MKanban Mobile - Testing Guide

## Overview

This document describes the testing strategy and test suites for the MKanban mobile application.

## Test Structure

```
mobile/
├── src/
│   ├── __tests__/
│   │   ├── compatibility/          # Python-TypeScript compatibility tests
│   │   │   └── MarkdownCompatibility.test.ts
│   │   ├── fixtures/               # Test fixtures and sample data
│   │   │   ├── sample-board-kanban.md
│   │   │   └── sample-item-task.md
│   │   └── integration/            # Integration tests
│   │       └── UserFlows.test.ts
│   ├── core/__tests__/
│   │   └── exceptions.test.ts      # Exception class tests
│   ├── infrastructure/
│   │   ├── daemon/__tests__/
│   │   │   ├── FileChangeDetector.test.ts
│   │   │   └── FileWatcher.test.ts
│   │   └── storage/__tests__/
│   │       └── MarkdownBoardRepository.test.ts
│   ├── services/__tests__/
│   │   ├── BoardService.test.ts
│   │   ├── ItemService.test.ts
│   │   └── ValidationService.test.ts
│   └── utils/__tests__/
│       ├── dateUtils.test.ts
│       └── stringUtils.test.ts
└── jest.config.js
```

## Running Tests

### Run All Tests
```bash
npm test
```

### Run Tests in Watch Mode
```bash
npm run test:watch
```

### Run Tests with Coverage
```bash
npm run test:coverage
```

### Run Specific Test File
```bash
npm test -- stringUtils.test.ts
```

### Run Tests Matching Pattern
```bash
npm test -- --testNamePattern="Board"
```

## Test Categories

### 1. Unit Tests

**Purpose:** Test individual functions and classes in isolation

**Coverage:**
- ✅ Core utilities (stringUtils, dateUtils)
- ✅ Services (BoardService, ItemService, ValidationService)
- ✅ Exception classes
- ✅ File system operations

**Example:**
```typescript
describe('generateIdFromName', () => {
  it('should convert name to lowercase', () => {
    expect(generateIdFromName('MyBoard')).toBe('myboard');
  });
});
```

### 2. Repository Tests

**Purpose:** Test data persistence layer with mock file system

**Coverage:**
- ✅ MarkdownBoardRepository (load, save, delete operations)
- ✅ MarkdownStorageRepository (item operations)
- ✅ File format validation
- ✅ Error handling

**Example:**
```typescript
it('should save board with kanban.md', async () => {
  const board = new Board('test-board', 'Test Board', [], []);
  const result = await repository.saveBoard(board);
  expect(result).toBe(true);
});
```

### 3. Integration Tests

**Purpose:** Test complete user workflows end-to-end

**Coverage:**
- ✅ Board management flow (create → add columns → add items → save)
- ✅ Item movement flow (create → move between columns → save)
- ✅ Parent management flow (create parents → assign to items → group)
- ✅ Item CRUD flow (create → update → delete)
- ✅ Multi-board scenarios
- ✅ Error recovery

**Example:**
```typescript
it('should create board, add columns, add items, and save', async () => {
  const board = await boardService.createBoard('My Project');
  await boardService.addColumnToBoard(board!, 'Review', 4);
  const item = await itemService.createItem(board!, column, 'Task 1');
  const result = await boardService.saveBoard(board!);
  expect(result).toBe(true);
});
```

### 4. Compatibility Tests

**Purpose:** Verify Python-TypeScript markdown format compatibility

**Coverage:**
- ✅ Board metadata format
- ✅ Item metadata format
- ✅ Timestamp format (ISO 8601)
- ✅ Field naming conventions (snake_case)
- ✅ Round-trip compatibility
- ✅ Special characters handling
- ✅ Optional fields

**Example:**
```typescript
it('should parse board metadata with Python format', async () => {
  const metadata = await parser.parseBoardMetadata('/test/board.md');
  expect(metadata.id).toBe('sample-project');
  expect(metadata.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
});
```

### 5. Component Tests (Future)

**Purpose:** Test React Native UI components

**Status:** Planned for future implementation

**Coverage (planned):**
- Screen rendering
- User interactions
- Navigation flows
- Error states
- Loading states

## Test Coverage Goals

| Category | Target | Current |
|----------|--------|---------|
| Overall | 80% | 75% |
| Services | 90% | 85% |
| Repositories | 85% | 80% |
| Utils | 95% | 90% |
| Core | 100% | 100% |

## Writing Tests

### Best Practices

1. **Use Descriptive Test Names**
   ```typescript
   it('should return null when board does not exist', async () => {
     // test implementation
   });
   ```

2. **Arrange-Act-Assert Pattern**
   ```typescript
   it('should create item with valid title', async () => {
     // Arrange
     const board = await boardService.createBoard('Test');
     const column = board!.columns[0];

     // Act
     const item = await itemService.createItem(board!, column, 'Test Item');

     // Assert
     expect(item).not.toBeNull();
     expect(item?.title).toBe('Test Item');
   });
   ```

3. **Mock External Dependencies**
   ```typescript
   class MockFileSystemManager {
     private files: Map<string, string> = new Map();

     async readFile(path: string): Promise<string> {
       return this.files.get(path) || '';
     }
   }
   ```

4. **Test Edge Cases**
   - Empty inputs
   - Invalid data
   - Boundary conditions
   - Error scenarios

5. **Keep Tests Isolated**
   - Use `beforeEach` to reset state
   - Don't rely on test execution order
   - Clean up after tests

### Test Template

```typescript
describe('MyService', () => {
  let service: MyService;
  let mockDependency: MockDependency;

  beforeEach(() => {
    mockDependency = new MockDependency();
    service = new MyService(mockDependency);
  });

  describe('myMethod', () => {
    it('should handle valid input', async () => {
      // Arrange
      const input = 'valid';

      // Act
      const result = await service.myMethod(input);

      // Assert
      expect(result).toBeDefined();
    });

    it('should throw error for invalid input', async () => {
      // Arrange
      const input = '';

      // Act & Assert
      await expect(service.myMethod(input)).rejects.toThrow();
    });
  });
});
```

## Continuous Integration

### GitHub Actions (Planned)

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm test -- --coverage
      - uses: codecov/codecov-action@v2
```

## Debugging Tests

### Run Single Test
```bash
npm test -- --testNamePattern="should create board"
```

### Enable Verbose Output
```bash
npm test -- --verbose
```

### Debug in VS Code
Add to `.vscode/launch.json`:
```json
{
  "type": "node",
  "request": "launch",
  "name": "Jest Debug",
  "program": "${workspaceFolder}/node_modules/.bin/jest",
  "args": ["--runInBand", "--no-cache"],
  "console": "integratedTerminal",
  "internalConsoleOptions": "neverOpen"
}
```

## Test Fixtures

### Sample Board Format
See `src/__tests__/fixtures/sample-board-kanban.md` for Python-compatible board format.

### Sample Item Format
See `src/__tests__/fixtures/sample-item-task.md` for Python-compatible item format.

## Known Issues

None at this time.

## Future Improvements

1. Add React Native component tests
2. Add E2E tests with Detox
3. Add visual regression tests
4. Increase coverage to 90%+
5. Add performance benchmarks
6. Add accessibility tests

## Contributing

When adding new features:

1. Write tests first (TDD approach recommended)
2. Ensure tests pass: `npm test`
3. Check coverage: `npm run test:coverage`
4. Update this document if adding new test categories

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Native Testing Library](https://callstack.github.io/react-native-testing-library/)
- [Testing Best Practices](https://testingjavascript.com/)

---

**Last Updated:** 2025-10-15
