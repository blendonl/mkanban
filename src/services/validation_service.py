from core.exceptions import ValidationError
from domain.entities.board import Board
from domain.entities.column import Column


class ValidationService:
    def validate_board_name(self, name: str) -> None:
        if not name or not name.strip():
            raise ValidationError("Board name cannot be empty")
        
        if len(name) > 100:
            raise ValidationError("Board name cannot exceed 100 characters")
        
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in name for char in invalid_chars):
            raise ValidationError(f"Board name contains invalid characters: {', '.join(invalid_chars)}")

    def validate_column_name(self, name: str) -> None:
        if not name or not name.strip():
            raise ValidationError("Column name cannot be empty")
        
        if len(name) > 50:
            raise ValidationError("Column name cannot exceed 50 characters")

    def validate_item_title(self, title: str) -> None:
        if not title or not title.strip():
            raise ValidationError("Item title cannot be empty")
        
        if len(title) > 200:
            raise ValidationError("Item title cannot exceed 200 characters")

    def validate_board(self, board: Board) -> None:
        self.validate_board_name(board.name)
        
        if len(board.columns) == 0:
            raise ValidationError("Board must have at least one column")
        
        column_names = [col.name.lower() for col in board.columns]
        if len(column_names) != len(set(column_names)):
            raise ValidationError("Board cannot have duplicate column names")
        
        positions = [col.position for col in board.columns if col.position is not None]
        if len(positions) != len(set(positions)):
            raise ValidationError("Board cannot have columns with duplicate positions")

    def validate_column_limit(self, limit: int | None) -> None:
        if limit is not None and limit < 1:
            raise ValidationError("Column limit must be at least 1")

    def validate_column_capacity(self, column: Column) -> None:
        if column.limit is not None and len(column.items) >= column.limit:
            raise ValidationError(f"Column '{column.name}' is at capacity ({column.limit} items). Cannot add more items.")