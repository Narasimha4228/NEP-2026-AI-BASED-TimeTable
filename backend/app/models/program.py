from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.user import MongoBaseModel

class ProgramBase(BaseModel):
    name: str = Field(..., description="Program name")
    code: Optional[str] = Field(None, description="Program code")
    type: Optional[str] = Field(None, description="Program type (FYUP, B.Ed, M.Ed, ITEP)")
    department: str = Field(..., description="Department offering the program")
    duration_years: Optional[int] = Field(None, description="Duration in years")
    total_semesters: Optional[int] = Field(None, description="Total number of semesters")
    credits_required: Optional[int] = Field(None, description="Total credits required for completion")
    description: Optional[str] = Field(None, description="Program description")
    is_active: bool = Field(True, description="Whether the program is active")

class ProgramCreate(BaseModel):
    name: str
    code: str
    type: str
    department: str
    duration_years: int
    total_semesters: int
    credits_required: int
    description: Optional[str] = None


class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    type: Optional[str] = None
    department: Optional[str] = None
    duration_years: Optional[int] = None
    total_semesters: Optional[int] = None
    credits_required: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Program(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    department: str
    code: Optional[str] = None
    type: Optional[str] = None
    duration_years: Optional[int] = None
    total_semesters: Optional[int] = None
    credits_required: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        from_attributes = True
