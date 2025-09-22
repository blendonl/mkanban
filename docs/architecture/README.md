# MKanban Architecture

MKanban follows clean architecture principles with clear separation of concerns and dependency injection for maintainable, testable code.

## Overview

The application is structured in layers:

1. **Domain Layer** - Core business logic and models
2. **Service Layer** - Business operations and orchestration
3. **Infrastructure Layer** - External concerns (storage, UI, integrations)
4. **Application Layer** - Entry points and coordination

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   main.py   │  │   app.py    │  │  CLI Commands   │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                    Service Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │BoardService │  │ItemService  │  │ValidationService│  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                Infrastructure Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │Repositories │  │   Storage   │  │   TUI Widgets   │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │    JIRA     │  │   Daemon    │  │     Logging     │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│                    Domain Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Models    │  │    Types    │  │   Constants     │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### Dependency Injection Container

Central to the architecture is the dependency injection container (`src.core.dependency_container`):

```python
container = get_container()
board_service = container.get(BoardService)
```

Benefits:
- **Testability**: Easy to inject mocks for testing
- **Maintainability**: Clear dependencies and lifecycle management
- **Extensibility**: New services automatically get dependencies

### Configuration System

Unified configuration management (`src.config.configuration_manager`):

- **Environment overrides**: `MKANBAN_*` environment variables
- **JSON configuration**: Persistent settings in `~/.mkanban/config.json`
- **Dataclass-based**: Type-safe configuration with defaults
- **Hierarchical**: Daemon, JIRA, and logging sub-configurations

### Service Layer

Business logic organized into focused services:

- **BoardService**: Board operations (create, load, save, delete)
- **ItemService**: Item management (CRUD operations, parent/child relationships)
- **ValidationService**: Data validation and constraints

### Repository Pattern

Separation of storage concerns:

- **MarkdownBoardRepository**: Board-level storage operations
- **MarkdownStorageRepository**: Item-level storage operations
- **Interfaces**: Abstract contracts for testability

### Utilities

Cross-cutting concerns:

- **PathResolver**: Centralized path management with session awareness
- **LoggerFactory**: Context-aware logging with structured metadata
- **FileOperations**: Safe file system operations

## Data Flow

### Board Loading
```
User Request → BoardService → MarkdownBoardRepository → File System
                    ↓
            Validation ← Models ← Parsed Data
```

### Item Operations
```
User Action → ItemService → MarkdownStorageRepository → File System
                   ↓
            Context Logging → LoggerFactory → Log Files
```

### Configuration Access
```
Service → ConfigurationManager → Environment/JSON → Defaults
```

## Key Design Patterns

### 1. Dependency Injection
- Services declare dependencies in constructors
- Container resolves and injects dependencies
- Singleton lifecycle for most services

### 2. Repository Pattern
- Abstract storage operations from business logic
- Swappable storage implementations
- Clear separation between board and item storage

### 3. Factory Pattern
- LoggerFactory creates context-aware loggers
- Centralized logger configuration
- Consistent logging across components

### 4. Service Layer Pattern
- Business logic encapsulated in services
- Clear boundaries between concerns
- Composable operations

## File Organization

```
src/
├── core/                    # Core domain and DI
│   ├── constants.py         # Application constants
│   ├── dependency_container.py  # DI container
│   └── types.py            # Core type definitions
├── config/                  # Configuration management
│   ├── configuration_manager.py  # Unified config
│   ├── environment.py       # Legacy environment utils
│   └── settings.py          # Legacy settings (deprecated)
├── models/                  # Domain models
│   ├── board.py            # Board model
│   ├── column.py           # Column model
│   ├── item.py             # Item model
│   └── parent.py           # Parent grouping model
├── services/                # Business logic layer
│   ├── board_service.py    # Board operations
│   ├── item_service.py     # Item management
│   └── validation_service.py  # Data validation
├── infrastructure/          # External concerns
│   ├── storage/            # Persistence layer
│   ├── jira/              # JIRA integration
│   └── tmux/              # Session management
├── utils/                   # Cross-cutting utilities
│   ├── logger_factory.py   # Logging infrastructure
│   ├── path_resolver.py    # Path management
│   └── file_operations.py  # File system ops
└── ui/                     # User interface
    ├── app.py              # Main TUI application
    └── widgets/            # UI components
```

## Logging Architecture

Context-aware logging system:

### Logger Types
- **Daemon Logger**: Background operations with timestamped files
- **TUI Logger**: Interactive session logging
- **Component Loggers**: Service-specific logging

### Context Enrichment
- **Board Context**: Board name and path
- **Column Context**: Column name and position
- **Item Context**: Item title and ID
- **JIRA Context**: Ticket prefix for JIRA operations

### Log Structure
```
[2024-01-01T10:00:00] DAEMON INFO board_service: Loading board [board=my-project, path=/data/boards/my-project]
[2024-01-01T10:00:00] DAEMON DEBUG item_service: Creating item [board=my-project, column=to-do, item=Fix bug]
[2024-01-01T10:00:00] DAEMON INFO jira_service: [JIRA:PROJ-123] Syncing ticket [board=jira-tickets, item=PROJ-123]
```

## Extension Points

### Adding New Services
1. Create service class with constructor dependencies
2. Register factory in dependency container
3. Services automatically get logging and configuration

### Adding New Storage Backends
1. Implement repository interfaces
2. Register in dependency container
3. Existing services work unchanged

### Adding New Configuration
1. Add fields to configuration dataclasses
2. Add environment variable mapping
3. Update default factories

## Testing Strategy

- **Unit Tests**: Mock dependencies via container
- **Integration Tests**: Use test container configuration
- **Repository Tests**: Test against temporary file systems
- **Service Tests**: Focus on business logic with mocked dependencies

The architecture promotes testability through dependency injection and clear separation of concerns.