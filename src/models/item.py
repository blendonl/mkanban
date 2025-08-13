from datetime import datetime
from pydantic import BaseModel, Field
import re


class Item(BaseModel):
    id: str = Field(default="")
    title: str
    description: str = ""
    parent_id: str | None = None
    column_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def model_post_init(self, __context) -> None:
        if not self.id:
            self.id = self._generate_id_from_title(self.title)
    
    def _generate_id_from_title(self, title: str) -> str:
        safe_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        safe_title = re.sub(r'\s+', '_', safe_title.strip())
        return safe_title or 'unnamed_item'

    def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def move_to_column(self, column_id: str) -> None:
        self.column_id = column_id
        self.updated_at = datetime.now()

    def set_parent(self, parent_id: str | None) -> None:
        self.parent_id = parent_id
        self.updated_at = datetime.now()

    @property
    def has_parent(self) -> bool:
        return self.parent_id is not None
