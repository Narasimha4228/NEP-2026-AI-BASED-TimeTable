from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from bson import ObjectId
from enum import Enum

# -----------------------------
# Role Enum (STRICT)
# -----------------------------
class UserRole(str, Enum):
    admin = "admin"
    faculty = "faculty"
    student = "student"


# -----------------------------
# MongoDB Base Model
# -----------------------------
class MongoBaseModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "populate_by_name": True,
        "by_alias": True
    }


# -----------------------------
# User Base
# -----------------------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True
    role: UserRole = UserRole.student

    # ONLY ONE of these is used based on role
    faculty_id: Optional[str] = None   # for faculty
    group_id: Optional[str] = None     # for students


# -----------------------------
# User Create (Signup)
# -----------------------------
class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    full_name: Optional[str] = None
    password: str

    role: UserRole = UserRole.student

    faculty_id: Optional[str] = None
    group_id: Optional[str] = None

    is_active: bool = True

    @field_validator("full_name", mode="before")
    @classmethod
    def set_full_name(cls, v, info):
        if v is None and "name" in info.data:
            return info.data["name"]
        if v is None:
            raise ValueError("full_name or name is required")
        return v

    @field_validator("faculty_id", mode="after")
    @classmethod
    def validate_faculty(cls, v, info):
        if info.data.get("role") == UserRole.faculty and not v:
            raise ValueError("faculty_id is required for faculty users")
        return v

    # Removed group_id validation for initial registration - groups can be assigned later


# -----------------------------
# User Update
# -----------------------------
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    faculty_id: Optional[str] = None
    group_id: Optional[str] = None


# -----------------------------
# User in DB
# -----------------------------
class UserInDB(UserBase, MongoBaseModel):
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# -----------------------------
# User Response
# -----------------------------
class User(UserBase, MongoBaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
