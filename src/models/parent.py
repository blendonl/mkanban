from datetime import datetime
from pydantic import BaseModel, Field
import re


class Parent(BaseModel):
    id: str = Field(default="")
    name: str
    description: str = ""
    color: str = "blue"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def model_post_init(self, __context) -> None:
        if not self.id:
            self.id = self._generate_id_from_name(self.name)
    
    def _generate_id_from_name(self, name: str) -> str:
        safe_name = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        safe_name = re.sub(r'\s+', '_', safe_name.strip())
        return safe_name or 'unnamed_parent'

    def update(self, **kwargs) -> None:
        """Update parent fields and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
