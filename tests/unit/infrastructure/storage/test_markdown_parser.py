
from src.infrastructure.storage.markdown_parser import MarkdownParser
from tests.fixtures.test_data import SAMPLE_BOARD_MARKDOWN, SAMPLE_ITEM_MARKDOWN


class TestMarkdownParser:
    """Test cases for the MarkdownParser class."""

    def setup_method(self):
        """Set up test dependencies."""
        self.parser = MarkdownParser()

    def test_parse_board_markdown_success(self):
        """Test successfully parsing board markdown."""
        result = self.parser.parse_board_markdown(SAMPLE_BOARD_MARKDOWN)

        assert result is not None
        assert result["name"] == "Test Board"
        assert result["description"] == "A test board for unit testing"
        assert len(result["columns"]) == 3
        assert result["columns"][0]["name"] == "To Do"
        assert result["columns"][1]["name"] == "In Progress"
        assert result["columns"][2]["name"] == "Done"

    def test_parse_item_markdown_success(self):
        """Test successfully parsing item markdown."""
        result = self.parser.parse_item_markdown(SAMPLE_ITEM_MARKDOWN)

        assert result is not None
        assert result["title"] == "Test Task"
        assert result["description"] == "A sample task for testing"
        assert result["status"] == "To Do"
        assert "test" in result["tags"]
        assert "sample" in result["tags"]

    def test_parse_markdown_with_no_frontmatter(self):
        """Test parsing markdown without frontmatter."""
        markdown_content = """# Simple Markdown

This is just content without frontmatter.
"""
        result = self.parser.parse_item_markdown(markdown_content)

        # Should return empty dict or handle gracefully
        assert result == {} or result is None

    def test_parse_markdown_with_invalid_yaml(self):
        """Test parsing markdown with invalid YAML frontmatter."""
        invalid_markdown = """---
invalid: yaml: content
  - missing quotes
  improper indentation
---

# Content
"""
        result = self.parser.parse_item_markdown(invalid_markdown)

        # Should handle gracefully
        assert result == {} or result is None

    def test_generate_board_markdown(self):
        """Test generating board markdown from data."""
        board_data = {
            "name": "Generated Board",
            "description": "A programmatically generated board",
            "columns": [
                {"name": "Todo", "position": 0},
                {"name": "Done", "position": 1}
            ]
        }

        result = self.parser.generate_board_markdown(board_data)

        assert "Generated Board" in result
        assert "Todo" in result
        assert "Done" in result
        assert "---" in result  # YAML frontmatter delimiters

    def test_generate_item_markdown(self):
        """Test generating item markdown from data."""
        item_data = {
            "title": "Generated Task",
            "description": "A programmatically generated task",
            "status": "In Progress",
            "tags": ["generated", "test"]
        }

        result = self.parser.generate_item_markdown(item_data)

        assert "Generated Task" in result
        assert "In Progress" in result
        assert "generated" in result
        assert "test" in result
        assert "---" in result  # YAML frontmatter delimiters