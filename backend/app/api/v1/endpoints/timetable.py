from typing import List
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from app.models.user import User
from app.models.timetable import Timetable, TimetableCreate
from app.services.auth import get_current_active_user
from app.db.mongodb import db
from app.services.timetable.advanced_generator import AdvancedTimetableGenerator
import asyncio
import logging

router = APIRouter()

# =====================================================
# GET TIMETABLES (ROLE BASED FILTERING)
# =====================================================
@router.get("/", response_model=List[Timetable])
async def get_timetables(
    current_user: User = Depends(get_current_active_user),
):
    role = current_user.role.value  # ✅ FIX HERE

    if role == "admin":
        query = {}

    elif role == "faculty":
        if not current_user.faculty_id:
            raise HTTPException(
                status_code=400,
                detail="Faculty ID not assigned to this user"
            )

        query = {
            "entries.faculty_id": current_user.faculty_id
        }

    elif role == "student":
        if not current_user.group_id:
            raise HTTPException(
                status_code=400,
                detail="Student group not assigned to this user"
            )

        query = {
            "entries.group_id": current_user.group_id
        }

    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    timetables = await db.db.timetables.find(query).to_list(100)

    for t in timetables:
        t["id"] = str(t["_id"])
        del t["_id"]
        t["created_by"] = str(t["created_by"])
        t["program_id"] = str(t["program_id"])

    return timetables


# =====================================================
# GET SINGLE TIMETABLE
# =====================================================
@router.get("/{timetable_id}", response_model=Timetable)
async def get_timetable(
    timetable_id: str,
    current_user: User = Depends(get_current_active_user),
):
    timetable = await db.db.timetables.find_one(
        {"_id": ObjectId(timetable_id)}
    )

    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    role = current_user.role.value  # ✅ FIX HERE
    entries = timetable.get("entries", [])

    if role == "faculty":
        if not any(
            e.get("faculty_id") == current_user.faculty_id
            for e in entries
        ):
            raise HTTPException(status_code=403, detail="Access denied")

    if role == "student":
        if not any(
            e.get("group_id") == current_user.group_id
            for e in entries
        ):
            raise HTTPException(status_code=403, detail="Access denied")

    timetable["id"] = str(timetable["_id"])
    del timetable["_id"]
    timetable["created_by"] = str(timetable["created_by"])
    timetable["program_id"] = str(timetable["program_id"])

    return timetable


@router.get("/my")
async def get_my_timetable(
    current_user: User = Depends(get_current_active_user),
):
    """Return the most recent generated timetable for the current student, grouped by course."""
    # Only students get a personalized grouped view; faculty/admin can use other endpoints
    if current_user.role.value != "student":
        raise HTTPException(status_code=403, detail="Only students may access this endpoint")

    group_id = current_user.group_id
    if not group_id:
        raise HTTPException(status_code=400, detail="Student group not assigned to this user")

    # Find latest generated timetable that contains entries for this group
    timetable = await db.db.timetables.find_one(
        {"entries.group_id": group_id, "is_draft": False},
        sort=[("generated_at", -1)]
    )

    if not timetable:
        return {"message": "No generated timetable available for your group", "timetable": None}

    entries = timetable.get("entries", [])
    # Filter entries for this group
    my_entries = [e for e in entries if e.get("group_id") == group_id]

    # Group by course_code
    grouped = {}
    for e in my_entries:
        code = e.get("course_code") or e.get("course") or "UNKNOWN"
        if code not in grouped:
            grouped[code] = {
                "course_name": e.get("course_name") or e.get("course_name", ""),
                "sessions": []
            }
        grouped[code]["sessions"].append({
            "day": e.get("day") or e.get("time_slot", {}).get("day"),
            "start_time": e.get("start_time") or e.get("time_slot", {}).get("start_time"),
            "end_time": e.get("end_time") or e.get("time_slot", {}).get("end_time"),
            "room": e.get("room"),
            "faculty": e.get("faculty"),
            "is_lab": e.get("is_lab", False),
            "duration_minutes": e.get("duration_minutes") or e.get("session_duration")
        })

    return {
        "timetable_id": str(timetable["_id"]),
        "generated_at": timetable.get("generated_at"),
        "grouped_by_course": grouped
    }


