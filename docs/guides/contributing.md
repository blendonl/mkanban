# Contributing Guide

Thank you for your interest in contributing to MKanban! This guide will help you get started with contributing to the project.

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.9 or higher
- Git
- A GitHub account
- Basic familiarity with terminal/command line

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mkanban.git
   cd mkanban
   ```

3. **Set up the development environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Verify setup
   make test
   ```

4. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/mkanban.git
   ```

## Ways to Contribute

### 🐛 Bug Reports

Help us improve by reporting bugs:

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating issues
3. **Provide clear reproduction steps**
4. **Include system information** (OS, Python version, etc.)
5. **Add relevant logs** with `MKANBAN_DEBUG=true`

#### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g. Ubuntu 22.04]
- Python version: [e.g. 3.11.2]
- MKanban version: [e.g. 1.0.0]

**Additional Context**
Add any other context about the problem here.

**Logs**
```
Paste relevant logs here (run with MKANBAN_DEBUG=true)
```
```

### 💡 Feature Requests

Suggest new features or improvements:

1. **Check existing feature requests** to avoid duplicates
2. **Use the feature request template**
3. **Provide clear use cases** and motivation
4. **Consider implementation complexity**

#### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Describe the problem this feature would solve or the workflow it would improve.

**Proposed Solution**
Describe how you envision this feature working.

**Alternatives Considered**
Describe alternative solutions you've considered.

**Additional Context**
Add any other context, mockups, or examples.
```

### 📝 Documentation

Help improve our documentation:

- **Fix typos** and grammatical errors
- **Add missing documentation** for features
- **Improve existing documentation** clarity
- **Add examples** and use cases
- **Update outdated information**

### 🔧 Code Contributions

#### Types of Code Contributions

- **Bug fixes** - Fix reported issues
- **Feature implementation** - Add new functionality
- **Performance improvements** - Optimize existing code
- **Code quality** - Refactoring, type hints, etc.
- **Tests** - Add or improve test coverage

## Development Workflow

### 1. Planning Your Contribution

1. **Find or create an issue** describing what you want to work on
2. **Comment on the issue** to let others know you're working on it
3. **Discuss the approach** if it's a significant change

### 2. Creating a Branch

```bash
# Ensure you're on main and up to date
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 3. Making Changes

#### Code Standards

Follow these standards when writing code:

- **Type hints**: Use type hints for all function signatures
- **Docstrings**: Document public APIs with clear docstrings
- **Error handling**: Handle exceptions appropriately with logging
- **Testing**: Write tests for new functionality
- **Logging**: Use context-aware logging with relevant context

#### Code Style

```python
# Good example
from typing import Optional, List
from src.domain.entities.board import Board
from src.utils.logger_factory import ContextAwareLogger

class ExampleService:
    """Service demonstrating coding standards."""

    def __init__(self, logger: ContextAwareLogger):
        """Initialize the service.

        Args:
            logger: Context-aware logger for this service
        """
        self._logger = logger

    def process_boards(self, board_names: List[str]) -> List[Board]:
        """Process multiple boards and return successful results.

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

            except Exception as e:
                self._logger.error("Error processing board",
                                 board=board_name,
                                 error=str(e))
                continue

        self._logger.info("Processing completed",
                         total=len(board_names),
                         successful=len(processed_boards))

        return processed_boards
```

#### Testing Requirements

All code contributions must include appropriate tests:

```python
# Unit test example
def test_board_service_create_board():
    # Arrange
    mock_repository = Mock()
    mock_validator = Mock()
    mock_logger = Mock()

    mock_validator.validate_board_name.return_value = True
    mock_repository.save_board.return_value = True

    service = BoardService(mock_repository, mock_validator, mock_logger)

    # Act
    board = service.create_board("test-board")

    # Assert
    assert board is not None
    assert board.name == "test-board"
    mock_repository.save_board.assert_called_once()
```

### 4. Quality Checks

Before committing, run all quality checks:

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# All checks together
make check
```

#### Linting Tools

We use multiple tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style and error checking
- **mypy**: Type checking
- **ruff**: Modern Python linting

### 5. Committing Changes

#### Commit Message Format

Use conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(services): add board duplication functionality

Adds the ability to duplicate existing boards with all their
columns and items. Useful for creating similar project boards.

Fixes #123
```

