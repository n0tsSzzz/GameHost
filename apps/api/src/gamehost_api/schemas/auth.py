from uuid import UUID

from gamehost_shared.enums import UserRole
from gamehost_shared.schemas import CamelModel


class RegisterRequest(CamelModel):
    email: str
    password: str


class LoginRequest(CamelModel):
    email: str
    password: str


class TokenResponse(CamelModel):
    access: str


class UserResponse(CamelModel):
    id: UUID
    email: str
    role: UserRole
    is_active: bool
