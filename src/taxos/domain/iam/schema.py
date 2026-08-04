"""API schemas for Identity & Access Management."""
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class OrganizationCreate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

class MembershipCreate(BaseModel):
    email: EmailStr
    role: str

class MembershipResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int
    role: str
    joined_at: datetime
