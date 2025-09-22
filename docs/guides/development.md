# Development Guide

This guide covers everything you need to know to contribute to MKanban, from setting up your development environment to understanding the codebase architecture and testing practices.

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Git
- Make (optional, for convenience commands)
- tmux (for session-based features)

### Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd mkanban

# Create and activate virtual environment
make setup
# Or manually:
# python -m venv venv
# source venv/bin/activate  # On Windows: venv\Scripts\activate
# pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests to verify setup
make test
```

### Development Workflow

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Run the application in development
python main.py --data-dir ./dev-data

# Build executable (optional)
make executable
```

## Project Structure

```
mkanban/
├── src/                          # Source code
│   ├── core/                     # Core domain and DI
│   │   ├── constants.py          # Application constants
│   │   ├── dependency_container.py  # Dependency injection
│   │   └── types.py              # Type definitions
│   ├── config/                   # Configuration management
│   │   ├── configuration_manager.py  # Unified configuration
│   │   ├── environment.py        # Legacy environment utils
│   │   └── settings.py           # Legacy settings
│   ├── domain/                   # Domain models and interfaces
│   │   ├── entities/             # Pydantic models
│   │   └── repositories/         # Repository interfaces
│   ├── services/                 # Business logic layer
│   │   ├── board_service.py      # Board operations
│   │   ├── item_service.py       # Item management
│   │   └── validation_service.py # Data validation
│   ├── infrastructure/           # External integrations
│   │   ├── storage/              # File system storage
│   │   ├── jira/                 # JIRA integration
│   │   └── tmux/                 # Session management
│   ├── utils/                    # Cross-cutting utilities
│   │   ├── logger_factory.py     # Logging infrastructure
│   │   ├── path_resolver.py      # Path management
│   │   └── file_operations.py    # File system operations
│   └── ui/                       # User interface
│       ├── app.py                # Main TUI application
│       └── widgets/              # UI components
├── tests/                        # Test suite
├── docs/                         # Documentation
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── Makefile                      # Development commands
├── main.py                       # Entry point
└── CLAUDE.md                     # AI assistant instructions
```

## Architecture Overview

MKanban follows clean architecture principles:

### Dependency Flow

```
UI/CLI → Services → Repositories → Models
         ↓
    Configuration
         ↓
    Utilities (Logging, Paths, etc.)
```

### Key Principles

1. **Dependency Injection**: All components get dependencies injected
2. **Single Responsibility**: Each class/module has one clear purpose
3. **Repository Pattern**: Storage abstracted behind interfaces
4. **Configuration-Driven**: Behavior controlled by configuration
5. **Context-Aware Logging**: All operations include relevant context

## Development Patterns

### Adding a New Service

1. **Create the service class**:

```python
# src/services/my_new_service.py
from src.services.validation_service import ValidationService
from src.utils.logger_factory import ContextAwareLogger

class MyNewService:
    def __init__(
        self,
        validation_service: ValidationService,
        logger: ContextAwareLogger
    ):
        self._validation_service = validation_service
        self._logger = logger

    def do_something(self, data: str) -> bool:
        self._logger.info("Doing something", data=data)

        if not self._validation_service.validate_input(data):
            self._logger.warning("Invalid input", data=data)
            return False

        # Implementation here
        self._logger.info("Operation completed successfully", data=data)
        return True
```

2. **Register in dependency container**:

```python
# src/core/dependency_container.py
def _setup_default_factories(self):
    # ... existing factories ...

    self._factories[MyNewService] = lambda: MyNewService(
        self.get(ValidationService),
        self.get(LoggerFactory).get_daemon_logger("my_new_service")
    )
```

3. **Add convenience function**:

```python
# src/core/dependency_container.py
def get_my_new_service() -> MyNewService:
    return get_container().get(MyNewService)
```

### Adding Configuration Options

1. **Add to configuration dataclass**:

```python
# src/config/configuration_manager.py
@dataclass
class UnifiedConfiguration:
    # ... existing fields ...
    my_new_setting: bool = True
    my_new_value: int = 42
```

2. **Add environment variable mapping**:

```python
# src/config/configuration_manager.py
def _apply_environment_overrides(self, config: UnifiedConfiguration) -> None:
    # ... existing overrides ...

    if my_setting := os.environ.get("MKANBAN_MY_SETTING"):
        config.my_new_setting = my_setting.lower() in ("true", "1", "yes")

    if my_value := os.environ.get("MKANBAN_MY_VALUE"):
        try:
            config.my_new_value = int(my_value)
        except ValueError:
            pass
```

3. **Use in services**:

```python
class MyService:
    def __init__(self, config_manager: ConfigurationManager):
        self.config = config_manager.config

    def operation(self):
        if self.config.my_new_setting:
            # Do something based on configuration
            pass
```

### Adding New Models

1. **Define the model**:

```python
# src/domain/entities/my_model.py
from pydantic import BaseModel, Field
from src.core.types import Timestamp
from src.utils.date_utils import now

class MyModel(BaseModel):
    id: str = Field(default="")
    name: str
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)

    def model_post_init(self, __context) -> None:
        if not self.id:
            self.id = generate_id_from_name(self.name) or "unnamed"

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = now()
```

