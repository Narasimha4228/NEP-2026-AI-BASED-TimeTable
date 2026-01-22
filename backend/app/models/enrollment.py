from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.user import MongoBaseModel

class EnrollmentBase(BaseModel):
    student_id: str = Field(..., description="Student user ID")
    course_id: str = Field(..., description="Course ID")
    program_id: str = Field(..., description="Program ID")
    semester: int = Field(..., description="Semester number")
    academic_year: str = Field(..., description="Academic year")
    status: str = Field(default="enrolled", description="Enrollment status (enrolled, dropped, completed)")
    grade: Optional[str] = Field(None, description="Grade received")
    enrolled_at: datetime = Field(default_factory=datetime.utcnow)

class EnrollmentCreate(BaseModel):
    course_id: str
    program_id: str
    semester: int
    academic_year: str

class EnrollmentUpdate(BaseModel):
    status: Optional[str] = None
    grade: Optional[str] = None

class Enrollment(EnrollmentBase, MongoBaseModel):
    pass

class StudentEnrollmentSummary(BaseModel):
    student_id: str
    student_name: str
    program_name: str
    semester: int
    academic_year: str
    enrolled_courses: List[dict] = []
    total_credits: int = 0