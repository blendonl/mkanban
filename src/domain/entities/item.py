from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from src.core.types import ItemId, ColumnId, ParentId, Timestamp, FilePath
from src.utils.string_utils import generate_id_from_name, get_safe_filename
from src.utils.date_utils import now
from .git_metadata import GitMetadata


class Item(BaseModel):
    id: ItemId = Field(default="")
    title: str
    column_id: ColumnId
    description: str = ""
    parent_id: Optional[ParentId] = None
    created_at: Timestamp = Field(default_factory=now)
    moved_in_progress_at: Optional[Timestamp] = None
    moved_in_done_at: Optional[Timestamp] = None
    worked_on_for: Optional[str] = None  # Format: "HH:MM"
    file_path: Optional[FilePath] = None

    # Git-specific fields (optional)
    git_metadata: Optional[GitMetadata] = None
    is_git_managed: bool = Field(default=False)

    # Generic metadata for any integration (JIRA, GitHub, etc.)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_jira_managed: bool = Field(default=False)
    auto_sync_enabled: bool = Field(default=True)

    def model_post_init(self, __context) -> None:
        # If this is a git task and no title is provided, generate from branch name
        if self.git_metadata and not self.title:
            self.title = self._generate_title_from_branch()

        # If no description and this is a git task with commit message, use it
        if self.git_metadata and not self.description and self.git_metadata.last_commit_message:
            self.description = self.git_metadata.last_commit_message

        # If this is a Jira task and no title is provided, use summary
        if self.is_jira_managed and not self.title:
            ticket_key = self.metadata.get("ticket_key", "")
            self.title = ticket_key
            if hasattr(self, '_jira_summary') and self._jira_summary:
                self.title = f"{ticket_key}: {self._jira_summary}"

        # Set ID based on source:
        # - JIRA tasks: Use JIRA ticket key
        # - Git tasks: Use branch-based ID
        # - Manual tasks: Will be set by service layer with board context
        # - File-based: Extract from filename
        if not self.id:
            if self.is_jira_managed and self.metadata.get("ticket_key"):
                # JIRA items use ticket key as ID
                self.id = self.metadata.get("ticket_key", "")
            elif self.file_path:
                # Extract ID from filename (supports both old and new formats)
                filename = Path(self.file_path).stem
                # New format: {id}-{title} or old format: {title}
                if '-' in filename:
                    # Try to extract ID prefix (e.g., "REC-27-fix-bug" -> "REC-27")
                    parts = filename.split('-', 2)
                    if len(parts) >= 2 and parts[1].isdigit():
                        self.id = f"{parts[0]}-{parts[1]}"
                    else:
                        # Fallback to full filename as ID
                        self.id = filename
                else:
                    self.id = filename
                if not self.title or self.title == filename:
                    self.title = filename
            elif self.git_metadata:
                # Git items use branch-based ID
                self.id = generate_id_from_name(self.title) or "unnamed_item"
            # Manual items will have ID set by ItemService with board context

    def update(self, **kwargs) -> None:
        # Protect system-managed timing fields from manual updates
        protected_fields = {'moved_in_progress_at', 'moved_in_done_at', 'worked_on_for'}
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in protected_fields:
                setattr(self, key, value)

    def move_to_column(self, column_id: ColumnId) -> None:
        old_column_id = self.column_id
        self.column_id = column_id

        # Normalize column IDs for comparison (handle both hyphen and underscore)
        normalized_column_id = column_id.replace('_', '-')
        normalized_old_column_id = old_column_id.replace('_', '-') if old_column_id else None

        # Track when item moves to in-progress
        if normalized_column_id == "in-progress" and normalized_old_column_id != "in-progress":
            self.moved_in_progress_at = now()

        # Track when item moves to done and calculate work duration
        if normalized_column_id == "done" and normalized_old_column_id != "done":
            self.moved_in_done_at = now()

            # Calculate worked_on_for if item was previously in progress
            if self.moved_in_progress_at:
                self.worked_on_for = self._calculate_work_duration(
                    self.moved_in_progress_at,
                    self.moved_in_done_at
                )

    def set_parent(self, parent_id: Optional[ParentId]) -> None:
        self.parent_id = parent_id

    @property
    def has_parent(self) -> bool:
        return self.parent_id is not None

    def _calculate_work_duration(self, start_time: Timestamp, end_time: Timestamp) -> str:
        """Calculate work duration in HH:MM format"""
        try:
            # Parse timestamps - handle both string and datetime types
            if isinstance(start_time, str):
                start_dt = datetime.fromisoformat(start_time)
            else:
                start_dt = start_time

            if isinstance(end_time, str):
                end_dt = datetime.fromisoformat(end_time)
            else:
                end_dt = end_time

            # Calculate duration
            duration = end_dt - start_dt
            total_minutes = int(duration.total_seconds() / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60

            return f"{hours}:{minutes:02d}"
        except Exception:
            # If calculation fails, return None (will be handled gracefully)
            return None

    def _generate_title_from_branch(self) -> str:
        """Generate a human-readable title from branch name"""
        if not self.git_metadata:
            return ""

        branch_name = self.git_metadata.branch_name
        Path(self.git_metadata.repository_path)

        # Remove common prefixes
        prefixes = ["feature/", "bugfix/", "hotfix/", "fix/", "feat/"]
        for prefix in prefixes:
            if branch_name.startswith(prefix):
                branch_name = branch_name[len(prefix):]
                break

        # Replace dashes and underscores with spaces and title case
        title = branch_name.replace("-", " ").replace("_", " ").title()

        # Return title without repository name
        return title

    def update_git_metadata(self, **kwargs) -> None:
        """Update git metadata fields"""
        if not self.git_metadata:
            return

        for key, value in kwargs.items():
            if hasattr(self.git_metadata, key):
                setattr(self.git_metadata, key, value)

    def set_current_branch(self, is_current: bool) -> None:
        """Mark this task as corresponding to the current branch"""
        if self.git_metadata:
            self.git_metadata.is_current_branch = is_current

    def mark_branch_deleted(self) -> None:
        """Mark the associated branch as deleted"""
        if self.git_metadata:
            self.git_metadata.branch_deleted_at = now()
            self.git_metadata.is_current_branch = False

    def get_repository_name(self) -> Optional[str]:
        """Get the repository name from the path"""
        if self.git_metadata:
            return Path(self.git_metadata.repository_path).name
        return None

    def get_short_commit_hash(self) -> Optional[str]:
        """Get short version of commit hash"""
        if self.git_metadata and self.git_metadata.last_commit_hash:
            return self.git_metadata.last_commit_hash[:7]
        return None

    def is_branch_active(self) -> bool:
        """Check if the associated branch is still active (not deleted)"""
        if self.git_metadata:
            return self.git_metadata.branch_deleted_at is None
        return False

    def should_auto_complete(self) -> bool:
        """Check if task should be auto-completed based on branch state"""
        done_column_id = get_safe_filename("done")

        return (
            self.is_git_managed
            and self.auto_sync_enabled
            and not self.is_branch_active()
            and self.column_id != done_column_id
        )

    def should_auto_activate(self) -> bool:
        """Check if task should be moved to in-progress based on current branch"""
        # Convert common column names to their corresponding IDs
        excluded_column_ids = [
            get_safe_filename("in-progress"),
            get_safe_filename("done")
        ]

        return (
            self.is_git_managed
            and self.auto_sync_enabled
            and self.git_metadata
            and self.git_metadata.is_current_branch
            and self.is_branch_active()
            and self.column_id not in excluded_column_ids
        )

    def update_jira_metadata(self, **kwargs) -> None:
        """Update Jira metadata fields"""
        if not self.is_jira_managed:
            return

        for key, value in kwargs.items():
            self.metadata[key] = value
        self.metadata["last_sync"] = now()

    def add_linked_ticket(self, ticket_key: str) -> None:
        """Add a linked Jira ticket"""
        linked_tickets = self.metadata.get("linked_tickets", [])
        if ticket_key not in linked_tickets:
            linked_tickets.append(ticket_key)
            self.metadata["linked_tickets"] = linked_tickets

    def remove_linked_ticket(self, ticket_key: str) -> None:
        """Remove a linked Jira ticket"""
        linked_tickets = self.metadata.get("linked_tickets", [])
        if ticket_key in linked_tickets:
            linked_tickets.remove(ticket_key)
            self.metadata["linked_tickets"] = linked_tickets

    def get_jira_ticket_key(self) -> Optional[str]:
        """Get the primary Jira ticket key"""
        return self.metadata.get("ticket_key")

    def get_parent_ticket_key(self) -> Optional[str]:
        """Get the parent JIRA ticket key"""
        return self.metadata.get("parent_ticket_key")

    def get_epic_key(self) -> Optional[str]:
        """Get the epic key this ticket belongs to"""
        return self.metadata.get("epic_key")

    def get_subtask_keys(self) -> List[str]:
        """Get list of subtask ticket keys"""
        return self.metadata.get("subtask_keys", [])

    def get_linked_ticket_keys(self) -> List[str]:
        """Get all linked ticket keys from issue links"""
        issue_links = self.metadata.get("issue_links", [])
        return [link.get("key", "") for link in issue_links if link.get("key")]

    def has_jira_parent(self) -> bool:
        """Check if this item has a JIRA parent"""
        return self.is_jira_managed and self.metadata.get("parent_ticket_key") is not None

    def has_jira_subtasks(self) -> bool:
        """Check if this item has JIRA subtasks"""
        return self.is_jira_managed and len(self.metadata.get("subtask_keys", [])) > 0

    def is_jira_subtask(self) -> bool:
        """Check if this is a JIRA subtask"""
        return self.is_jira_managed and self.metadata.get("is_subtask", False)

    def should_sync_to_jira(self) -> bool:
        """Check if this item should sync back to Jira"""
        return (
            self.is_jira_managed
            and self.auto_sync_enabled
        )

    @classmethod
    def from_git_branch(cls, branch_name: str, repository_path: str, column_id: ColumnId, **branch_info) -> "Item":
        """Create an Item from git branch information"""
        git_metadata = GitMetadata(
            repository_path=repository_path,
            branch_name=branch_name,
            branch_full_name=branch_info.get("full_name", f"refs/heads/{branch_name}"),
            last_commit_hash=branch_info.get("last_commit_hash"),
            last_commit_message=branch_info.get("last_commit_message"),
            last_commit_author=branch_info.get("last_commit_author"),
            last_commit_date=branch_info.get("last_commit_date"),
            is_current_branch=branch_info.get("is_current", False),
            branch_created_at=now(),
        )

        return cls(
            title="",  # Will be generated in model_post_init
            column_id=column_id,
            git_metadata=git_metadata,
            is_git_managed=True,
            auto_sync_enabled=True,
        )

    @classmethod
    def from_jira_ticket(cls, ticket_key: str, ticket_data: Dict[str, Any], column_id: ColumnId) -> "Item":
        """Create an Item from Jira ticket information"""
        metadata = {
            "ticket_key": ticket_key,
            "ticket_id": ticket_data.get("id", ""),
            "ticket_url": ticket_data.get("url", ""),
            "project_key": ticket_data.get("project_key", ""),
            "issue_type": ticket_data.get("issue_type", ""),
            "priority": ticket_data.get("priority"),
            "assignee": ticket_data.get("assignee"),
            "reporter": ticket_data.get("reporter"),
            "labels": ticket_data.get("labels", []),
            "components": ticket_data.get("components", []),
            "jira_status": ticket_data.get("status", ""),
            "last_sync": now(),
            # Hierarchy fields
            "parent_ticket_key": ticket_data.get("parent"),
            "epic_key": ticket_data.get("epic_link"),
            "subtask_keys": ticket_data.get("subtasks", []),
            "is_subtask": ticket_data.get("is_subtask", False),
            # Issue links
            "issue_links": ticket_data.get("issue_links", []),
            # Sprint and planning
            "sprint_name": ticket_data.get("sprint"),
            "story_points": ticket_data.get("story_points"),
            # Versions
            "fix_versions": ticket_data.get("fix_versions", []),
            "affects_versions": ticket_data.get("affects_versions", []),
        }

        return cls(
            title=f"{ticket_key}: {ticket_data.get('summary') or ticket_key}",
            column_id=column_id,
            description=ticket_data.get("description") or "",
            metadata=metadata,
            is_jira_managed=True,
            auto_sync_enabled=True,
        )

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "title": self.title,
            "column_id": self.column_id,
            "description": self.description,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "moved_in_progress_at": self.moved_in_progress_at,
            "moved_in_done_at": self.moved_in_done_at,
            "worked_on_for": self.worked_on_for,
        }

        # Add git-specific fields if this is a git-managed item
        if self.is_git_managed:
            result["is_git_managed"] = self.is_git_managed
            if self.git_metadata:
                result["git_metadata"] = self.git_metadata.to_dict()

        # Add integration metadata if present
        if self.metadata:
            result["metadata"] = self.metadata

        # Add Jira-specific flag if this is a Jira-managed item
        if self.is_jira_managed:
            result["is_jira_managed"] = self.is_jira_managed

        # Add auto_sync_enabled if not default
        if not self.auto_sync_enabled:
            result["auto_sync_enabled"] = self.auto_sync_enabled

        return result
