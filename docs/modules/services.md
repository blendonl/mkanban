# Services Layer

The services layer contains the core business logic of MKanban, orchestrating operations between repositories, handling validation, and providing context-aware logging.

## Overview

The services layer includes:

- **BoardService**: Board-level operations (create, load, save, delete)
- **ItemService**: Item management (CRUD operations, parent/child relationships)
- **ValidationService**: Data validation and business rule enforcement

All services are managed by the dependency injection container and include context-aware logging.

## BoardService

The `BoardService` handles all board-level operations with comprehensive logging and validation.

### Constructor

```python
class BoardService:
    def __init__(
        self,
        board_repository: BoardRepository,
        validation_service: ValidationService,
        logger: ContextAwareLogger
    ):
        self._board_repository = board_repository
        self._validation_service = validation_service
        self._logger = logger
```

### Core Operations

#### Board Creation

```python
def create_board(
    self,
    name: str,
    columns: Optional[List[str]] = None,
    base_path: Optional[Path] = None
) -> Board:
    """Create a new board with the specified name and columns."""
```

**Usage:**
```python
board_service = get_board_service()

# Create board with default columns
board = board_service.create_board("my-project")

# Create board with custom columns
board = board_service.create_board(
    "development",
    columns=["backlog", "todo", "in-progress", "review", "done"]
)
```

**Logging:**
```
[2024-01-01T10:00:00] DAEMON INFO board_service: Creating new board [board=my-project]
[2024-01-01T10:00:00] DAEMON DEBUG board_service: Board created successfully [board=my-project, columns=3, path=/data/boards/my-project]
```

#### Board Loading

```python
def load_board(self, name: str, base_path: Optional[Path] = None) -> Optional[Board]:
    """Load an existing board by name."""

def load_all_boards(self, base_path: Optional[Path] = None) -> List[Board]:
    """Load all available boards."""

def board_exists(self, name: str, base_path: Optional[Path] = None) -> bool:
    """Check if a board exists."""
```

**Usage:**
```python
# Load specific board
board = board_service.load_board("my-project")
if board:
    print(f"Loaded board: {board.name}")

# Load all boards
boards = board_service.load_all_boards()
for board in boards:
    print(f"Available: {board.name}")

# Check existence
if board_service.board_exists("my-project"):
    print("Board exists")
```

#### Board Persistence

```python
def save_board(self, board: Board, base_path: Optional[Path] = None) -> bool:
    """Save a board to storage."""

def delete_board(self, name: str, base_path: Optional[Path] = None) -> bool:
    """Delete a board and all its contents."""
```

**Usage:**
```python
# Save board
success = board_service.save_board(board)
if success:
    print("Board saved successfully")

# Delete board
if board_service.delete_board("old-project"):
    print("Board deleted")
```

#### Column Management

```python
def add_column(self, board: Board, column_name: str, position: Optional[int] = None) -> bool:
    """Add a new column to the board."""

def remove_column(self, board: Board, column_name: str) -> bool:
    """Remove a column from the board."""

def rename_column(self, board: Board, old_name: str, new_name: str) -> bool:
    """Rename a column in the board."""
```

**Usage:**
```python
# Add column at end
board_service.add_column(board, "testing")

# Add column at specific position
board_service.add_column(board, "review", position=2)

# Remove column
board_service.remove_column(board, "old-column")

# Rename column
board_service.rename_column(board, "todo", "backlog")
```

## ItemService

The `ItemService` manages individual items and their relationships within boards.

### Constructor

```python
class ItemService:
    def __init__(
        self,
        storage_repository: StorageRepository,
        validation_service: ValidationService,
        logger: ContextAwareLogger
    ):
        self._storage_repository = storage_repository
        self._validation_service = validation_service
        self._logger = logger
```

### Core Operations

#### Item Creation

```python
def create_item(
    self,
    board: Board,
    column: Column,
    title: str,
    content: str = "",
    parent_id: Optional[str] = None
) -> Optional[Item]:
    """Create a new item in the specified column."""
```

**Usage:**
```python
item_service = get_item_service()

# Create simple item
item = item_service.create_item(
    board=board,
    column=todo_column,
    title="Fix authentication bug",
    content="The login form is not validating credentials properly"
)

# Create child item
child_item = item_service.create_item(
    board=board,
    column=todo_column,
    title="Update login tests",
    parent_id=parent_item.id
)
```

**Logging:**
```
[2024-01-01T10:00:00] DAEMON INFO item_service: Creating new item [board=my-project, column=todo, item=Fix authentication bug]
[2024-01-01T10:00:00] DAEMON DEBUG item_service: Item created successfully [board=my-project, column=todo, item=Fix authentication bug, id=abc123, parent=None]
```

#### Item Retrieval

```python
def get_item(self, board: Board, item_id: str) -> Optional[Item]:
    """Get a specific item by ID."""

def get_items_in_column(self, board: Board, column: Column) -> List[Item]:
    """Get all items in a specific column."""

def get_child_items(self, board: Board, parent_item: Item) -> List[Item]:
    """Get all child items of a parent item."""
```

**Usage:**
```python
# Get specific item
item = item_service.get_item(board, "abc123")

# Get all items in column
items = item_service.get_items_in_column(board, todo_column)

# Get child items
children = item_service.get_child_items(board, parent_item)
```

#### Item Updates

