from pydantic import BaseModel, Field
from datetime import datetime

# Pydantic schemas for creating, updating, and returning Case resources.
class CaseCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
        description="Title of the case, e.g. 'Workplace 2024' or 'Personal relationship'."
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional description of the case context."
    )

class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)

class CaseResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True