2. **Add to exports**:

```python
# src/domain/entities/__init__.py
from .my_model import MyModel

__all__ = ["Board", "Column", "Item", "Parent", "MyModel"]
```

### Adding Repository Methods

1. **Add to interface**:

```python
# src/domain/repositories/my_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.my_model import MyModel

class MyRepository(ABC):
    @abstractmethod
    def save_model(self, model: MyModel) -> bool:
        pass

    @abstractmethod
    def load_model(self, id: str) -> Optional[MyModel]:
        pass
```

2. **Implement concrete repository**:

```python
# src/infrastructure/storage/markdown_my_repository.py
from pathlib import Path
from typing import Optional
from src.domain.repositories.my_repository import MyRepository
from src.domain.entities.my_model import MyModel
from src.utils.path_resolver import PathResolver
from src.utils.logger_factory import ContextAwareLogger

class MarkdownMyRepository(MyRepository):
    def __init__(self, path_resolver: PathResolver, logger: ContextAwareLogger):
        self.path_resolver = path_resolver
        self.logger = logger

    def save_model(self, model: MyModel) -> bool:
        try:
            path = self._get_model_path(model.id)
            content = self._serialize_model(model)

            # Use file operations for safe writing
            file_ops = get_container().get(FileOperations)
            success = file_ops.safe_write_file(path, content)

            if success:
                self.logger.info("Model saved", model_id=model.id)
            else:
                self.logger.error("Failed to save model", model_id=model.id)

            return success

        except Exception as e:
            self.logger.error("Error saving model", model_id=model.id, error=str(e))
            return False
```

## Testing

### Test Organization

```
tests/
├── unit/                    # Unit tests
│   ├── test_services/       # Service layer tests
│   ├── test_repositories/   # Repository tests
│   ├── test_models/         # Model tests
│   └── test_utils/          # Utility tests
├── integration/             # Integration tests
│   ├── test_storage/        # Storage integration
│   └── test_jira/           # JIRA integration
├── fixtures/                # Test data
└── conftest.py             # Pytest configuration
```

### Writing Unit Tests

```python
# tests/unit/test_services/test_board_service.py
import pytest
from unittest.mock import Mock, MagicMock
from src.services.board_service import BoardService
from src.domain.entities.board import Board

class TestBoardService:
    @pytest.fixture
    def mock_repository(self):
        return Mock()

    @pytest.fixture
    def mock_validator(self):
        return Mock()

    @pytest.fixture
    def mock_logger(self):
        return Mock()

    @pytest.fixture
    def board_service(self, mock_repository, mock_validator, mock_logger):
        return BoardService(mock_repository, mock_validator, mock_logger)

    def test_create_board(self, board_service, mock_repository, mock_validator):
        # Arrange
        mock_validator.validate_board_name.return_value = True
        mock_repository.save_board.return_value = True

        # Act
        board = board_service.create_board("test-board")

        # Assert
        assert board is not None
        assert board.name == "test-board"
        mock_repository.save_board.assert_called_once()
        mock_validator.validate_board_name.assert_called_once_with("test-board")

    def test_create_board_invalid_name(self, board_service, mock_validator):
        # Arrange
        mock_validator.validate_board_name.return_value = False

        # Act
        board = board_service.create_board("")

        # Assert
        assert board is None
        mock_validator.validate_board_name.assert_called_once_with("")
```

### Integration Testing

```python
# tests/integration/test_storage/test_board_storage.py
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from src.infrastructure.storage.markdown_board_repository import MarkdownBoardRepository
from src.domain.entities.board import Board

class TestBoardStorageIntegration:
    @pytest.fixture
    def temp_dir(self):
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def board_repository(self, temp_dir):
        # Create test path resolver
        mock_path_resolver = Mock()
        mock_path_resolver.get_board_path.return_value = temp_dir / "test-board"

        # Create test logger
        mock_logger = Mock()

        return MarkdownBoardRepository(mock_path_resolver, mock_logger)

    def test_save_and_load_board(self, board_repository):
        # Create board
        board = Board(name="test-board")
        board.add_column("todo")
        board.add_column("done")

        # Save board
        success = board_repository.save_board(board)
        assert success

        # Load board
        loaded_board = board_repository.load_board("test-board")
        assert loaded_board is not None
        assert loaded_board.name == "test-board"
        assert len(loaded_board.columns) == 2
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_services/test_board_service.py

# Run with coverage
pytest --cov=src

# Run only integration tests
pytest tests/integration/

# Run with debugging
pytest -s -vv
```

## Code Quality

### Linting and Formatting

MKanban uses multiple tools for code quality:

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Type checking with mypy
mypy src/

# Linting with flake8
flake8 src/ tests/

# Modern linting with ruff
ruff check src/ tests/