```python
def update_item(
    self,
    board: Board,
    item: Item,
    title: Optional[str] = None,
    content: Optional[str] = None,
    status: Optional[str] = None
) -> bool:
    """Update an existing item."""

def move_item(
    self,
    board: Board,
    item: Item,
    target_column: Column,
    target_position: Optional[int] = None
) -> bool:
    """Move an item to a different column."""
```

**Usage:**
```python
# Update item content
item_service.update_item(
    board=board,
    item=item,
    title="Fix critical authentication bug",
    content="Updated description with more details"
)

# Move item to different column
item_service.move_item(
    board=board,
    item=item,
    target_column=in_progress_column
)
```

#### Item Deletion

```python
def delete_item(self, board: Board, item: Item) -> bool:
    """Delete an item and all its children."""

def delete_item_from_column(self, board: Board, item: Item, column: Column) -> bool:
    """Delete an item from a specific column."""
```

**Usage:**
```python
# Delete item (and children)
success = item_service.delete_item(board, item)

# Delete from specific column
success = item_service.delete_item_from_column(board, item, column)
```

#### Parent/Child Relationships

```python
def set_parent(self, board: Board, item: Item, parent_item: Optional[Item]) -> bool:
    """Set or clear the parent of an item."""

def get_item_hierarchy(self, board: Board) -> Dict[str, List[Item]]:
    """Get the complete parent/child hierarchy for the board."""
```

**Usage:**
```python
# Set parent relationship
item_service.set_parent(board, child_item, parent_item)

# Clear parent relationship
item_service.set_parent(board, child_item, None)

# Get hierarchy
hierarchy = item_service.get_item_hierarchy(board)
for parent_id, children in hierarchy.items():
    print(f"Parent {parent_id} has {len(children)} children")
```

## ValidationService

The `ValidationService` enforces business rules and data validation across the application.

### Constructor

```python
class ValidationService:
    def __init__(self):
        pass  # Stateless service
```

### Validation Methods

#### Board Validation

```python
def validate_board_name(self, name: str) -> bool:
    """Validate that a board name is acceptable."""

def validate_board(self, board: Board) -> List[str]:
    """Validate a complete board and return any errors."""
```

#### Column Validation

```python
def validate_column_name(self, name: str) -> bool:
    """Validate that a column name is acceptable."""

def validate_column_position(self, position: int, max_position: int) -> bool:
    """Validate that a column position is valid."""
```

#### Item Validation

```python
def validate_item_title(self, title: str) -> bool:
    """Validate that an item title is acceptable."""

def validate_item(self, item: Item) -> List[str]:
    """Validate a complete item and return any errors."""

def validate_parent_relationship(self, item: Item, parent: Item) -> bool:
    """Validate that a parent/child relationship is valid."""
```

### Usage

```python
validation_service = get_container().get(ValidationService)

# Validate board name
if validation_service.validate_board_name("my-project"):
    print("Valid board name")

# Validate complete board
errors = validation_service.validate_board(board)
if errors:
    for error in errors:
        print(f"Validation error: {error}")

# Validate item title
if not validation_service.validate_item_title(""):
    print("Item title cannot be empty")
```

## Service Integration

Services work together through the dependency injection container:

### Cross-Service Operations

```python
def complete_board_setup():
    board_service = get_board_service()
    item_service = get_item_service()

    # Create board
    board = board_service.create_board("new-project")

    # Add items to board
    todo_column = board.get_column("to-do")
    item = item_service.create_item(
        board=board,
        column=todo_column,
        title="Initial task"
    )

    # Save everything
    board_service.save_board(board)
```

### Service Context Sharing

Services share context through the logging system:

```python
# BoardService logs with board context
board_service.load_board("my-project")
# → [board=my-project] Loading board

# ItemService inherits and extends context
item_service.create_item(board, column, "task")
# → [board=my-project, column=todo, item=task] Creating new item
```

## Error Handling

Services use Python's exception handling with structured logging:

### Service-Level Errors

```python
def load_board(self, name: str) -> Optional[Board]:
    try:
        self._logger.debug("Loading board", board=name)
        board = self._board_repository.load_board(name)
        if board:
            self._logger.info("Board loaded successfully", board=name)
        else:
            self._logger.warning("Board not found", board=name)
        return board
    except Exception as e:
        self._logger.error("Failed to load board", board=name, error=str(e))
        return None
```

### Validation Errors

```python
def create_item(self, board: Board, column: Column, title: str) -> Optional[Item]:
    if not self._validation_service.validate_item_title(title):
        self._logger.warning("Invalid item title", board=board.name, title=title)
        return None

    # Continue with creation
```

## Best Practices

### Service Design

1. **Single Responsibility**: Each service handles one domain area
2. **Dependency Injection**: Declare all dependencies in constructor
3. **Context Logging**: Include relevant context in all log messages
4. **Validation**: Validate inputs before processing
5. **Error Handling**: Log errors and return appropriate values

### Using Services

1. **Get from Container**: Always use dependency injection container
2. **Handle None Returns**: Services may return None for failures
3. **Check Validation**: Validate data before calling service methods
4. **Monitor Logs**: Use logging output for debugging and monitoring

```python
# Good service usage
board_service = get_board_service()
board = board_service.load_board("my-project")
if board:
    # Process board
    pass
else:
    print("Failed to load board")

# Avoid direct instantiation
# board_service = BoardService(...)  # Don't do this
```

The services layer provides a clean, well-tested foundation for all business operations in MKanban, with comprehensive logging and validation built in.