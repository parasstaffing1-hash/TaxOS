"""Domain entities for Identity & Access Management."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    is_active: bool
    created_at: datetime


class OrganizationEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime


class MembershipEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    organization_id: int
    role: str
    joined_at: datetime


class APIKeyEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int
    name: str
    key_hash: str
    created_at: datetime
    expires_at: datetime | None = None


class AuditLogEntity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None
    organization_id: int | None
    action: str
    resource: str
    timestamp: datetime
