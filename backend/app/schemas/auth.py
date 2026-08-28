from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import RoleEnum


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: RoleEnum
    phone: str | None = Field(default=None, max_length=32)
    university_id: str | None = None  # students self-registering under an HEI
    department: str | None = None  # student department
    roll_number: str | None = None  # student roll number


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    role: RoleEnum
    phone: str | None = None
    is_email_verified: bool = False