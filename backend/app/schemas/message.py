from pydantic import BaseModel, Field
from datetime import datetime

# Pydantic schemas for creating, updating, and returning Message resources.
class MessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=2000,
        description="Message content to analyze. Avoid using real names or personal information."
    )
    author_alias: str | None = Field(
        default=None,
        max_length=50,
        description="Optional alias for the message author. For privacy, avoid real names."
    )
class MessageUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, may_length=2000)
    author_alias: str | None = Field(default=None, max_length = 50)

class MessageResponse(BaseModel):
    id: int
    case_id: int
    content: str
    author_alias: str | None
    timestamp: datetime

    class Config:
        from_attributes = True