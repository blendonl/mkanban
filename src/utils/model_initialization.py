from pathlib import Path
from typing import Optional, Union
from src.utils.string_utils import generate_id_from_name


class ModelInitializer:
    """Utility class for common model initialization patterns."""

    @staticmethod
    def initialize_id_from_file_path(
        current_id: Optional[str],
        file_path: Optional[Union[str, Path]],
        name: Optional[str] = None,
        fallback: str = "unnamed"
    ) -> str:
        """
        Initialize ID using common pattern:
        1. Use current_id if provided
        2. Extract from file_path if available
        3. Generate from name if provided
        4. Use fallback
        """
        if current_id:
            return current_id

        if file_path:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            if path.is_file():
                # For files, use parent directory name
                return path.parent.name
            elif path.is_dir():
                # For directories, use directory name
                return path.name

        if name:
            generated_id = generate_id_from_name(name)
            if generated_id:
                return generated_id

        return fallback

    @staticmethod
    def initialize_name_from_file_path(
        current_name: Optional[str],
        file_path: Optional[Union[str, Path]],
        id_value: Optional[str] = None
    ) -> str:
        """
        Initialize name using common pattern:
        1. Use current_name if provided and different from id
        2. Extract and format from file_path if available
        3. Use id_value as fallback
        """
        if current_name and (not id_value or current_name != id_value):
            return current_name

        if file_path:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            if path.is_file():
                # For files, use parent directory name
                dir_name = path.parent.name
            elif path.is_dir():
                # For directories, use directory name
                dir_name = path.name
            else:
                dir_name = None

            if dir_name:
                # Format directory name to human-readable
                return dir_name.replace("-", " ").replace("_", " ").title()

        if id_value:
            return id_value.replace("-", " ").replace("_", " ").title()

        return "Unnamed"

    @staticmethod
    def ensure_position_value(current_position: Optional[int], default_position: int = 0) -> int:
        """Ensure position has a valid value."""
        return current_position if current_position is not None else default_position

    @staticmethod
    def consolidate_entity_initialization(
        entity_type: str,
        current_id: Optional[str] = None,
        current_name: Optional[str] = None,
        file_path: Optional[Union[str, Path]] = None,
        position: Optional[int] = None,
        fallback_id: Optional[str] = None
    ) -> dict:
        """
        Consolidate common entity initialization logic.
        Returns a dictionary with 'id', 'name', and 'position' keys.
        """
        fallback = fallback_id or f"unnamed_{entity_type}"

        # Initialize ID
        entity_id = ModelInitializer.initialize_id_from_file_path(
            current_id, file_path, current_name, fallback
        )

        # Initialize name
        entity_name = ModelInitializer.initialize_name_from_file_path(
            current_name, file_path, entity_id
        )

        # Initialize position
        entity_position = ModelInitializer.ensure_position_value(position, 0)

        return {
            "id": entity_id,
            "name": entity_name,
            "position": entity_position
        }