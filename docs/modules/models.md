# Domain Models and Types

MKanban uses Pydantic models to define domain entities with type safety, validation, and serialization. The domain layer contains the core business objects that represent the Kanban board structure.

## Overview

Core domain entities:

- **Board**: Top-level container for columns and configuration
- **Column**: Organizational units that contain items
- **Item**: Individual tasks with rich metadata and integrations
- **Parent**: Grouping mechanism for related items
- **Core Types**: Type aliases and enums for consistency

## Core Types

The `src.core.types` module defines type aliases and enums used throughout the application.

### Type Aliases

```python
ItemId = str           # Unique identifier for items
ColumnId = str         # Unique identifier for columns
BoardId = str          # Unique identifier for boards
ParentId = str         # Unique identifier for parent groups
FilePath = Union[str, Path]  # File system paths
Timestamp = datetime   # Datetime objects for timestamps
Metadata = Dict[str, Union[str, int, bool, List, Dict]]  # General metadata
```

### Enums

#### RefreshType

```python
class RefreshType(Enum):
    FULL = "full"           # Complete board refresh
    PARTIAL = "partial"     # Update only changed items
    ITEMS_ONLY = "items_only"  # Refresh items without structure
```

#### ThemeType

```python
class ThemeType(Enum):
    DARK = "dark"          # Dark theme
    LIGHT = "light"        # Light theme
```

#### ParentColor

```python
class ParentColor(Enum):
    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    PURPLE = "purple"
    CYAN = "cyan"
    ORANGE = "orange"
```

## Board Model

The `Board` model represents the top-level Kanban board container.

### Structure

```python
class Board(BaseModel):
    id: BoardId = Field(default="")
    name: str
    description: str = ""
    file_path: Optional[FilePath] = None
    columns: list[Column] = Field(default_factory=list)
    parents: list[Parent] = Field(default_factory=list)
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)
```

### Key Features

#### Automatic ID Generation

```python
def model_post_init(self, __context) -> None:
    if self.file_path and not self.id:
        dir_name = Path(self.file_path).parent.name
        self.id = dir_name
        if not self.name or self.name == dir_name:
            self.name = dir_name
    elif not self.id:
        self.id = generate_id_from_name(self.name) or "unnamed_board"
```

**Behavior:**
- Uses directory name as ID if `file_path` is provided
- Generates ID from name using `generate_id_from_name()` utility
- Falls back to "unnamed_board" if no name provided

#### Column Management

```python
def add_column(self, name: str, position: Optional[int] = None) -> Column:
    """Add a new column to the board."""

def remove_column(self, column_id: ColumnId) -> bool:
    """Remove a column from the board."""

def get_column_by_id(self, column_id: ColumnId) -> Optional[Column]:
    """Get a column by its ID."""

def get_first_column(self) -> Optional[Column]:
    """Get the first column by position."""
```

**Usage:**
```python
board = Board(name="My Project")

# Add columns
todo_column = board.add_column("To Do", position=0)
progress_column = board.add_column("In Progress", position=1)
done_column = board.add_column("Done", position=2)

# Get column
column = board.get_column_by_id("to-do")
if column:
    print(f"Found column: {column.name}")

# Remove column
board.remove_column("old-column-id")
```

#### Parent/Child Management

```python
def add_parent(self, name: str, color: str = "blue") -> Parent:
    """Add a new parent group."""

def remove_parent(self, parent_id: ParentId) -> bool:
    """Remove a parent group."""

def get_parent_by_id(self, parent_id: ParentId) -> Optional[Parent]:
    """Get a parent by its ID."""

def get_orphaned_items(self) -> list[Item]:
    """Get all items without a parent."""
```

**Usage:**
```python
# Add parent groups
auth_parent = board.add_parent("Authentication", color="blue")
ui_parent = board.add_parent("User Interface", color="green")

# Get orphaned items
orphaned = board.get_orphaned_items()
print(f"Found {len(orphaned)} items without parents")
```

