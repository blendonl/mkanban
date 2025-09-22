from pydantic import BaseModel, Field
from src.core.types import ParentId, ParentColor, Timestamp
from src.utils.string_utils import generate_id_from_name
from src.utils.date_utils import now


class Parent(BaseModel):
    id: ParentId = Field(default="")
    name: str
    description: str = ""
    color: str = ParentColor.BLUE.value
    created_at: Timestamp = Field(default_factory=now)
    updated_at: Timestamp = Field(default_factory=now)

    def model_post_init(self, __context) -> None:
        if not self.id:
            self.id = generate_id_from_name(self.name) or "unnamed_parent"

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = now()
