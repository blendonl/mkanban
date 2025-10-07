import re
from typing import Optional
from textual.widgets import Static
from textual.containers import Vertical, Horizontal
from src.domain.entities.item import Item
from src.controllers.item_controller import ItemController


class ItemWidget(Vertical):
    def __init__(
        self,
        item: Item,
        item_controller: ItemController,
        parent_name: Optional[str] = None,
    ):
        self.item = item
        self.parent_name = parent_name
        self.item_controller = item_controller

        # Sanitize item ID for valid CSS identifier
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", item.id)
        super().__init__(classes="item", id=f"item_{safe_id}")
        self.can_focus = True

    def compose(self):
        """Compose the structured card layout"""
        # Row 1: Icon + Title
        yield Static(self._get_title_row(), classes="item-title-row")

        # Row 2: Spacer
        yield Static(" ", classes="item-spacer")

        # Row 3: Labels/Components
        labels_text = self._get_labels_row()
        yield Static(labels_text if labels_text else " ", classes="item-labels-row")

        # Row 4: Spacer
        yield Static(" ", classes="item-spacer")

        # Row 5: Footer (Ticket ID left, Priority + Subtask count right)
        yield Horizontal(
            Static(self._get_footer_left(), classes="item-footer-left"),
            Static(self._get_footer_right(), classes="item-footer-right"),
            classes="item-footer-row",
        )

    def _get_title_row(self) -> str:
        """Build the title row with icon and title"""
        parts = []

        # Add issue type icon
        icon = self._get_issue_type_icon()
        if icon:
            parts.append(icon)

        # Add title
        parts.append(self.item.title)

        return " ".join(parts)

    def _get_issue_type_icon(self) -> str:
        """Get the issue type icon"""
        if not self.item.is_jira_managed or not self.item.jira_metadata:
            return ""

        issue_type = self.item.jira_metadata.issue_type.lower()
        if "epic" in issue_type:
            return "📚"
        elif "story" in issue_type:
            return "📖"
        elif "bug" in issue_type:
            return "🐛"
        elif "subtask" in issue_type or self.item.jira_metadata.is_subtask:
            return "☑️"
        elif "task" in issue_type:
            return "📋"
        else:
            return "📄"

    def _get_labels_row(self) -> str:
        """Build the labels/components row"""
        if not self.item.is_jira_managed or not self.item.jira_metadata:
            return ""

        items = []

        # Add components first
        if self.item.jira_metadata.components:
            items.extend(self.item.jira_metadata.components)

        # Add labels if no components
        elif self.item.jira_metadata.labels:
            items.extend(self.item.jira_metadata.labels)

        if items:
            # Join first few items, truncate if too many
            display_items = items[:3]
            result = ", ".join(display_items)
            if len(items) > 3:
                result += f", +{len(items) - 3}"
            return f"🏷️ {result}"

        return ""

    def _get_footer_left(self) -> str:
        """Build the footer left side (Ticket ID)"""
        if self.item.is_jira_managed and self.item.jira_metadata:
            return self.item.jira_metadata.ticket_key
        return self.item.id

    def _get_footer_right(self) -> str:
        """Build the footer right side (Priority + Subtask count)"""
        if not self.item.is_jira_managed or not self.item.jira_metadata:
            return ""

        parts = []

        # Priority indicator
        priority = (self.item.jira_metadata.priority or "").lower()
        if priority in ["highest", "blocker"]:
            parts.append("🔴")
        elif priority == "high":
            parts.append("🟠")
        elif priority == "medium":
            parts.append("🟡")
        elif priority == "low":
            parts.append("🟢")
        elif priority == "lowest":
            parts.append("🔵")

        # Subtask count
        if self.item.jira_metadata.subtask_keys:
            count = len(self.item.jira_metadata.subtask_keys)
            parts.append(f"☑️{count}")

        return " ".join(parts)

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")
