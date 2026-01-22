from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth import get_current_active_user
from app.models.user import User, UserRole
from app.models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate, StudentEnrollmentSummary
from app.db.mongodb import db
from bson import ObjectId
from datetime import datetime

router = APIRouter()

# -----------------------------
# Helper: Mongo → API
# -----------------------------
def serialize_enrollment(enrollment: dict) -> dict:
    enrollment["id"] = str(enrollment["_id"])
    enrollment.pop("_id", None)
    return enrollment

# -----------------------------
# ENROLL IN COURSE (STUDENTS)
# -----------------------------
@router.post("/", response_model=Enrollment)
async def enroll_course(
    enrollment_data: EnrollmentCreate,
    current_user: User = Depends(get_current_active_user),
):
    """Allow students to enroll in courses"""
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="Only students can enroll in courses")

    # Check if course exists and is active
    course = await db.db.courses.find_one({
        "_id": ObjectId(enrollment_data.course_id),
        "is_active": True
    })
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or inactive")

    # Check if student is already enrolled
    existing = await db.db.enrollments.find_one({
        "student_id": current_user.id,
        "course_id": enrollment_data.course_id,
        "academic_year": enrollment_data.academic_year
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this course")

    # Create enrollment
    enrollment_doc = {
        "student_id": current_user.id,
        "course_id": enrollment_data.course_id,
        "program_id": enrollment_data.program_id,
        "semester": enrollment_data.semester,
        "academic_year": enrollment_data.academic_year,
        "status": "enrolled",
        "enrolled_at": datetime.utcnow()
    }

    result = await db.db.enrollments.insert_one(enrollment_doc)
    enrollment_doc["_id"] = result.inserted_id

    return serialize_enrollment(enrollment_doc)

# -----------------------------
# GET STUDENT ENROLLMENTS
# -----------------------------
@router.get("/my-enrollments", response_model=List[Enrollment])
async def get_my_enrollments(
    academic_year: Optional[str] = None,
    semester: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's enrollments"""
    filter_query = {"student_id": current_user.id}

    if academic_year:
        filter_query["academic_year"] = academic_year
    if semester:
        filter_query["semester"] = semester

    enrollments = await db.db.enrollments.find(filter_query).to_list(length=None)
    return [serialize_enrollment(e) for e in enrollments]

# -----------------------------
# DROP COURSE (STUDENTS)
# -----------------------------
@router.put("/{enrollment_id}/drop")
async def drop_course(
    enrollment_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Allow students to drop enrolled courses"""
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=403, detail="Only students can drop courses")

    enrollment = await db.db.enrollments.find_one({
        "_id": ObjectId(enrollment_id),
        "student_id": current_user.id
    })
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    await db.db.enrollments.update_one(
        {"_id": ObjectId(enrollment_id)},
        {"$set": {"status": "dropped"}}
    )

    return {"message": "Course dropped successfully"}

# -----------------------------
# GET COURSE ENROLLMENTS (ADMIN/FACULTY)
# -----------------------------
@router.get("/course/{course_id}", response_model=List[Enrollment])
async def get_course_enrollments(
    course_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get all enrollments for a course (admin/faculty only)"""
    if current_user.role not in [UserRole.admin, UserRole.faculty]:
        raise HTTPException(status_code=403, detail="Access denied")

    enrollments = await db.db.enrollments.find({"course_id": course_id}).to_list(length=None)
    return [serialize_enrollment(e) for e in enrollments]

# -----------------------------
# GET STUDENT ENROLLMENT SUMMARY (ADMIN)
# -----------------------------
@router.get("/summary/{student_id}", response_model=StudentEnrollmentSummary)
async def get_student_enrollment_summary(
    student_id: str,
    academic_year: str,
    semester: int,
    current_user: User = Depends(get_current_active_user),
):
    """Get enrollment summary for a student (admin only)"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get student info
    student = await db.db.users.find_one({"_id": ObjectId(student_id)})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get program info
    program = await db.db.programs.find_one({"_id": ObjectId(student.get("program_id"))})

    # Get enrollments
    enrollments = await db.db.enrollments.find({
        "student_id": student_id,
        "academic_year": academic_year,
        "semester": semester,
        "status": "enrolled"
    }).to_list(length=None)

    # Get course details
    enrolled_courses = []
    total_credits = 0
    for enrollment in enrollments:
        course = await db.db.courses.find_one({"_id": ObjectId(enrollment["course_id"])})
        if course:
            enrolled_courses.append({
                "course_id": str(course["_id"]),
                "course_code": course["code"],
                "course_name": course["name"],
                "credits": course["credits"]
            })
            total_credits += course["credits"]

    return StudentEnrollmentSummary(
        student_id=student_id,
        student_name=student["full_name"],
        program_name=program["name"] if program else "Unknown",
        semester=semester,
        academic_year=academic_year,
        enrolled_courses=enrolled_courses,
        total_credits=total_credits
    )