# =====================================================
# CREATE TIMETABLE
# =====================================================
@router.post("/", response_model=Timetable)
async def create_timetable(
    timetable_data: TimetableCreate,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new timetable"""
    timetable_dict = timetable_data.model_dump()
    timetable_dict["created_by"] = ObjectId(current_user.id)
    timetable_dict["created_at"] = datetime.utcnow()
    timetable_dict["is_draft"] = True

    result = await db.db.timetables.insert_one(timetable_dict)
    timetable_dict["id"] = str(result.inserted_id)
    del timetable_dict["_id"]

    return Timetable(**timetable_dict)


# =====================================================
# UPDATE TIMETABLE
# =====================================================
@router.put("/{timetable_id}", response_model=Timetable)
async def update_timetable(
    timetable_id: str,
    timetable_data: dict,
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing timetable"""
    # Check if timetable exists and user has access
    existing = await db.db.timetables.find_one({"_id": ObjectId(timetable_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Timetable not found")

    # Role-based access control
    role = current_user.role.value
    if role == "faculty" and not any(
        e.get("faculty_id") == current_user.faculty_id for e in existing.get("entries", [])
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    elif role == "student" and not any(
        e.get("group_id") == current_user.group_id for e in existing.get("entries", [])
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    # Update the timetable
    update_data = {"$set": {**timetable_data, "updated_at": datetime.utcnow()}}
    await db.db.timetables.update_one({"_id": ObjectId(timetable_id)}, update_data)

    # Return updated timetable
    updated = await db.db.timetables.find_one({"_id": ObjectId(timetable_id)})
    updated["id"] = str(updated["_id"])
    del updated["_id"]
    updated["created_by"] = str(updated["created_by"])
    updated["program_id"] = str(updated["program_id"])

    return Timetable(**updated)


# =====================================================
# DELETE TIMETABLE
# =====================================================
@router.delete("/{timetable_id}")
async def delete_timetable(
    timetable_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Delete a timetable"""
    # Check if timetable exists
    existing = await db.db.timetables.find_one({"_id": ObjectId(timetable_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Timetable not found")

    # Only admin can delete timetables
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete timetables")

    await db.db.timetables.delete_one({"_id": ObjectId(timetable_id)})
    return {"message": "Timetable deleted successfully"}


# =====================================================
# GENERATE TIMETABLE
# =====================================================
@router.post("/{timetable_id}/generate")
async def generate_timetable(
    timetable_id: str,
    options: dict = None,
    current_user: User = Depends(get_current_active_user),
):
    """Generate timetable entries using AI/optimization"""
    # Check if timetable exists
    existing = await db.db.timetables.find_one({"_id": ObjectId(timetable_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Timetable not found")

    # Only admin can generate timetables
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can generate timetables")

    # Determine generation method and parameters
    opts = options or {}
    method = opts.get("method", "advanced")
    semester = existing.get("semester")
    program_id = str(existing.get("program_id")) if existing.get("program_id") else None

    logger = logging.getLogger(__name__)

    try:
        if method == "advanced":
            # Use AdvancedTimetableGenerator
            generator = AdvancedTimetableGenerator()

            # Load DB data (async) and apply any academic setup passed in options
            academic_setup = opts.get("academic_setup")
            await generator.load_from_database_with_setup(program_id, semester, academic_setup)

            # Run the synchronous generation in a threadpool to avoid blocking event loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, generator.generate_timetable, program_id, semester)

            if not result.get("success"):
                logger.error(f"Advanced generator failed: {result.get('error')}")
                raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))

            # Save generated entries into timetable document
            entries = result.get("schedule", [])
            update_doc = {
                "entries": entries,
                "is_draft": False,
                "generated_at": datetime.utcnow(),
                "generation_method": "advanced",
                "validation_status": "generated",
                "optimization_score": result.get("score"),
                "metadata": {
                    "generation_attempts": result.get("attempts_made"),
                    "statistics": result.get("statistics"),
                    "validation": result.get("validation")
                }
            }

            await db.db.timetables.update_one({"_id": ObjectId(timetable_id)}, {"$set": update_doc})

            return {
                "message": "Timetable generated successfully",
                "timetable_id": timetable_id,
                "status": "generated",
                "entries": entries,
                "score": result.get("score")
            }

        else:
            # Unsupported method; fallback to generic response
            raise HTTPException(status_code=400, detail=f"Unsupported generation method: {method}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during timetable generation")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# =====================================================
# EXPORT TIMETABLE
# =====================================================
@router.get("/{timetable_id}/export")
async def export_timetable(
    timetable_id: str,
    format: str = "excel",
    current_user: User = Depends(get_current_active_user),
):
    """Export timetable in specified format"""
    # Check if timetable exists and user has access
    existing = await db.db.timetables.find_one({"_id": ObjectId(timetable_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Timetable not found")

    role = current_user.role.value
    entries = existing.get("entries", [])

    if role == "faculty" and not any(
        e.get("faculty_id") == current_user.faculty_id for e in entries
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    elif role == "student" and not any(
        e.get("group_id") == current_user.group_id for e in entries
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    # TODO: Implement actual export logic
    # For now, return a placeholder
    if format == "json":
        return existing
    else:
        # Return placeholder for other formats
        return {"message": f"Export in {format} format not yet implemented"}


# =====================================================
# SAVE DRAFT TIMETABLE
# =====================================================
@router.post("/draft")
async def save_draft_timetable(
    draft_data: dict,
    current_user: User = Depends(get_current_active_user),
):
    """Save a draft timetable"""
    # Only admin can save drafts
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can save draft timetables")

    draft_data["created_by"] = ObjectId(current_user.id)
    draft_data["created_at"] = datetime.utcnow()
    draft_data["is_draft"] = True

    result = await db.db.timetables.insert_one(draft_data)
    draft_data["id"] = str(result.inserted_id)
    del draft_data["_id"]

    return {"message": "Draft saved successfully", "timetable_id": draft_data["id"]}