## Column Model

The `Column` model represents individual columns within a board.

### Structure

```python
class Column(BaseModel):
    id: ColumnId = Field(default="")
    name: str
    position: int = 0
    limit: Optional[int] = None  # WIP limit
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)
    items: list[Item] = Field(default_factory=list)
    file_path: Optional[FilePath] = None
```

### Features

#### Automatic ID and Name Generation

```python
def model_post_init(self, __context) -> None:
    if self.file_path and not self.id:
        dir_name = Path(self.file_path).parent.name
        self.id = dir_name
        if not self.name or self.name == dir_name:
            self.name = dir_name.replace("-", " ").replace("_", " ").title()
    elif not self.id:
        self.id = generate_id_from_name(self.name) or "unnamed_column"
```

**Behavior:**
- Uses directory name as ID if loading from file system
- Converts directory names to human-readable titles ("to-do" → "To Do")
- Generates ID from name for new columns

#### Item Management

```python
def add_item(self, title: str, parent_id: Optional[ParentId] = None) -> Item:
    """Add a new item to this column."""

def move_item_to_end(self, item: Item) -> bool:
    """Move an item to the end of this column."""

def remove_item(self, item_id: str) -> bool:
    """Remove an item from this column."""

def get_item_by_id(self, item_id: str) -> Optional[Item]:
    """Get an item by its ID."""

def get_all_items(self) -> list[Item]:
    """Get all items in this column."""
```

**Usage:**
```python
column = Column(name="To Do", position=0)

# Add items
item1 = column.add_item("Fix authentication bug")
item2 = column.add_item("Update documentation", parent_id=auth_parent.id)

# Move item
column.move_item_to_end(item1)

# Get items
all_items = column.get_all_items()
specific_item = column.get_item_by_id("item-123")
```

#### WIP Limits

```python
column = Column(name="In Progress", position=1, limit=3)

# Check if column is at limit
if len(column.items) >= column.limit:
    print("Column at WIP limit!")
```

## Item Model

The `Item` model represents individual tasks with support for Git and JIRA integration.

### Core Structure

```python
class Item(BaseModel):
    id: ItemId = Field(default="")
    title: str
    column_id: ColumnId
    description: str = ""
    parent_id: Optional[ParentId] = None
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)
    file_path: Optional[FilePath] = None

    # Git integration
    git_metadata: Optional[GitMetadata] = None
    is_git_managed: bool = Field(default=False)
    auto_sync_enabled: bool = Field(default=True)

    # JIRA integration
    jira_metadata: Optional[JiraMetadata] = None
    is_jira_managed: bool = Field(default=False)
    linked_tickets: List[str] = Field(default_factory=list)
```

### Git Integration

#### GitMetadata Model

```python
class GitMetadata(BaseModel):
    repository_path: str
    branch_name: str
    branch_full_name: str
    last_commit_hash: Optional[str] = None
    last_commit_message: Optional[str] = None
    last_commit_author: Optional[str] = None
    last_commit_date: Optional[str] = None
    is_current_branch: bool = False
    branch_created_at: Optional[Timestamp] = None
    branch_deleted_at: Optional[Timestamp] = None
```

#### Git-Managed Items

```python
# Create from Git branch
item = Item.from_git_branch(
    branch_name="feature/auth-improvements",
    repository_path="/home/user/project",
    column_id="todo",
    last_commit_hash="abc123",
    last_commit_message="Add login validation",
    is_current=True
)

# Git operations
item.set_current_branch(True)
item.mark_branch_deleted()
item.update_git_metadata(last_commit_hash="def456")

# Auto-sync features
if item.should_auto_activate():
    # Move to in-progress when branch becomes current
    item.move_to_column("in-progress")

if item.should_auto_complete():
    # Move to done when branch is deleted
    item.move_to_column("done")
```

#### Title Generation from Branch