```
fix(storage): handle file permission errors gracefully

Previously, the app would crash when encountering permission
errors. Now it logs the error and continues operation.
```

### 6. Creating a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a pull request** on GitHub:
   - Use a clear, descriptive title
   - Fill out the PR template completely
   - Link related issues
   - Add screenshots for UI changes

#### Pull Request Template

```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #(issue number)

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Screenshots (if applicable)
Add screenshots here.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review performed
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

### 7. Code Review Process

1. **Automated checks** will run (CI/CD)
2. **Maintainers will review** your code
3. **Address feedback** by making additional commits
4. **Once approved**, your PR will be merged

#### Review Criteria

Reviewers will check for:

- ✅ **Functionality**: Does it work as intended?
- ✅ **Code quality**: Is it well-written and maintainable?
- ✅ **Tests**: Are there adequate tests?
- ✅ **Documentation**: Is it properly documented?
- ✅ **Performance**: Does it impact performance?
- ✅ **Security**: Are there security implications?
- ✅ **Compatibility**: Does it break existing functionality?

## Specific Contribution Areas

### 🎨 UI/UX Improvements

- **Textual widgets**: Improve existing TUI components
- **Themes**: Add new themes or improve existing ones
- **Accessibility**: Improve keyboard navigation and screen reader support
- **User experience**: Streamline workflows and interactions

### 🔌 Integration Features

- **Git integration**: Improve branch detection and automation
- **JIRA integration**: Enhance JIRA synchronization
- **External tools**: Add support for other project management tools
- **Export/import**: Add data export/import capabilities

### ⚡ Performance Improvements

- **Large datasets**: Optimize for boards with many items
- **Memory usage**: Reduce memory footprint
- **Startup time**: Improve application startup performance
- **File operations**: Optimize file I/O operations

### 🔧 Developer Experience

- **Development tools**: Improve development workflow
- **Testing infrastructure**: Enhance testing capabilities
- **Documentation**: Improve developer documentation
- **Code quality**: Add better linting rules and tools

## Project-Specific Guidelines

### Architecture Principles

Follow these architectural principles:

1. **Dependency Injection**: Use the DI container for all dependencies
2. **Single Responsibility**: Each class should have one clear purpose
3. **Repository Pattern**: Separate storage concerns from business logic
4. **Configuration-Driven**: Make behavior configurable
5. **Context-Aware Logging**: Include relevant context in all log messages

### Adding New Features

When adding new features:

1. **Start with the domain model** if new entities are needed
2. **Add repository interfaces** for storage needs
3. **Implement services** for business logic
4. **Register in DI container** for dependency management
5. **Add configuration options** if needed
6. **Update UI components** for user interaction
7. **Write comprehensive tests**

### Working with Existing Code

When modifying existing code:

1. **Understand the current architecture** before making changes
2. **Maintain backward compatibility** when possible
3. **Update related tests** when changing behavior
4. **Update documentation** when changing APIs
5. **Consider migration path** for breaking changes

## Getting Help

### Resources

- **Documentation**: Start with docs in the `/docs` folder
- **Code Examples**: Look at existing code for patterns
- **Tests**: Check test files for usage examples
- **Issues**: Search existing issues for similar problems

### Communication

- **GitHub Issues**: For bugs and feature requests
- **Pull Request Comments**: For code-specific questions
- **Discussions**: For general questions and ideas

### Mentorship

New contributors are welcome! If you're new to:

- **Open source**: We'll help you learn the process
- **Python**: We can guide you on Python best practices
- **The codebase**: We'll help you understand the architecture

Just ask in the issues or discussions!

## Recognition

Contributors are recognized in several ways:

- **Contributors list**: Added to the project contributors
- **Release notes**: Significant contributions mentioned in releases
- **Documentation**: Featured in contributor spotlights

## Code of Conduct

Please note that this project follows a Code of Conduct. By participating, you agree to uphold this code:

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Be patient** with new contributors
- **Focus on the project** goals and quality

## License

By contributing to MKanban, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to MKanban! Your contributions help make this tool better for everyone.