from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    full_name: str
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    designation: Optional[str] = None
    region: Optional[str] = None
    institution_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    designation: Optional[str] = None
    region: Optional[str] = None
    institution_id: Optional[int] = None
