from enum import Enum
from typing import Any, Optional, List
from pydantic import BaseModel, Field


class ConditionType(str, Enum):
    """Types of conditions that must be met for action execution"""
    TIME_RANGE = "time_range"
    TASK_IN_COLUMN = "task_in_column"
    TASK_PROPERTY = "task_property"
    BOARD_PROPERTY = "board_property"
    DAY_OF_WEEK = "day_of_week"
    CUSTOM = "custom"


class Operator(str, Enum):
    """Comparison operators for conditions"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    MATCHES_REGEX = "matches_regex"


class Condition(BaseModel):
    """Defines a condition that must be met for action execution"""
    type: ConditionType = Field(description="The type of condition")

    # Time range condition
    start_time: Optional[str] = Field(
        default=None,
        description="Start time in HH:MM format for TIME_RANGE"
    )
    end_time: Optional[str] = Field(
        default=None,
        description="End time in HH:MM format for TIME_RANGE"
    )

    # Task in column condition
    column_ids: Optional[List[str]] = Field(
        default=None,
        description="List of column IDs for TASK_IN_COLUMN"
    )

    # Property-based conditions
    field: Optional[str] = Field(
        default=None,
        description="Field name for property conditions"
    )
    operator: Optional[Operator] = Field(
        default=None,
        description="Comparison operator for property conditions"
    )
    value: Optional[Any] = Field(
        default=None,
        description="Value to compare against for property conditions"
    )

    # Day of week condition
    days: Optional[List[int]] = Field(
        default=None,
        description="Days of week (1=Monday, 7=Sunday) for DAY_OF_WEEK"
    )

    # Custom condition
    expression: Optional[str] = Field(
        default=None,
        description="Custom expression for CUSTOM type"
    )

    # Logic operator for combining conditions
    logic_operator: str = Field(
        default="and",
        description="Logic operator when multiple conditions exist (and/or)"
    )

    def is_time_based(self) -> bool:
        """Check if this is a time-based condition"""
        return self.type in [ConditionType.TIME_RANGE, ConditionType.DAY_OF_WEEK]

    def is_property_based(self) -> bool:
        """Check if this is a property-based condition"""
        return self.type in [ConditionType.TASK_PROPERTY, ConditionType.BOARD_PROPERTY]

    def is_column_based(self) -> bool:
        """Check if this is a column-based condition"""
        return self.type == ConditionType.TASK_IN_COLUMN
