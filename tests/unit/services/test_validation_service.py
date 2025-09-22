import pytest

from src.services.validation_service import ValidationService
from src.core.exceptions import ValidationError
from tests.fixtures.entity_factories import BoardFactory, ColumnFactory
from tests.fixtures.test_data import VALIDATION_TEST_CASES


class TestValidationService:
    """Test cases for the ValidationService class."""

    def setup_method(self):
        """Set up test dependencies."""
        self.service = ValidationService()

    def test_validate_board_name_valid(self):
        """Test validation with valid board names."""
        for valid_name in VALIDATION_TEST_CASES["valid_board_names"]:
            self.service.validate_board_name(valid_name)  # Should not raise

    def test_validate_board_name_empty(self):
        """Test validation with empty board name."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_board_name("")

        assert "Board name cannot be empty" in str(exc_info.value)

    def test_validate_board_name_whitespace_only(self):
        """Test validation with whitespace-only board name."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_board_name("   ")

        assert "Board name cannot be empty" in str(exc_info.value)

    def test_validate_board_name_too_long(self):
        """Test validation with board name exceeding length limit."""
        long_name = "a" * 101  # Exceeds 100 character limit

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_board_name(long_name)

        assert "Board name cannot exceed 100 characters" in str(exc_info.value)

    def test_validate_board_name_invalid_characters(self):
        """Test validation with invalid characters in board name."""
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]

        for char in invalid_chars:
            board_name = f"Board{char}Name"
            with pytest.raises(ValidationError) as exc_info:
                self.service.validate_board_name(board_name)

            assert "Board name contains invalid characters" in str(exc_info.value)

    def test_validate_column_name_valid(self):
        """Test validation with valid column names."""
        for valid_name in VALIDATION_TEST_CASES["valid_column_names"]:
            self.service.validate_column_name(valid_name)  # Should not raise

    def test_validate_column_name_empty(self):
        """Test validation with empty column name."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_column_name("")

        assert "Column name cannot be empty" in str(exc_info.value)

    def test_validate_column_name_whitespace_only(self):
        """Test validation with whitespace-only column name."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_column_name("   ")

        assert "Column name cannot be empty" in str(exc_info.value)

    def test_validate_column_name_too_long(self):
        """Test validation with column name exceeding length limit."""
        long_name = "a" * 51  # Exceeds 50 character limit

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_column_name(long_name)

        assert "Column name cannot exceed 50 characters" in str(exc_info.value)

    def test_validate_item_title_valid(self):
        """Test validation with valid item titles."""
        for valid_title in VALIDATION_TEST_CASES["valid_item_titles"]:
            self.service.validate_item_title(valid_title)  # Should not raise

    def test_validate_item_title_empty(self):
        """Test validation with empty item title."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_item_title("")

        assert "Item title cannot be empty" in str(exc_info.value)

    def test_validate_item_title_whitespace_only(self):
        """Test validation with whitespace-only item title."""
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_item_title("   ")

        assert "Item title cannot be empty" in str(exc_info.value)

    def test_validate_item_title_too_long(self):
        """Test validation with item title exceeding length limit."""
        long_title = "a" * 201  # Exceeds 200 character limit

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_item_title(long_title)

        assert "Item title cannot exceed 200 characters" in str(exc_info.value)

    def test_validate_board_valid(self):
        """Test validation with a valid board."""
        board = BoardFactory.create()

        self.service.validate_board(board)  # Should not raise

    def test_validate_board_invalid_name(self):
        """Test validation with board having invalid name."""
        board = BoardFactory.create(name="")

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_board(board)

        assert "Board name cannot be empty" in str(exc_info.value)

    def test_validate_board_no_columns(self):
        """Test validation with board having no columns."""
        board = BoardFactory.create_empty()

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_board(board)

        assert "Board must have at least one column" in str(exc_info.value)

    def test_validate_board_duplicate_column_names(self):
        """Test validation with board having duplicate column names."""
        board = BoardFactory.create_empty()
        board.add_column("To Do", 0)
        board.add_column("to do", 1)  # Case-insensitive duplicate

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_board(board)

        assert "Board cannot have duplicate column names" in str(exc_info.value)

    def test_validate_board_duplicate_column_positions(self):
        """Test validation with board having duplicate column positions."""
        board = BoardFactory.create_empty()
        column1 = ColumnFactory.create(name="Column 1", position=1)
        column2 = ColumnFactory.create(name="Column 2", position=1)
        board.columns = [column1, column2]

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_board(board)

        assert "Board cannot have columns with duplicate positions" in str(exc_info.value)

    def test_validate_column_limit_valid(self):
        """Test validation with valid column limits."""
        valid_limits = [1, 5, 10, 100]

        for limit in valid_limits:
            self.service.validate_column_limit(limit)  # Should not raise

    def test_validate_column_limit_none(self):
        """Test validation with no column limit (None)."""
        self.service.validate_column_limit(None)  # Should not raise

    def test_validate_column_limit_invalid(self):
        """Test validation with invalid column limits."""
        invalid_limits = [0, -1, -10]

        for limit in invalid_limits:
            with pytest.raises(ValidationError) as exc_info:
                self.service.validate_column_limit(limit)

            assert "Column limit must be at least 1" in str(exc_info.value)

    def test_validate_column_capacity_under_limit(self):
        """Test validation with column under capacity."""
        column = ColumnFactory.create_with_items(item_count=3)
        column.limit = 5

        self.service.validate_column_capacity(column)  # Should not raise

    def test_validate_column_capacity_at_limit(self):
        """Test validation with column at capacity."""
        column = ColumnFactory.create_with_items(item_count=3)
        column.limit = 3

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_column_capacity(column)

        assert f"Column '{column.name}' is at capacity (3 items)" in str(exc_info.value)

    def test_validate_column_capacity_over_limit(self):
        """Test validation with column over capacity."""
        column = ColumnFactory.create_with_items(item_count=5)
        column.limit = 3

        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_column_capacity(column)

        assert f"Column '{column.name}' is at capacity (3 items)" in str(exc_info.value)

    def test_validate_column_capacity_no_limit(self):
        """Test validation with column having no limit."""
        column = ColumnFactory.create_with_items(item_count=100)
        column.limit = None

        self.service.validate_column_capacity(column)  # Should not raise

    def test_validation_edge_cases(self):
        """Test validation with edge cases."""
        # Board name at exactly 100 characters
        max_name = "a" * 100
        self.service.validate_board_name(max_name)  # Should not raise

        # Column name at exactly 50 characters
        max_column = "a" * 50
        self.service.validate_column_name(max_column)  # Should not raise

        # Item title at exactly 200 characters
        max_title = "a" * 200
        self.service.validate_item_title(max_title)  # Should not raise

    def test_validation_with_unicode_characters(self):
        """Test validation with unicode characters."""
        unicode_names = [
            "Таблица проекта",  # Cyrillic
            "プロジェクトボード",  # Japanese
            "项目看板",  # Chinese
            "Board with émojis 🚀",  # Emojis
        ]

        for name in unicode_names:
            if len(name) <= 100:  # Within length limit
                self.service.validate_board_name(name)  # Should not raise

            if len(name) <= 50:  # Within column limit
                self.service.validate_column_name(name)  # Should not raise

            if len(name) <= 200:  # Within item limit
                self.service.validate_item_title(name)  # Should not raise

    def test_validation_complex_board_scenario(self):
        """Test validation in a complex board scenario."""
        # Create a valid complex board
        board = BoardFactory.create(name="Complex Project Board")

        # Add columns with varying positions
        board.add_column("Backlog", 0)
        board.add_column("In Progress", 1)
        board.add_column("Review", 2)
        board.add_column("Done", 3)

        # Should validate successfully
        self.service.validate_board(board)

        # Test column capacity validation
        review_column = board.get_column_by_id("review")
        if review_column:
            review_column.limit = 2
            # Add items up to limit
            for i in range(2):
                review_column.items.append(
                    type('MockItem', (), {'id': f'item-{i}'})()
                )

            # Should be at capacity
            with pytest.raises(ValidationError):
                self.service.validate_column_capacity(review_column)

    def test_validation_error_messages_specificity(self):
        """Test that validation error messages are specific and helpful."""
        # Test board name with multiple invalid characters
        with pytest.raises(ValidationError) as exc_info:
            self.service.validate_board_name("Board/With\\Invalid*Chars")

        error_message = str(exc_info.value)
        assert "invalid characters" in error_message
        # Should list the invalid characters
        assert "/" in error_message or "\\" in error_message or "*" in error_message

    def test_validation_service_stateless(self):
        """Test that validation service is stateless."""
        # Multiple validations should not affect each other
        self.service.validate_board_name("Board 1")
        self.service.validate_column_name("Column 1")
        self.service.validate_item_title("Item 1")

        # Should still work with different inputs
        self.service.validate_board_name("Board 2")
        self.service.validate_column_name("Column 2")
        self.service.validate_item_title("Item 2")

        # Invalid validation should not affect subsequent valid ones
        with pytest.raises(ValidationError):
            self.service.validate_board_name("")

        self.service.validate_board_name("Valid Board")  # Should still work