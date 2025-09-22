# Dependency Injection System

MKanban uses a lightweight dependency injection container to manage service dependencies, promote testability, and provide clean separation of concerns.

## Overview

The dependency injection system consists of:

- **DependencyContainer**: Core container managing service instances and factories
- **Global Container**: Singleton container accessible throughout the application
- **Service Registration**: Automatic registration of core services
- **Convenience Functions**: Easy access to common services

## DependencyContainer

The `DependencyContainer` class manages service lifecycles and dependencies.

### Usage

```python
from src.core.dependency_container import get_container

# Get the global container
container = get_container()

# Request services
board_service = container.get(BoardService)
config_manager = container.get(ConfigurationManager)
logger = container.get_daemon_logger("my_component")
```

### Core Methods

#### Service Resolution

- **`get(interface: Type[T]) -> T`**: Get an instance of the requested service
- **`register_factory(interface, factory)`**: Register a factory function for a service
- **`register_instance(interface, instance)`**: Register a singleton instance

#### Logging Convenience

- **`get_logger(name, component)`**: Get a context-aware logger
- **`get_daemon_logger(name)`**: Get a daemon-specific logger
- **`get_tui_logger(name)`**: Get a TUI-specific logger

#### Testing Support

- **`clear_instances()`**: Clear all singleton instances
- **`setup_for_testing()`**: Configure container for testing

### Example

```python
from src.core.dependency_container import get_container
from src.services.board_service import BoardService

container = get_container()

# Services are automatically resolved with their dependencies
board_service = container.get(BoardService)
# BoardService gets: MarkdownBoardRepository, ValidationService, Logger

# Use the service
board = board_service.load_board("my-project")
```

## Service Registration

Services are automatically registered with their factories in the container setup.

### Default Service Factories

```python
def _setup_default_factories(self):
    # Configuration
    self._factories[ConfigurationManager] = lambda: ConfigurationManager()

    # Utilities
    self._factories[PathResolver] = lambda: PathResolver(self.get(ConfigurationManager))
    self._factories[LoggerFactory] = lambda: LoggerFactory(
        self.get(ConfigurationManager),
        self.get(PathResolver)
    )

    # File operations
    self._factories[FileOperations] = lambda: FileOperations(
        self.get(LoggerFactory).get_daemon_logger("file_operations")
    )

    # Repositories
    self._factories[MarkdownBoardRepository] = lambda: MarkdownBoardRepository(
        self.get(PathResolver),
        self.get(LoggerFactory).get_daemon_logger("board_repository")
    )

    # Services
    self._factories[BoardService] = lambda: BoardService(
        self.get(MarkdownBoardRepository),
        self.get(ValidationService),
        self.get(LoggerFactory).get_daemon_logger("board_service")
    )
```

### Service Dependencies

Services declare their dependencies in their constructors:

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

## Singleton Lifecycle

Most services are managed as singletons:

1. **First request**: Service factory is called, instance is created and cached
2. **Subsequent requests**: Cached instance is returned
3. **Dependencies**: Automatically resolved and injected

### Benefits

- **Memory efficiency**: Single instance per service type
- **State consistency**: Shared state across the application
- **Performance**: No repeated initialization

## Global Container Access

The global container provides application-wide access to services:

```python
# Global container instance
_container: Optional[DependencyContainer] = None

def get_container() -> DependencyContainer:
    """Get the global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container

def set_container(container: DependencyContainer) -> None:
    """Set the global dependency container (useful for testing)."""
    global _container
    _container = container
```

### Convenience Functions

```python
# Direct access to common services
def get_board_service() -> BoardService:
    return get_container().get(BoardService)

def get_config_manager() -> ConfigurationManager:
    return get_container().get(ConfigurationManager)

def get_daemon_logger(name: str) -> ContextAwareLogger:
    return get_container().get_daemon_logger(name)
```

## Adding New Services

### 1. Create Service Class

```python
class MyNewService:
    def __init__(
        self,
        config_manager: ConfigurationManager,
        logger: ContextAwareLogger
    ):
        self._config = config_manager
        self._logger = logger

    def do_something(self):
        self._logger.info("Doing something")
```

### 2. Register Factory

```python
# In DependencyContainer._setup_default_factories()
self._factories[MyNewService] = lambda: MyNewService(
    self.get(ConfigurationManager),
    self.get(LoggerFactory).get_daemon_logger("my_new_service")
)
```

