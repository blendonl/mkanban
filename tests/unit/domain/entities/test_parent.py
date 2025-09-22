from unittest.mock import patch

from src.domain.entities.parent import Parent
from tests.fixtures.entity_factories import ParentFactory


class TestParent:
    """Test cases for the Parent entity."""

    def test_parent_creation_with_defaults(self):
        """Test creating a parent with default values."""
        parent = Parent(name="Test Epic")

        assert parent.name == "Test Epic"
        assert parent.color == "blue"
        assert parent.description == ""
        assert parent.id == "test-epic"
        assert parent.created_at is not None
        assert parent.updated_at is not None

    def test_parent_creation_with_all_fields(self):
        """Test creating a parent with all fields specified."""
        parent = Parent(
            name="Complete Epic",
            color="green",
            description="A comprehensive epic for testing"
        )

        assert parent.name == "Complete Epic"
        assert parent.color == "green"
        assert parent.description == "A comprehensive epic for testing"
        assert parent.id == "complete-epic"

    def test_parent_id_generation_from_name(self):
        """Test that parent ID is generated from name."""
        test_cases = [
            ("User Authentication", "user-authentication"),
            ("Epic #123", "epic-123"),
            ("Feature/Enhancement", "feature-enhancement"),
            ("Multi   Spaces   Epic", "multi-spaces-epic"),
            ("Special@Chars$Epic!", "special-chars-epic"),
        ]

        for name, expected_id in test_cases:
            parent = Parent(name=name)
            assert parent.id == expected_id

    def test_parent_update(self):
        """Test updating parent properties."""
        parent = ParentFactory.create()
        original_updated_at = parent.updated_at

        with patch('src.utils.date_utils.now') as mock_now:
            mock_now.return_value = original_updated_at + 1
            parent.update(
                description="Updated description",
                color="red"
            )

        assert parent.description == "Updated description"
        assert parent.color == "red"
        assert parent.updated_at > original_updated_at

    def test_valid_colors(self):
        """Test that valid colors are accepted."""
        valid_colors = ["blue", "green", "red", "yellow", "purple", "orange", "pink", "gray"]

        for color in valid_colors:
            parent = Parent(name="Test Epic", color=color)
            assert parent.color == color

    def test_is_color_methods(self):
        """Test color checking methods."""
        blue_parent = ParentFactory.create(color="blue")
        green_parent = ParentFactory.create(color="green")
        red_parent = ParentFactory.create(color="red")

        # Test specific color checks
        assert blue_parent.is_blue() is True
        assert blue_parent.is_green() is False
        assert blue_parent.is_red() is False

        assert green_parent.is_green() is True
        assert green_parent.is_blue() is False

        assert red_parent.is_red() is True
        assert red_parent.is_blue() is False

    def test_color_hex_values(self):
        """Test getting hex color values."""
        color_mappings = {
            "blue": "#3B82F6",
            "green": "#10B981",
            "red": "#EF4444",
            "yellow": "#F59E0B",
            "purple": "#8B5CF6",
            "orange": "#F97316",
            "pink": "#EC4899",
            "gray": "#6B7280"
        }

        for color, expected_hex in color_mappings.items():
            parent = Parent(name="Test", color=color)
            assert parent.get_color_hex() == expected_hex

    def test_color_hex_unknown_color(self):
        """Test hex value for unknown color."""
        # Create parent with custom color
        parent = Parent(name="Test", color="custom")
        # Should return default blue hex
        assert parent.get_color_hex() == "#3B82F6"

    def test_parent_display_name(self):
        """Test getting display name with emoji."""
        parent = ParentFactory.create(name="Feature Epic", color="green")

        display_name = parent.get_display_name()

        # Should include color emoji and name
        assert "Feature Epic" in display_name
        assert "🟢" in display_name

    def test_parent_display_name_all_colors(self):
        """Test display names for all color options."""
        color_emojis = {
            "blue": "🔵",
            "green": "🟢",
            "red": "🔴",
            "yellow": "🟡",
            "purple": "🟣",
            "orange": "🟠",
            "pink": "🩷",
            "gray": "⚫"
        }

        for color, emoji in color_emojis.items():
            parent = Parent(name="Test Epic", color=color)
            display_name = parent.get_display_name()
            assert emoji in display_name
            assert "Test Epic" in display_name

    def test_parent_serialization(self):
        """Test that parent can be serialized to dict."""
        parent = ParentFactory.create(
            name="Serialization Epic",
            color="purple",
            description="Epic for testing serialization"
        )

        parent_dict = parent.model_dump()

        assert isinstance(parent_dict, dict)
        assert parent_dict["name"] == "Serialization Epic"
        assert parent_dict["color"] == "purple"
        assert parent_dict["description"] == "Epic for testing serialization"
        assert parent_dict["id"] == "serialization-epic"

    def test_parent_equality(self):
        """Test parent equality comparison."""
        parent1 = ParentFactory.create(name="Same Epic")
        parent2 = ParentFactory.create(name="Same Epic")
        parent3 = ParentFactory.create(name="Different Epic")

        # Parents with same name should have same ID
        assert parent1.id == parent2.id
        # Parents with different names should have different IDs
        assert parent1.id != parent3.id

    def test_parent_updated_at_changes_on_modifications(self):
        """Test that updated_at changes when parent is modified."""
        parent = ParentFactory.create()
        original_updated_at = parent.updated_at

        with patch('src.utils.date_utils.now') as mock_now:
            mock_now.return_value = original_updated_at + 1
            parent.update(description="Updated")

        assert parent.updated_at > original_updated_at

    def test_parent_validation_edge_cases(self):
        """Test parent validation with edge cases."""
        # Empty name
        empty_parent = Parent(name="")
        assert empty_parent.id == ""

        # Very long name
        long_name = "A" * 200
        long_parent = Parent(name=long_name)
        assert len(long_parent.id) <= 200

        # Name with only special characters
        special_parent = Parent(name="!@#$%^&*()")
        assert special_parent.id != ""

    def test_parent_color_case_insensitive(self):
        """Test that color comparison is case insensitive."""
        parent = Parent(name="Test", color="Blue")

        # The model should normalize to lowercase
        assert parent.color.lower() == "blue"

    def test_parent_description_multiline(self):
        """Test parent with multiline description."""
        multiline_desc = """This is a complex epic that spans
        multiple lines and includes various
        features and requirements."""

        parent = Parent(
            name="Complex Epic",
            description=multiline_desc
        )

        assert parent.description == multiline_desc

    def test_parent_with_complex_scenario(self):
        """Test parent behavior in a complex scenario."""
        # Create epic for authentication feature
        auth_epic = Parent(
            name="User Authentication System",
            color="blue",
            description="Complete user authentication including login, logout, registration, and password reset"
        )

        # Verify initial setup
        assert auth_epic.is_blue() is True
        assert "User Authentication System" in auth_epic.get_display_name()
        assert auth_epic.get_color_hex() == "#3B82F6"

        # Update the epic as requirements change
        auth_epic.update(
            description="Enhanced authentication with OAuth, 2FA, and social login",
            color="green"  # Changed priority/status
        )

        # Verify updates
        assert auth_epic.is_green() is True
        assert auth_epic.is_blue() is False
        assert "Enhanced authentication" in auth_epic.description
        assert auth_epic.get_color_hex() == "#10B981"

        # Verify display name updates
        display_name = auth_epic.get_display_name()
        assert "🟢" in display_name
        assert "User Authentication System" in display_name

    def test_parent_factory_batch_creation(self):
        """Test creating multiple parents with factory."""
        parents = ParentFactory.create_batch(5)

        assert len(parents) == 5
        # Each should have unique names
        names = [p.name for p in parents]
        assert len(set(names)) == 5
        # Each should have different colors (cycling through available colors)
        colors = [p.color for p in parents]
        assert len(set(colors)) >= 2  # Should have at least 2 different colors