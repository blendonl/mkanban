// Manual test to verify exceptions work correctly
// Run with: node mobile/src/core/__tests__/manual-exception-test.js

const {
  MKanbanError,
  ValidationError,
  ItemNotFoundError,
  ColumnNotFoundError,
  BoardNotFoundError,
} = require('../exceptions.ts');

console.log('Testing exception classes...\n');

// Test MKanbanError
try {
  throw new MKanbanError('Base error test');
} catch (error) {
  console.log('✓ MKanbanError:', error.name, '-', error.message);
  console.log('  Is Error:', error instanceof Error);
  console.log('  Is MKanbanError:', error instanceof MKanbanError);
}

// Test ValidationError
try {
  throw new ValidationError('Invalid board name');
} catch (error) {
  console.log('\n✓ ValidationError:', error.name, '-', error.message);
  console.log('  Is MKanbanError:', error instanceof MKanbanError);
  console.log('  Is ValidationError:', error instanceof ValidationError);
}

// Test ItemNotFoundError
try {
  throw new ItemNotFoundError('Item ABC-123 not found');
} catch (error) {
  console.log('\n✓ ItemNotFoundError:', error.name, '-', error.message);
  console.log('  Is MKanbanError:', error instanceof MKanbanError);
}

// Test ColumnNotFoundError
try {
  throw new ColumnNotFoundError('Column "done" not found');
} catch (error) {
  console.log('\n✓ ColumnNotFoundError:', error.name, '-', error.message);
  console.log('  Is MKanbanError:', error instanceof MKanbanError);
}

// Test BoardNotFoundError
try {
  throw new BoardNotFoundError('Board "my-project" not found');
} catch (error) {
  console.log('\n✓ BoardNotFoundError:', error.name, '-', error.message);
  console.log('  Is MKanbanError:', error instanceof MKanbanError);
}

console.log('\n✅ All exception classes working correctly!');
