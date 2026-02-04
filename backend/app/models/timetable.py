from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.user import MongoBaseModel


class TimetableEntry(BaseModel):
    faculty_id: Optional[str] = None
    group_id: Optional[str] = None
    subject: Optional[str] = None
    room: Optional[str] = None
    day: Optional[str] = None
    slot: Optional[str] = None


class TimetableBase(BaseModel):
    title: Optional[str] = None
    program_id: str
    department_code: Optional[str] = None  # Store department code for direct filtering
    semester: int
    academic_year: Optional[str] = None
    entries: List[TimetableEntry] = []
    is_draft: bool = True


class TimetableCreate(BaseModel):
    title: str
    program_id: str
    semester: int
    academic_year: str


class Timetable(TimetableBase, MongoBaseModel):
    created_by: str
    faculty_ids: List[str] = []
    group_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    group_id: Optional[str] = None
    validation_status: Optional[str] = None
    generated_at: Optional[datetime] = None
    generation_method: Optional[str] = None
    metadata: Optional[dict] = None
    optimization_score: Optional[int] = None
    department_code: Optional[str] = None  # Department code for filtering
