import shutil
from pathlib import Path
from typing import List, Optional, Generator
from src.utils.logger_factory import ContextAwareLogger


class FileOperations:
    def __init__(self, logger: ContextAwareLogger):
        self.logger = logger

    def ensure_directory_exists(self, path: Path) -> Path:
        """Ensure directory exists, creating parent directories as needed."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {path}")
            return path
        except Exception as e:
            self.logger.error(f"Failed to create directory: {path} - {e}")
            raise

    def safe_delete_file(self, file_path: Path) -> bool:
        """Safely delete a file with proper error handling."""
        if not file_path.exists():
            self.logger.warning(f"Cannot delete non-existent file: {file_path}")
            return False

        try:
            file_path.unlink()
            self.logger.debug(f"Successfully deleted file: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file: {file_path} - {e}")
            return False

    def safe_delete_directory(self, dir_path: Path) -> bool:
        """Safely delete a directory and all its contents."""
        if not dir_path.exists():
            self.logger.warning(f"Cannot delete non-existent directory: {dir_path}")
            return False

        if not dir_path.is_dir():
            self.logger.warning(f"Path is not a directory: {dir_path}")
            return False

        try:
            shutil.rmtree(dir_path)
            self.logger.debug(f"Successfully deleted directory: {dir_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete directory: {dir_path} - {e}")
            return False

    def safe_rename_file(self, old_path: Path, new_path: Path) -> bool:
        """Safely rename/move a file with proper error handling."""
        if not old_path.exists():
            self.logger.warning(f"Cannot rename non-existent file: {old_path}")
            return False

        try:
            # Ensure target directory exists
            self.ensure_directory_exists(new_path.parent)
            old_path.rename(new_path)
            self.logger.debug(f"Successfully renamed file: {old_path} -> {new_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to rename file: {old_path} -> {new_path} - {e}")
            return False

    def find_files_by_pattern(self, directory: Path, pattern: str) -> List[Path]:
        """Find all files matching a pattern in a directory."""
        if not directory.exists() or not directory.is_dir():
            self.logger.warning(f"Directory does not exist: {directory}")
            return []

        try:
            files = list(directory.glob(pattern))
            self.logger.debug(f"Found {len(files)} files matching '{pattern}' in {directory}")
            return files
        except Exception as e:
            self.logger.error(f"Failed to search for files in {directory}: {e}")
            return []

    def find_files_recursively(self, directory: Path, pattern: str) -> List[Path]:
        """Find all files matching a pattern recursively in a directory tree."""
        if not directory.exists() or not directory.is_dir():
            self.logger.warning(f"Directory does not exist: {directory}")
            return []

        try:
            files = list(directory.rglob(pattern))
            self.logger.debug(f"Found {len(files)} files matching '{pattern}' recursively in {directory}")
            return files
        except Exception as e:
            self.logger.error(f"Failed to search recursively for files in {directory}: {e}")
            return []

    def get_unique_filename(self, directory: Path, base_name: str, extension: str = "", max_attempts: int = 100) -> Path:
        """Generate a unique filename by appending numbers if file exists."""
        file_path = directory / f"{base_name}{extension}"

        if not file_path.exists():
            return file_path

        for i in range(1, max_attempts + 1):
            file_path = directory / f"{base_name}_{i}{extension}"
            if not file_path.exists():
                self.logger.debug(f"Generated unique filename: {file_path}")
                return file_path

        # If we've exhausted attempts, use timestamp
        import time
        timestamp = int(time.time())
        file_path = directory / f"{base_name}_{timestamp}{extension}"
        self.logger.warning(f"Used timestamp for unique filename: {file_path}")
        return file_path

    def copy_file(self, source: Path, destination: Path) -> bool:
        """Copy a file to a new location."""
        if not source.exists():
            self.logger.warning(f"Cannot copy non-existent file: {source}")
            return False

        try:
            self.ensure_directory_exists(destination.parent)
            shutil.copy2(source, destination)
            self.logger.debug(f"Successfully copied file: {source} -> {destination}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy file: {source} -> {destination} - {e}")
            return False

    def move_file(self, source: Path, destination: Path) -> bool:
        """Move a file to a new location."""
        if not source.exists():
            self.logger.warning(f"Cannot move non-existent file: {source}")
            return False

        try:
            self.ensure_directory_exists(destination.parent)
            shutil.move(str(source), str(destination))
            self.logger.debug(f"Successfully moved file: {source} -> {destination}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to move file: {source} -> {destination} - {e}")
            return False

    def get_file_size(self, file_path: Path) -> Optional[int]:
        """Get file size in bytes."""
        if not file_path.exists():
            return None

        try:
            return file_path.stat().st_size
        except Exception as e:
            self.logger.error(f"Failed to get file size: {file_path} - {e}")
            return None

    def is_file_writable(self, file_path: Path) -> bool:
        """Check if a file is writable."""
        try:
            return file_path.exists() and file_path.is_file() and file_path.stat().st_mode & 0o200
        except Exception:
            return False

    def cleanup_empty_directories(self, root_directory: Path) -> int:
        """Remove empty directories recursively. Returns count of removed directories."""
        if not root_directory.exists() or not root_directory.is_dir():
            return 0

        removed_count = 0

        # Walk directories bottom-up to handle nested empty directories
        for dir_path in reversed(list(root_directory.rglob("*"))):
            if dir_path.is_dir():
                try:
                    # Try to remove if empty
                    dir_path.rmdir()
                    removed_count += 1
                    self.logger.debug(f"Removed empty directory: {dir_path}")
                except OSError:
                    # Directory not empty, skip
                    pass
                except Exception as e:
                    self.logger.error(f"Failed to remove directory: {dir_path} - {e}")

        if removed_count > 0:
            self.logger.info(f"Cleaned up {removed_count} empty directories")

        return removed_count