```python
def _generate_title_from_branch(self) -> str:
    """Generate a human-readable title from branch name"""
    branch_name = self.git_metadata.branch_name

    # Remove common prefixes
    prefixes = ["feature/", "bugfix/", "hotfix/", "fix/", "feat/"]
    for prefix in prefixes:
        if branch_name.startswith(prefix):
            branch_name = branch_name[len(prefix):]
            break

    # Convert to title case
    title = branch_name.replace("-", " ").replace("_", " ").title()
    return title
```

**Examples:**
- `feature/auth-improvements` → "Auth Improvements"
- `bugfix/login-validation` → "Login Validation"
- `hotfix/security-patch` → "Security Patch"

### JIRA Integration

#### JiraMetadata Model

```python
class JiraMetadata(BaseModel):
    ticket_key: str          # PROJ-123
    ticket_id: str           # Internal Jira ID
    ticket_url: str
    project_key: str
    issue_type: str
    priority: Optional[str] = None
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    last_sync: Optional[Timestamp] = None
    jira_status: str = ""
```

#### JIRA-Managed Items

```python
# Create from JIRA ticket
ticket_data = {
    "id": "12345",
    "url": "https://company.atlassian.net/browse/PROJ-123",
    "project_key": "PROJ",
    "issue_type": "Bug",
    "summary": "Fix authentication issue",
    "description": "Users cannot log in with valid credentials",
    "status": "To Do",
    "priority": "High",
    "assignee": "john.doe@company.com"
}

item = Item.from_jira_ticket("PROJ-123", ticket_data, "todo")

# JIRA operations
item.update_jira_metadata(priority="Critical", assignee="jane.doe@company.com")
item.add_linked_ticket("PROJ-124")
item.remove_linked_ticket("PROJ-125")

# Sync checking
if item.should_sync_to_jira():
    # Sync changes back to JIRA
    pass
```

### Item Operations

#### Basic Operations

```python
def update(self, **kwargs) -> None:
    """Update item fields and timestamp."""

def move_to_column(self, column_id: ColumnId) -> None:
    """Move item to a different column."""

def set_parent(self, parent_id: Optional[ParentId]) -> None:
    """Set or clear the parent relationship."""
```

#### Utility Methods

```python
@property
def has_parent(self) -> bool:
    """Check if item has a parent."""

def get_repository_name(self) -> Optional[str]:
    """Get repository name from Git metadata."""

def get_short_commit_hash(self) -> Optional[str]:
    """Get 7-character commit hash."""

def is_branch_active(self) -> bool:
    """Check if Git branch is still active."""

def get_jira_ticket_key(self) -> Optional[str]:
    """Get primary JIRA ticket key."""
```

**Usage:**
```python
item = Item(title="Fix bug", column_id="todo")

# Basic operations
item.update(title="Fix critical bug", description="Updated description")
item.move_to_column("in-progress")
item.set_parent(auth_parent.id)

# Check properties
if item.has_parent:
    print(f"Item belongs to parent: {item.parent_id}")

# Git information
if item.is_git_managed:
    repo = item.get_repository_name()
    commit = item.get_short_commit_hash()
    print(f"Branch in {repo}, commit {commit}")

# JIRA information
if item.is_jira_managed:
    ticket = item.get_jira_ticket_key()
    print(f"JIRA ticket: {ticket}")
```

## Parent Model

The `Parent` model represents grouping containers for related items.

### Structure

```python
class Parent(BaseModel):
    id: ParentId = Field(default="")
    name: str
    description: str = ""
    color: str = ParentColor.BLUE.value
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)
```

### Features

#### Automatic ID Generation

```python
def model_post_init(self, __context) -> None:
    if not self.id:
        self.id = generate_id_from_name(self.name) or "unnamed_parent"
```

#### Color Coding

