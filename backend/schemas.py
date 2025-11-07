from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Following the convention: class name lowercased -> collection name

class User(BaseModel):
    email: EmailStr
    password_hash: str = Field(min_length=10)
    role: str = "admin"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TestResponse(BaseModel):
    status: str
    db: bool
