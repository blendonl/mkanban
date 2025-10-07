"""Branch Service

Handles git branch operations for task-based workflows.
"""

import re
import subprocess
from pathlib import Path

from src.core.exceptions import MKanbanError
from src.infrastructure.git.repository import GitOperations
from src.utils.logger_factory import ContextAwareLogger


class BranchService:
    """Service for managing git branches based on task information."""

    def __init__(self, logger: ContextAwareLogger):
        self._logger = logger

    def format_task_title_as_branch(self, title: str, item_id: str = None) -> str:
        """Format a task title for use as a git branch name.

        Args:
            title: The task title to format
            item_id: Optional item ID to prefix the branch name

        Returns:
            A git-safe branch name (lowercase, hyphens, no special chars)
            Format: {item_id}-{title} if item_id provided, otherwise just {title}
        """
        # Convert to lowercase
        formatted = title.lower()

        # Replace spaces and special characters with hyphens
        formatted = re.sub(r'[^\w\-]', '-', formatted)

        # Replace multiple consecutive hyphens with single hyphen
        formatted = re.sub(r'-+', '-', formatted)

        # Remove leading/trailing hyphens
        formatted = formatted.strip('-')

        # Add item ID prefix if provided
        if item_id:
            # Make item_id lowercase for consistency
            id_prefix = item_id.lower()
            formatted = f"{id_prefix}-{formatted}"

        # Limit length to reasonable git branch name length (50 chars)
        if len(formatted) > 50:
            formatted = formatted[:50].rstrip('-')

        return formatted

    def checkout_or_create_branch(self, task_title: str, repo_path: Path, item_id: str = None) -> bool:
        """Create or checkout a git branch based on task title.

        Args:
            task_title: The task title to use for branch naming
            repo_path: Path to the git repository
            item_id: Optional item ID to prefix the branch name

        Returns:
            True if operation succeeded, False otherwise

        Raises:
            MKanbanError: If git operations fail
        """
        try:
            git_ops = GitOperations(repo_path)
        except MKanbanError as e:
            self._logger.error(f"Failed to initialize git repository: {e}")
            raise

        # Format the task title as a branch name
        branch_name = self.format_task_title_as_branch(task_title, item_id)

        if not branch_name:
            raise MKanbanError(f"Could not create valid branch name from task title: '{task_title}'")

        self._logger.info("Processing branch operation", branch=branch_name)

        # Check if branch exists
        branch_exists = git_ops.branch_exists(branch_name)

        try:
            if branch_exists:
                # Checkout existing branch
                self._logger.info("Checking out existing branch", branch=branch_name)
                result = self._run_git_command(["checkout", branch_name], repo_path)

                if result.returncode != 0:
                    raise MKanbanError(f"Failed to checkout branch '{branch_name}': {result.stderr}")

                self._logger.info("Successfully checked out branch", branch=branch_name)
            else:
                # Create new branch
                self._logger.info("Creating new branch", branch=branch_name)
                result = self._run_git_command(["checkout", "-b", branch_name], repo_path)

                if result.returncode != 0:
                    raise MKanbanError(f"Failed to create branch '{branch_name}': {result.stderr}")

                self._logger.info("Successfully created branch", branch=branch_name)

            return True

        except subprocess.TimeoutExpired:
            raise MKanbanError(f"Git operation timed out for branch '{branch_name}'")
        except Exception as e:
            raise MKanbanError(f"Unexpected error during branch operation: {e}")

    def _run_git_command(self, args: list[str], repo_path: Path) -> subprocess.CompletedProcess:
        """Run a git command in the repository directory.

        Args:
            args: Git command arguments (without 'git' prefix)
            repo_path: Path to the git repository

        Returns:
            CompletedProcess with command result
        """
        cmd = ["git"] + args
        return subprocess.run(
            cmd, cwd=repo_path, capture_output=True, text=True, timeout=30
        )