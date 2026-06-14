from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# Pydantic schemas for user registration, authentication, and token responses.
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Password must be at least 8 characters."
    )

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None