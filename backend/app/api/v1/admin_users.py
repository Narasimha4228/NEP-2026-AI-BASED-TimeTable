from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.services.auth import get_current_active_user
from app.models.user import User, UserRole
from app.db.mongodb import db

router = APIRouter()

# -------------------------------
# ADMIN ONLY CHECK
# -------------------------------
def admin_only(user: User):
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin only")

# -------------------------------
# ASSIGN FACULTY ROLE
# -------------------------------
@router.put("/users/{user_id}/make-faculty")
async def make_faculty(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    admin_only(current_user)

    result = await db.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "role": "faculty",
            "faculty_id": user_id
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User promoted to faculty"}

# -------------------------------
# ASSIGN STUDENT GROUP
# -------------------------------
@router.put("/users/{user_id}/assign-group/{group_id}")
async def assign_student_group(
    user_id: str,
    group_id: str,
    current_user: User = Depends(get_current_active_user)
):
    admin_only(current_user)

    result = await db.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "role": "student",
            "group_id": group_id
        }}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Student group assigned"}
