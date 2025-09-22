import pytest
from unittest.mock import patch

from src.services.board_service import BoardService
from src.core.exceptions import BoardNotFoundError, ValidationError
from tests.fixtures.entity_factories import BoardFactory
from tests.fixtures.mock_factories import MockRepositoryFactory, MockServiceFactory


class TestBoardService:
    """Test cases for the BoardService class."""

    def setup_method(self):
        """Set up test dependencies."""
        self.mock_repository = MockRepositoryFactory.create_board_repository()
        self.mock_validator = MockServiceFactory.create_validation_service()
        self.mock_logger = MockServiceFactory.create_logger()

        self.service = BoardService(
            board_repository=self.mock_repository,
            validation_service=self.mock_validator,
            logger=self.mock_logger
        )

    def test_get_all_boards(self):
        """Test retrieving all boards."""
        boards = [BoardFactory.create(name="Board 1"), BoardFactory.create(name="Board 2")]
        self.mock_repository.load_all_boards.return_value = boards

        result = self.service.get_all_boards()

        assert result == boards
        self.mock_repository.load_all_boards.assert_called_once()

    def test_get_board_by_id_success(self):
        """Test successfully retrieving a board by ID."""
        board = BoardFactory.create(name="Test Board")
        self.mock_repository.load_board_by_id.return_value = board

        result = self.service.get_board_by_id(board.id)

        assert result == board
        self.mock_repository.load_board_by_id.assert_called_once_with(board.id)
        self.mock_logger.debug.assert_called_once()
        self.mock_logger.info.assert_called_once()

    def test_get_board_by_id_not_found(self):
        """Test retrieving a non-existent board by ID."""
        self.mock_repository.load_board_by_id.return_value = None

        with pytest.raises(BoardNotFoundError) as exc_info:
            self.service.get_board_by_id("non-existent-id")

        assert "Board with id 'non-existent-id' not found" in str(exc_info.value)
        self.mock_logger.warning.assert_called_once()

    def test_get_board_by_name_success(self):
        """Test successfully retrieving a board by name."""
        board = BoardFactory.create(name="Test Board")
        self.mock_repository.load_board_by_name.return_value = board

        result = self.service.get_board_by_name("Test Board")

        assert result == board
        self.mock_repository.load_board_by_name.assert_called_once_with("Test Board")
        self.mock_logger.debug.assert_called_once()
        self.mock_logger.info.assert_called_once()

    def test_get_board_by_name_not_found(self):
        """Test retrieving a non-existent board by name."""
        self.mock_repository.load_board_by_name.return_value = None

        with pytest.raises(BoardNotFoundError) as exc_info:
            self.service.get_board_by_name("Non-existent Board")

        assert "Board with name 'Non-existent Board' not found" in str(exc_info.value)
        self.mock_logger.warning.assert_called_once()

    def test_create_board_success(self):
        """Test successfully creating a new board."""
        # Mock validation passes
        self.mock_validator.validate_board_name.return_value = None
        # Mock no existing board
        self.mock_repository.load_board_by_name.return_value = None

        result = self.service.create_board("New Board", "A new test board")

        assert result.name == "New Board"
        assert result.description == "A new test board"
        self.mock_validator.validate_board_name.assert_called_once_with("New Board")
        self.mock_repository.load_board_by_name.assert_called_once_with("New Board")
        self.mock_repository.save_board.assert_called_once()
        self.mock_logger.info.assert_called()

    def test_create_board_validation_failure(self):
        """Test creating a board with invalid name."""
        validation_error = ValidationError("Board name cannot be empty")
        self.mock_validator.validate_board_name.side_effect = validation_error

        with pytest.raises(ValidationError):
            self.service.create_board("")

        self.mock_validator.validate_board_name.assert_called_once_with("")
        self.mock_repository.save_board.assert_not_called()

    def test_create_board_already_exists(self):
        """Test creating a board that already exists."""
        existing_board = BoardFactory.create(name="Existing Board")
        self.mock_repository.load_board_by_name.return_value = existing_board

        with pytest.raises(ValidationError) as exc_info:
            self.service.create_board("Existing Board")

        assert "Board with name '{name}' already exists" in str(exc_info.value)
        self.mock_logger.warning.assert_called_once()
        self.mock_repository.save_board.assert_not_called()

    def test_save_board_success(self):
        """Test successfully saving a board."""
        board = BoardFactory.create()

        self.service.save_board(board)

        self.mock_validator.validate_board.assert_called_once_with(board)
        self.mock_repository.save_board.assert_called_once_with(board)
        self.mock_logger.debug.assert_called_once()
        self.mock_logger.info.assert_called_once()

    def test_save_board_validation_failure(self):
        """Test saving an invalid board."""
        board = BoardFactory.create()
        validation_error = ValidationError("Board must have at least one column")
        self.mock_validator.validate_board.side_effect = validation_error

        with pytest.raises(ValidationError):
            self.service.save_board(board)

        self.mock_validator.validate_board.assert_called_once_with(board)
        self.mock_repository.save_board.assert_not_called()

    def test_delete_board(self):
        """Test deleting a board."""
        board_id = "board-to-delete"
        self.mock_repository.delete_board.return_value = True

        result = self.service.delete_board(board_id)

        assert result is True
        self.mock_repository.delete_board.assert_called_once_with(board_id)

    def test_add_column_to_board_success(self):
        """Test successfully adding a column to a board."""
        board = BoardFactory.create()

        result = self.service.add_column_to_board(board, "New Column", 1)

        assert result.name == "New Column"
        assert result.position == 1
        assert result in board.columns
        self.mock_validator.validate_column_name.assert_called_once_with("New Column")
        self.mock_logger.info.assert_called()

    def test_add_column_to_board_validation_failure(self):
        """Test adding a column with invalid name."""
        board = BoardFactory.create()
        validation_error = ValidationError("Column name cannot be empty")
        self.mock_validator.validate_column_name.side_effect = validation_error

        with pytest.raises(ValidationError):
            self.service.add_column_to_board(board, "")

        self.mock_validator.validate_column_name.assert_called_once_with("")

    def test_add_column_to_board_duplicate_name(self):
        """Test adding a column with duplicate name."""
        board = BoardFactory.create()
        existing_column = board.columns[0]

        with pytest.raises(ValidationError) as exc_info:
            self.service.add_column_to_board(board, existing_column.name.upper())

        assert "Column '{column_name}' already exists in board" in str(exc_info.value)
        self.mock_logger.warning.assert_called_once()

    def test_remove_column_from_board_success(self):
        """Test successfully removing an empty column."""
        board = BoardFactory.create()
        column_to_remove = board.columns[0]
        # Ensure column is empty
        column_to_remove.items = []

        result = self.service.remove_column_from_board(board, column_to_remove.id)

        assert result is True
        assert column_to_remove not in board.columns

    def test_remove_column_from_board_not_found(self):
        """Test removing a non-existent column."""
        board = BoardFactory.create()

        result = self.service.remove_column_from_board(board, "non-existent-id")

        assert result is False

    def test_remove_column_from_board_with_items(self):
        """Test removing a column that contains items."""
        board = BoardFactory.create_with_items(item_count_per_column=2)
        column_to_remove = board.columns[0]

        with pytest.raises(ValidationError) as exc_info:
            self.service.remove_column_from_board(board, column_to_remove.id)

        assert "Cannot delete column that contains items" in str(exc_info.value)

    def test_list_board_names(self):
        """Test listing all board names."""
        board_names = ["Board 1", "Board 2", "Board 3"]
        self.mock_repository.list_board_names.return_value = board_names

        result = self.service.list_board_names()

        assert result == board_names
        self.mock_repository.list_board_names.assert_called_once()

    def test_get_or_create_sample_board_existing(self):
        """Test getting an existing sample board."""
        existing_board = BoardFactory.create(name="sample")
        self.mock_repository.load_board_by_name.return_value = existing_board

        with patch.object(self.service, 'get_board_by_name', return_value=existing_board):
            result = self.service.get_or_create_sample_board("sample")

        assert result == existing_board
        self.mock_repository.create_sample_board.assert_not_called()

    def test_get_or_create_sample_board_new(self):
        """Test creating a new sample board when it doesn't exist."""
        sample_board = BoardFactory.create(name="default")

        # Mock the exception and repository methods
        with patch.object(self.service, 'get_board_by_name', side_effect=BoardNotFoundError("Not found")):
            self.mock_repository.create_sample_board.return_value = sample_board

            result = self.service.get_or_create_sample_board("default")

        assert result == sample_board
        self.mock_repository.create_sample_board.assert_called_once_with("default")
        self.mock_repository.save_board.assert_called_once_with(sample_board)

    def test_service_logging_integration(self):
        """Test that service methods log appropriately."""
        board = BoardFactory.create()
        self.mock_repository.load_board_by_id.return_value = board

        self.service.get_board_by_id(board.id)

        # Verify logging calls
        self.mock_logger.debug.assert_called_with("Loading board by id", board=board.id)
        self.mock_logger.info.assert_called_with("Successfully loaded board", board=board.name)

    def test_service_with_complex_scenario(self):
        """Test service behavior in a complex scenario."""
        # Setup initial state
        boards = [
            BoardFactory.create(name="Project Alpha"),
            BoardFactory.create(name="Project Beta")
        ]
        self.mock_repository.load_all_boards.return_value = boards
        self.mock_repository.load_board_by_name.side_effect = lambda name: next(
            (b for b in boards if b.name == name), None
        )

        # Test listing boards
        all_boards = self.service.get_all_boards()
        assert len(all_boards) == 2

        # Test retrieving specific board
        alpha_board = self.service.get_board_by_name("Project Alpha")
        assert alpha_board.name == "Project Alpha"

        # Test adding column to board
        new_column = self.service.add_column_to_board(alpha_board, "Testing", 2)
        assert new_column.name == "Testing"
        assert new_column in alpha_board.columns

        # Test saving the modified board
        self.service.save_board(alpha_board)
        self.mock_repository.save_board.assert_called_with(alpha_board)

        # Verify all validations were called
        self.mock_validator.validate_column_name.assert_called_with("Testing")
        self.mock_validator.validate_board.assert_called_with(alpha_board)