# All together
make lint
```

### Pre-commit Hooks

Set up pre-commit hooks for automatic quality checks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Standards

1. **Type Hints**: Use type hints for all function signatures
2. **Docstrings**: Document public APIs with clear docstrings
3. **Error Handling**: Handle exceptions appropriately with logging
4. **Naming**: Use descriptive names following Python conventions
5. **Single Responsibility**: Keep functions and classes focused
6. **Dependency Injection**: Use the DI container for all dependencies

### Example Code Style

```python
from typing import Optional, List
from src.domain.entities.board import Board
from src.utils.logger_factory import ContextAwareLogger

class ExampleService:
    """Service demonstrating code quality standards."""

    def __init__(self, logger: ContextAwareLogger):
        """Initialize the service.

        Args:
            logger: Context-aware logger for this service
        """
        self._logger = logger

    def process_boards(self, board_names: List[str]) -> List[Board]:
        """Process multiple boards and return results.

        Args:
            board_names: List of board names to process

        Returns:
            List of successfully processed boards

        Raises:
            ProcessingError: If critical processing error occurs
        """
        self._logger.info("Processing boards", count=len(board_names))

        processed_boards: List[Board] = []

        for board_name in board_names:
            try:
                board = self._process_single_board(board_name)
                if board:
                    processed_boards.append(board)
                    self._logger.debug("Board processed", board=board_name)
                else:
                    self._logger.warning("Board processing failed", board=board_name)

            except Exception as e:
                self._logger.error("Error processing board",
                                 board=board_name,
                                 error=str(e))
                # Continue processing other boards
                continue

        self._logger.info("Board processing completed",
                         total=len(board_names),
                         successful=len(processed_boards))

        return processed_boards

    def _process_single_board(self, board_name: str) -> Optional[Board]:
        """Process a single board (private helper method)."""
        # Implementation details...
        pass
```

## Debugging

### Logging Setup

Enable debug logging for development:

```bash
# Set debug mode
export MKANBAN_DEBUG=true

# Run with debug logging
python main.py --data-dir ./dev-data
```

### Debugging Specific Components

```python
# Enable component-specific logging
logger = get_daemon_logger("board_service")
logger.set_context(board="debug-board")

# Debug with context
with logger.with_context(operation="debug_operation"):
    logger.debug("Debug information here")
```

### Common Debug Patterns

```python
# Debug service interactions
def debug_service_call(self, method_name: str, **kwargs):
    self._logger.debug(f"Calling {method_name}", **kwargs)
    result = getattr(self, method_name)(**kwargs)
    self._logger.debug(f"{method_name} result", result=result)
    return result

# Debug configuration
config = get_container().get(ConfigurationManager).config
logger.debug("Current configuration", config=config.model_dump())

# Debug dependency injection
container = get_container()
logger.debug("Container state",
             instances=list(container._instances.keys()),
             factories=list(container._factories.keys()))
```

## Performance Considerations

### Profiling

```python
# Profile with cProfile
python -m cProfile -o profile.stats main.py

# Analyze results
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"
```

### Memory Usage

```python
# Monitor memory usage
import tracemalloc

tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

### Performance Best Practices

1. **Lazy Loading**: Load data only when needed
2. **Caching**: Cache expensive operations
3. **Batch Operations**: Process multiple items together
4. **Efficient Data Structures**: Use appropriate data structures
5. **Async Operations**: Use async for I/O operations

## Contributing Guidelines

### Pull Request Process

1. **Fork and Branch**: Create a feature branch from main
2. **Implement Changes**: Follow coding standards and test thoroughly
3. **Add Tests**: Include unit and integration tests
4. **Update Documentation**: Update relevant documentation
5. **Run Quality Checks**: Ensure all linting and tests pass
6. **Submit PR**: Create pull request with clear description

### Commit Message Format

```
type(scope): brief description

Longer description explaining the change and its motivation.

Fixes #issue-number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Performance impact considered
- [ ] Security implications reviewed
- [ ] Error handling is appropriate

## Troubleshooting

### Common Development Issues

#### Import Errors
```bash
# Ensure Python path is correct
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use absolute imports throughout
```

#### Test Failures
```bash
# Run with verbose output
pytest -v --tb=short

# Run specific test
pytest tests/unit/test_services/test_board_service.py::TestBoardService::test_create_board
```

#### Configuration Issues
```bash
# Check configuration loading
python -c "from src.config.configuration_manager import get_config; print(get_config().config)"

# Verify environment variables
env | grep MKANBAN
```

#### Dependency Injection Issues
```bash
# Debug container state
python -c "
from src.core.dependency_container import get_container
container = get_container()
print('Instances:', list(container._instances.keys()))
print('Factories:', list(container._factories.keys()))
"
```

### Getting Help

1. **Check Documentation**: Start with docs in the `/docs` folder
2. **Run Tests**: Ensure tests pass on your system
3. **Check Issues**: Look for similar issues in the issue tracker
4. **Ask Questions**: Create an issue with the "question" label

## Continuous Integration

The project uses GitHub Actions for CI/CD:

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linting
      run: make lint

    - name: Run tests
      run: make test
```

This development guide should help you get started contributing to MKanban. The codebase follows clean architecture principles with comprehensive testing and quality standards.