### 3. Use Service

```python
from src.core.dependency_container import get_container

container = get_container()
my_service = container.get(MyNewService)
my_service.do_something()
```

## Testing with Dependency Injection

The container makes testing easy by allowing dependency mocking:

### Unit Testing

```python
import unittest.mock as mock
from src.core.dependency_container import DependencyContainer, set_container

def test_board_service():
    # Create test container
    test_container = DependencyContainer()

    # Mock dependencies
    mock_repository = mock.Mock()
    mock_validator = mock.Mock()
    mock_logger = mock.Mock()

    # Register mocks
    test_container.register_instance(BoardRepository, mock_repository)
    test_container.register_instance(ValidationService, mock_validator)
    test_container.register_factory(
        BoardService,
        lambda: BoardService(mock_repository, mock_validator, mock_logger)
    )

    # Use test container
    set_container(test_container)

    # Test service
    board_service = test_container.get(BoardService)
    board_service.create_board("test")

    # Verify mocks
    mock_repository.save_board.assert_called_once()
```

### Integration Testing

```python
def test_full_integration():
    # Use real container but with test configuration
    container = get_container()
    container.setup_for_testing()

    # Override specific services for testing
    test_config = create_test_configuration()
    container.register_instance(ConfigurationManager, test_config)

    # Test with real services
    board_service = container.get(BoardService)
    board = board_service.create_board("integration-test")

    assert board.name == "integration-test"
```

## Logger Integration

The container integrates closely with the logging system:

### Context-Aware Loggers

```python
# Get a logger with automatic context
logger = container.get_daemon_logger("board_operations")

# Logger automatically includes context
logger.info("Loading board", board="my-project")
# Output: [2024-01-01T10:00:00] DAEMON INFO board_operations: Loading board [board=my-project]
```

### Component-Specific Loggers

```python
# Different log destinations based on component
daemon_logger = container.get_daemon_logger("sync")      # → daemon logs
tui_logger = container.get_tui_logger("keyboard")        # → TUI logs
```

## Error Handling

### Missing Dependencies

```python
try:
    service = container.get(UnregisteredService)
except ValueError as e:
    print(f"Service not registered: {e}")
```

### Factory Errors

```python
# Factory that might fail
def risky_factory():
    if not some_condition:
        raise RuntimeError("Cannot create service")
    return SomeService()

container.register_factory(SomeService, risky_factory)

# Error propagates to caller
try:
    service = container.get(SomeService)
except RuntimeError as e:
    print(f"Service creation failed: {e}")
```

## Best Practices

### For Service Developers

1. **Declare dependencies in constructor**: Make dependencies explicit
2. **Use interfaces when possible**: Depend on abstractions, not concretions
3. **Keep constructors simple**: Avoid complex initialization in constructors
4. **Request specific loggers**: Use `get_daemon_logger("service_name")`

```python
# Good
class GoodService:
    def __init__(self, repository: Repository, logger: ContextAwareLogger):
        self._repository = repository
        self._logger = logger

# Avoid
class BadService:
    def __init__(self):
        self._repository = SomeConcreteRepository()  # Hard dependency
        self._logger = logging.getLogger(__name__)   # Generic logger
```

### For Application Developers

1. **Use container for service access**: Don't instantiate services manually
2. **Request services at boundaries**: Get services in main functions, not deep in call stacks
3. **Prefer convenience functions**: Use `get_board_service()` over `get_container().get(BoardService)`

```python
# Good - request at boundary
def main():
    board_service = get_board_service()
    board_service.process_boards()

# Avoid - requesting deep in call stack
def some_deep_function():
    board_service = get_board_service()  # Creates coupling
```

### For Testing

1. **Use test containers**: Create separate containers for tests
2. **Mock at boundaries**: Mock repositories and external services
3. **Clear between tests**: Use `clear_instances()` to avoid test pollution

## Migration Guide

When converting existing code to use dependency injection:

### Before
```python
# Manual instantiation with hidden dependencies
def create_board_service():
    config = Settings.load()
    repository = MarkdownBoardRepository(config)
    validator = ValidationService()
    logger = logging.getLogger("board_service")
    return BoardService(repository, validator, logger)

board_service = create_board_service()
```

### After
```python
# Container-managed with explicit dependencies
from src.core.dependency_container import get_board_service

board_service = get_board_service()
```

The dependency injection system simplifies service management, improves testability, and provides a foundation for clean architecture patterns.