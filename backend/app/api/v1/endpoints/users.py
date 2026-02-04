from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import User, UserCreate, UserUpdate, UserRole
from app.services.auth import get_current_active_user, get_password_hash
from app.db.mongodb import db
from bson import ObjectId

router = APIRouter()

# -----------------------------
# Helper: Mongo → API
# -----------------------------
def serialize_user(user: dict) -> dict:
    user["id"] = str(user["_id"])
    user.pop("_id", None)    
    # Convert ObjectId fields to strings
    if "faculty_id" in user and user["faculty_id"]:
        user["faculty_id"] = str(user["faculty_id"]) if not isinstance(user["faculty_id"], str) else user["faculty_id"]
    if "group_id" in user and user["group_id"]:
        user["group_id"] = str(user["group_id"]) if not isinstance(user["group_id"], str) else user["group_id"]
    
    # Remove hashed_password before returning
    user.pop("hashed_password", None)
    return user


# -----------------------------
# GET ALL USERS (ADMIN ONLY)
# -----------------------------
@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
):
    # Check admin role - handle both enum and string values
    user_role = current_user.role
    if isinstance(user_role, UserRole):
        user_role = user_role.value
    
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    users = await db.db.users.find().skip(skip).limit(limit).to_list(length=limit)
    return [serialize_user(u) for u in users]


# -----------------------------
# GET CURRENT USER
# -----------------------------
@router.get("/me", response_model=User)
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    return current_user


# -----------------------------
# GET USER BY ID
# -----------------------------
@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
):
    # Admin can view anyone, others only themselves
    if current_user.role != UserRole.admin and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user = await db.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return serialize_user(user)


# -----------------------------
# CREATE USER (ADMIN ONLY)
# -----------------------------
@router.post("/", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    existing = await db.db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_dict = user_data.model_dump(exclude={"password", "name"})
    user_dict["hashed_password"] = get_password_hash(user_data.password)

    result = await db.db.users.insert_one(user_dict)
    user = await db.db.users.find_one({"_id": result.inserted_id})

    return serialize_user(user)


# -----------------------------
# UPDATE USER
# -----------------------------
@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.admin and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user = await db.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    if update_data:
        await db.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
        )

    updated = await db.db.users.find_one({"_id": ObjectId(user_id)})
    return serialize_user(updated)


# -----------------------------
# DELETE USER (ADMIN ONLY)
# -----------------------------
@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    user = await db.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.db.users.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}


# -----------------------------
# CHANGE ROLE (ADMIN ONLY)
# -----------------------------
@router.patch("/{user_id}/role")
async def update_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    user = await db.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": new_role}},
    )

    return {
        "message": "Role updated successfully",
        "user_id": user_id,
        "new_role": new_role,
    }
