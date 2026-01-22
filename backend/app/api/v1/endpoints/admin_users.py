from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.services.auth import get_current_active_user
from app.models.user import User, UserRole
from app.db.mongodb import db
from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from app.models.user import User

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
@router.get("/users")
async def list_users(
    search: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    """
    Admin: list users (filter by email/name)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    query = {}
    if search:
        query = {
            "$or": [
                {"email": {"$regex": search, "$options": "i"}},
                {"full_name": {"$regex": search, "$options": "i"}},
            ]
        }

    users = await db.db.users.find(query).to_list(length=100)

    for u in users:
        u["_id"] = str(u["_id"])

    return users


@router.patch("/users/{user_id}/role")
async def change_user_role(
    user_id: str,
    new_role: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Admin: change user role
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if new_role not in ["admin", "faculty", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = await db.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": new_role}}
    )

    return {
        "message": "Role updated successfully",
        "user_id": user_id,
        "new_role": new_role
    }