```python
# Create parents with colors
auth_parent = Parent(name="Authentication", color=ParentColor.BLUE.value)
ui_parent = Parent(name="UI Components", color=ParentColor.GREEN.value)
api_parent = Parent(name="API", color=ParentColor.RED.value)

# Update parent
auth_parent.update(color=ParentColor.PURPLE.value, description="All auth-related tasks")
```

## Model Relationships

### Board → Columns → Items → Parents

```python
# Create complete board structure
board = Board(name="Project Alpha")

# Add columns
todo = board.add_column("To Do")
progress = board.add_column("In Progress")
done = board.add_column("Done")

# Add parents
auth_parent = board.add_parent("Authentication", color="blue")
ui_parent = board.add_parent("User Interface", color="green")

# Add items
login_item = todo.add_item("Implement login", parent_id=auth_parent.id)
dashboard_item = todo.add_item("Create dashboard", parent_id=ui_parent.id)

# Move items
login_item.move_to_column(progress.id)
progress.move_item_to_end(login_item)
```

### Git Integration Workflow

```python
# Create Git-managed item
git_item = Item.from_git_branch(
    branch_name="feature/user-profiles",
    repository_path="/home/user/myapp",
    column_id=todo.id,
    is_current=True
)

# Auto-activation when branch becomes current
if git_item.should_auto_activate():
    git_item.move_to_column(progress.id)

# Auto-completion when branch is deleted
git_item.mark_branch_deleted()
if git_item.should_auto_complete():
    git_item.move_to_column(done.id)
```

### JIRA Integration Workflow

```python
# Create JIRA-managed item
jira_item = Item.from_jira_ticket("PROJ-123", ticket_data, todo.id)

# Link related tickets
jira_item.add_linked_ticket("PROJ-124")
jira_item.add_linked_ticket("PROJ-125")

# Update from JIRA sync
jira_item.update_jira_metadata(
    priority="High",
    assignee="new.assignee@company.com",
    jira_status="In Progress"
)

# Check if needs sync back to JIRA
if jira_item.should_sync_to_jira():
    # Sync changes back to JIRA system
    pass
```

## Serialization

All models support serialization for storage and API usage:

```python
# Board serialization (automatic with Pydantic)
board_dict = board.model_dump()
board_json = board.model_dump_json()

# Item serialization with metadata
item_dict = item.to_dict()  # Custom method includes Git/JIRA metadata

# Deserialization
board = Board.model_validate(board_dict)
board = Board.model_validate_json(board_json)
```

## Validation

Pydantic provides automatic validation:

```python
# Type validation
try:
    item = Item(title="Test", column_id=123)  # Error: column_id must be string
except ValidationError as e:
    print(f"Validation error: {e}")

# Required fields
try:
    item = Item(column_id="todo")  # Error: title is required
except ValidationError as e:
    print(f"Missing title: {e}")

# Custom validation through model methods
if not board.get_column_by_id("invalid-id"):
    print("Column does not exist")
```

## Best Practices

### Model Usage

1. **Use factory methods**: Use `from_git_branch()` and `from_jira_ticket()` for integration
2. **Check existence**: Always check if relationships exist before accessing
3. **Update timestamps**: Use `update()` methods to maintain timestamps
4. **Handle None returns**: Many methods return Optional types

### Integration Patterns

1. **Git-managed items**: Set `is_git_managed=True` and provide `git_metadata`
2. **JIRA-managed items**: Set `is_jira_managed=True` and provide `jira_metadata`
3. **Auto-sync**: Use `auto_sync_enabled` to control automatic behavior
4. **Branch tracking**: Use `is_current_branch` for current branch awareness

### Performance Considerations

1. **Lazy loading**: Items are loaded separately from columns
2. **Batch operations**: Update multiple items together when possible
3. **Selective serialization**: Use `to_dict()` methods for efficient serialization
4. **Index by ID**: Use ID-based lookups for performance

The domain models provide a rich, type-safe foundation for all Kanban operations with built-in support for Git and JIRA integrations.