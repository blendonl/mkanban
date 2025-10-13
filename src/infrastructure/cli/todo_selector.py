import subprocess
import re
import click
from pathlib import Path
from typing import Optional, List, Tuple
from src.core.exceptions import MKanbanError, BoardNotFoundError
from src.core.dependency_container import DependencyContainer
from src.services.board_service import BoardService
from src.services.item_service import ItemService
from src.infrastructure.git.repository import GitOperations
from src.infrastructure.tmux.session_manager import TmuxSessionManager
from src.domain.entities.item import Item
from src.domain.entities.board import Board


class TodoSelector:
    def __init__(self, container: DependencyContainer, boards_path: Optional[Path] = None):
        self.container = container
        self.boards_path = boards_path
        self._board_service = container.get(BoardService)
        self._item_service = container.get(ItemService)
        self._tmux_manager = TmuxSessionManager()

    def run_todo_selector(self, selector_command: str, board_name: str) -> None:
        """Main entry point for the todo selector functionality"""
        session = self._tmux_manager.get_active_session()
        try:
            # Get the board using the same logic as other CLI commands
            try:
                board = self._board_service.get_board_by_name(session.name)
            except BoardNotFoundError:
                click.echo(f"Error: Board '{session.name}' not found")
                available_boards = self._board_service.list_board_names()
                if available_boards:
                    click.echo(f"Available boards: {', '.join(available_boards)}")
                return

            # Get all todos from the board
            todos = self._get_all_todos(board)
            if not todos:
                click.echo("No todos found in the current board")
                return

            # Format todos for display
            formatted_todos = self._format_todos_for_display(todos)

            # Execute selector command
            selected_todo = self._execute_selector_command(
                selector_command, formatted_todos
            )
            if not selected_todo:
                click.echo("No todo selected")
                return

            # Process the selected todo
            self._process_selected_todo(selected_todo, todos, board)

        except MKanbanError as e:
            click.echo(f"Error: {e}")
        except Exception as e:
            click.echo(f"Unexpected error: {e}")

    def _get_all_todos(self, board: Board) -> List[Item]:
        """Get all todos from all columns in the board"""
        todos = []
        for column in board.columns:
            todos.extend(column.items)
        return todos

    def _format_todos_for_display(self, todos: List[Item]) -> List[str]:
        """Format todos for display in the selector"""
        formatted = []
        for todo in todos:
            # Use the todo title as-is for display
            # User can add prefixes manually if needed
            formatted.append(todo.title)
        return formatted

    def _execute_selector_command(
        self, selector_command: str, todos: List[str]
    ) -> Optional[str]:
        """Execute the external selector command and return the selected todo"""
        try:
            # Join todos with newlines for input to selector
            todos_input = "\n".join(todos)

            # Split selector command to handle arguments
            cmd_parts = selector_command.split()

            # Execute the selector command
            result = subprocess.run(
                cmd_parts,
                input=todos_input,
                text=True,
                capture_output=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return None

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            click.echo(f"Error executing selector command '{selector_command}': {e}")
            return None

    def _process_selected_todo(
        self, selected_text: str, todos: List[Item], board: Board
    ) -> None:
        """Process the selected todo: create/switch branch and update status"""
        # Parse the selection to check if it contains a prefix
        title, prefix = self._parse_selection(selected_text)

        # Find the matching todo item
        todo = self._find_todo_by_title(title, todos)
        if not todo:
            click.echo(f"Error: Could not find todo with title '{title}'")
            return

        # Generate branch name
        branch_name = self._generate_branch_name(todo, prefix)

        # Get current repository
        repo_path = self._get_current_repository()
        if not repo_path:
            click.echo("Error: Not in a git repository")
            return

        # Create or switch to branch
        success = self._create_or_switch_branch(repo_path, branch_name)
        if not success:
            return

        # Update todo status to in-progress
        self._update_todo_status(todo, board)

        click.echo(
            f"Successfully switched to branch '{
                branch_name
            }' and moved todo to in-progress"
        )

    def _parse_selection(self, selected_text: str) -> Tuple[str, Optional[str]]:
        """Parse selection to extract title and optional prefix"""
        # Check if selection contains "  " (two spaces) indicating a prefix
        if "  " in selected_text:
            parts = selected_text.split("  ", 1)
            if len(parts) == 2:
                title = parts[0].strip()
                prefix = parts[1].strip()
                return title, prefix

        # No prefix specified
        return selected_text.strip(), None

    def _find_todo_by_title(self, title: str, todos: List[Item]) -> Optional[Item]:
        """Find a todo by its title"""
        for todo in todos:
            if todo.title == title:
                return todo
        return None

    def _generate_branch_name(self, todo: Item, prefix: Optional[str]) -> str:
        """Generate branch name based on todo type and prefix"""

        def sanitize_for_branch(text: str) -> str:
            """Sanitize text for use in branch names"""
            # Replace spaces and special characters with dashes
            sanitized = re.sub(r"[^\w\-/]", "-", text)
            # Remove multiple consecutive dashes
            sanitized = re.sub(r"-+", "-", sanitized)
            # Remove leading/trailing dashes
            sanitized = sanitized.strip("-")
            return sanitized.lower()

        if prefix:
            # User specified a prefix
            title_sanitized = sanitize_for_branch(todo.title)
            if prefix.endswith("/"):
                # Prefix like "feature/" - use as-is
                return f"{prefix}{title_sanitized}"
            else:
                # Prefix without slash - add one
                return f"{prefix}/{title_sanitized}"
        else:
            # No prefix specified - use default naming
            if todo.is_jira_managed:
                # JIRA todo: use full JIRA format
                ticket_key = todo.metadata.get("ticket_key", "")
                # Extract summary from title (remove ticket key if present)
                summary = todo.title
                if ticket_key and summary.startswith(f"{ticket_key}:"):
                    summary = summary[len(f"{ticket_key}:") :].strip()
                summary_sanitized = sanitize_for_branch(summary)
                return f"{ticket_key.lower()}-{summary_sanitized}"
            else:
                # Regular todo: use sanitized title directly
                return sanitize_for_branch(todo.title)

    def _get_current_repository(self) -> Optional[Path]:
        """Get the current git repository path"""
        if self._tmux_manager.is_in_tmux_session():
            return self._tmux_manager.get_active_session_repository()
        else:
            # Get repo path from external tmux session
            repo_path = self._tmux_manager.get_active_session_repository_external()
            if not repo_path:
                raise MKanbanError("No git repository found in active tmux session")
            return repo_path

    def _create_or_switch_branch(self, repo_path: Path, branch_name: str) -> bool:
        """Create or switch to the specified branch"""
        try:
            git_ops = GitOperations(repo_path)

            # Check if branch exists
            if git_ops.branch_exists(branch_name):
                # Switch to existing branch
                result = subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    click.echo(f"Switched to existing branch '{branch_name}'")
                    return True
                else:
                    click.echo(
                        f"Error switching to branch '{branch_name}': {result.stderr}"
                    )
                    return False
            else:
                # Create new branch
                result = subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    click.echo(f"Created and switched to new branch '{branch_name}'")
                    return True
                else:
                    click.echo(
                        f"Error creating branch '{branch_name}': {result.stderr}"
                    )
                    return False

        except Exception as e:
            click.echo(f"Error with git operations: {e}")
            return False

    def _update_todo_status(self, todo: Item, board: Board) -> None:
        """Update todo status to in-progress both locally and in JIRA if applicable"""
        try:
            # Find the in-progress column
            in_progress_column = None
            for column in board.columns:
                if column.id == "in-progress" or column.name.lower() in [
                    "in progress",
                    "in-progress",
                    "doing",
                ]:
                    in_progress_column = column
                    break

            if not in_progress_column:
                # Try to find any column that might be in-progress
                for column in board.columns:
                    if (
                        "progress" in column.name.lower()
                        or "doing" in column.name.lower()
                    ):
                        in_progress_column = column
                        break

            if not in_progress_column:
                click.echo("Warning: Could not find in-progress column")
                return

            # Remove todo from current column
            for column in board.columns:
                if todo in column.items:
                    column.items.remove(todo)
                    break

            # Add to in-progress column
            todo.column_id = in_progress_column.id
            in_progress_column.items.append(todo)

            # Save the board
            self._board_service.save_board(board)

            # Update JIRA status if it's a JIRA todo
            if todo.is_jira_managed:
                self._update_jira_status(todo)

        except Exception as e:
            click.echo(f"Warning: Could not update todo status: {e}")

    def _update_jira_status(self, todo: Item) -> None:
        """Update JIRA ticket status to In Progress"""
        try:
            # This would require async context, so we'll skip JIRA update for now
            # In a full implementation, you'd want to integrate with the JIRA daemon
            # or use the JiraClient directly in an async context
            ticket_key = todo.metadata.get("ticket_key", "")
            click.echo(
                f"Note: JIRA status update for {ticket_key} would be handled by daemon"
            )
        except Exception as e:
            click.echo(f"Warning: Could not update JIRA status: {e}")
