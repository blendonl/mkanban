import re
from typing import Optional
from textual.widgets import Markdown
from src.domain.entities.item import Item
from src.controllers.item_controller import ItemController


class ItemWidget(Markdown):
    def __init__(
        self,
        item: Item,
        item_controller: ItemController,
        parent_name: Optional[str] = None,
    ):
        self.item = item
        self.parent_name = parent_name
        self.item_controller = item_controller

        markdown_content = self._build_display_content()

        # Sanitize item ID for valid CSS identifier
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", item.id)
        super().__init__(markdown_content, classes="item", id=f"item_{safe_id}")
        self.can_focus = True

    def _build_display_content(self) -> str:
        """Build the markdown content for the item with JIRA indicators"""
        parts = []

        # Add JIRA indicators if this is a JIRA-managed item
        if self.item.is_jira_managed and self.item.jira_metadata:
            indicators = self._get_jira_indicators()
            if indicators:
                parts.append(indicators)

        # Add title
        parts.append(self.item.title)

        # Add JIRA badges if this is a JIRA item
        if self.item.is_jira_managed and self.item.jira_metadata:
            badges = self._get_jira_badges()
            if badges:
                parts.append(badges)

        # Add parent info if exists
        if self.parent_name:
            parts.append(f"\n\n*Parent: {self.parent_name}*")

        return " ".join(parts) if not self.parent_name else "\n\n".join([" ".join(parts[:-1]), parts[-1]]) if parts else ""

    def _get_jira_indicators(self) -> str:
        """Get JIRA issue type and priority indicators"""
        if not self.item.jira_metadata:
            return ""

        indicators = []

        # Issue type icon
        issue_type = self.item.jira_metadata.issue_type.lower()
        if "epic" in issue_type:
            indicators.append("📚")
        elif "story" in issue_type:
            indicators.append("📖")
        elif "bug" in issue_type:
            indicators.append("🐛")
        elif "subtask" in issue_type or self.item.jira_metadata.is_subtask:
            indicators.append("☑️")
        elif "task" in issue_type:
            indicators.append("📋")
        else:
            indicators.append("📄")

        # Priority indicator
        priority = (self.item.jira_metadata.priority or "").lower()
        if priority in ["highest", "blocker"]:
            indicators.append("🔴")
        elif priority == "high":
            indicators.append("🟠")
        elif priority == "medium":
            indicators.append("🟡")
        elif priority == "low":
            indicators.append("🟢")
        elif priority == "lowest":
            indicators.append("🔵")

        return "".join(indicators) if indicators else ""

    def _get_jira_badges(self) -> str:
        """Get JIRA metadata badges (story points, sprint, links, etc.)"""
        if not self.item.jira_metadata:
            return ""

        badges = []

        # Story points
        if self.item.jira_metadata.story_points:
            badges.append(f"`{self.item.jira_metadata.story_points}pts`")

        # Sprint
        if self.item.jira_metadata.sprint_name:
            sprint_short = self.item.jira_metadata.sprint_name[:15]
            if len(self.item.jira_metadata.sprint_name) > 15:
                sprint_short += "..."
            badges.append(f"`🏃{sprint_short}`")

        # Subtasks count
        if self.item.jira_metadata.subtask_keys:
            count = len(self.item.jira_metadata.subtask_keys)
            badges.append(f"`☑️{count}`")

        # Issue links count
        if self.item.jira_metadata.issue_links:
            count = len(self.item.jira_metadata.issue_links)
            badges.append(f"`🔗{count}`")

        # Components (show first one if exists)
        if self.item.jira_metadata.components:
            component = self.item.jira_metadata.components[0]
            if len(component) > 10:
                component = component[:10] + "..."
            badges.append(f"`{component}`")
            if len(self.item.jira_metadata.components) > 1:
                badges.append(f"`+{len(self.item.jira_metadata.components) - 1}`")

        # Labels (show first one if exists)
        elif self.item.jira_metadata.labels:
            label = self.item.jira_metadata.labels[0]
            if len(label) > 10:
                label = label[:10] + "..."
            badges.append(f"`{label}`")
            if len(self.item.jira_metadata.labels) > 1:
                badges.append(f"`+{len(self.item.jira_metadata.labels) - 1}`")

        return " ".join(badges) if badges else ""

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")
