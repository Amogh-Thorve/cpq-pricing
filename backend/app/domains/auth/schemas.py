from pydantic import BaseModel, EmailStr
from typing import Optional
from backend.app.domains.auth.models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.SALES_REP

class UserCreate(UserBase):
    """
    Schema for user registration.
    """
    password: str

class UserUpdate(BaseModel):
    """
    Schema for updating user details.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserRead(UserBase):
    """
    Schema returned when reading user details.
    """
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    """
    Schema representing a generated access token response.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserRead

class TokenPayload(BaseModel):
    """
    Internal schema representing the verified claims inside the JWT token.
    """
    sub: Optional[str] = None
    exp: Optional[int] = None

class LoginRequest(BaseModel):
    """
    Schema representing user login credentials.
    """
    email: EmailStr
    password: str
