from typing import List, Any, Dict
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
# HELPER: Convert ObjectIds to strings recursively
# =====================================================
def convert_objectid_to_str(obj: Any) -> Any:
    """Recursively convert ObjectId objects to strings."""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj

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
        # If no faculty_id assigned, return empty list
        if not current_user.faculty_id:
            return []

        query = {
            "entries.faculty_id": current_user.faculty_id
        }

    elif role == "student":
        # If no group_id assigned, return empty list
        if not current_user.group_id:
            return []

        query = {
            "entries.group_id": current_user.group_id,
            "is_draft": False
        }

    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    timetables = await db.db.timetables.find(query).to_list(100)

    result = []
    for t in timetables:
        # Convert all ObjectIds to strings recursively
        t = convert_objectid_to_str(t)
        t["id"] = t.pop("_id", None)
        result.append(t)

    return result


# =====================================================
# GET AVAILABLE FILTER OPTIONS
# =====================================================
@router.get("/options/filters", response_model=dict)
async def get_filter_options(
    current_user: User = Depends(get_current_active_user),
):
    """
    Return available options for timetable filtering.
    Returns programs, years, semesters, and sections from published timetables.
    """
    
    # Get all programs with published timetables
    programs_cursor = db.db.timetables.aggregate([
        {"$match": {"is_draft": False}},
        {"$group": {"_id": "$program_id"}},
    ])
    program_ids = await programs_cursor.to_list(None)
    program_ids = [p["_id"] for p in program_ids if p["_id"]]
    
    programs = []
    for pid in program_ids:
        try:
            prog = await db.db.programs.find_one({"_id": ObjectId(pid)})
        except Exception:
            prog = await db.db.programs.find_one({"_id": pid})
        
        if prog:
            programs.append({
                "id": str(prog.get("_id")),
                "code": prog.get("code"),  # department_code
                "name": prog.get("name") or prog.get("title"),
            })
    
    # Get all years from student groups in published timetables
    years_cursor = db.db.student_groups.aggregate([
        {"$group": {"_id": "$year"}},
        {"$sort": {"_id": 1}},
    ])
    years = await years_cursor.to_list(None)
    years = sorted([y["_id"] for y in years if y["_id"] is not None])
    
    # Get all semesters from student groups
    semesters_cursor = db.db.student_groups.aggregate([
        {"$group": {"_id": "$semester"}},
        {"$sort": {"_id": 1}},
    ])
    semesters = await semesters_cursor.to_list(None)
    semesters = sorted([s["_id"] for s in semesters if s["_id"] is not None], key=str)
    
    # Get all sections from student groups
    sections_cursor = db.db.student_groups.aggregate([
        {"$group": {"_id": "$section"}},
        {"$sort": {"_id": 1}},
    ])
    sections = await sections_cursor.to_list(None)
    sections = sorted([s["_id"] for s in sections if s["_id"] is not None])
    
    return {
        "programs": programs,
        "years": years,
        "semesters": semesters,
        "sections": sections,
    }


# =====================================================
# GET MY TIMETABLE (FOR STUDENTS) - MUST COME BEFORE /{timetable_id}
# =====================================================
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

    # Fetch the student group to obtain program/year/section/semester
    try:
        group_doc = await db.db.student_groups.find_one({"_id": ObjectId(group_id)})
    except Exception:
        group_doc = await db.db.student_groups.find_one({"_id": group_id})

    if not group_doc:
        raise HTTPException(status_code=404, detail="Student group not found")

    program_id = group_doc.get("program_id")
    year = group_doc.get("year")
    section = group_doc.get("section")
    semester = group_doc.get("semester")

    # Build a robust query: prefer matching top-level program_id and entries.group_id
    query = {"is_draft": False, "entries.group_id": group_id}
    if program_id:
        # program_id may be stored as ObjectId or string
        try:
            query["program_id"] = ObjectId(program_id)
        except Exception:
            query["program_id"] = program_id

    # Find latest completed/published timetable matching these values
    timetable = await db.db.timetables.find_one(query, sort=[("generated_at", -1)])

    if not timetable:
        return {"message": "No timetable available for your group", "timetable": None, "entries": []}

    # Convert ObjectIds to strings
    timetable = convert_objectid_to_str(timetable)
    entries = timetable.get("entries", [])
    # Filter entries for this group only
    my_entries = [e for e in entries if e.get("group_id") == group_id]

    # Get department code from stored value or fetch from program
    dept_code = timetable.get("department_code")
    if not dept_code and timetable.get("program_id"):
        try:
            prog = await db.db.programs.find_one({"_id": ObjectId(timetable.get("program_id"))})
            if not prog:
                prog = await db.db.programs.find_one({"_id": timetable.get("program_id")})
        except Exception:
            prog = await db.db.programs.find_one({"_id": timetable.get("program_id")})
        if prog:
            dept_code = prog.get("code")

    return {
        "department": dept_code,  # For backward compatibility
        "department_code": dept_code,
        "year": year,
        "section": section,
        "semester": semester,
        "timetable_id": str(timetable.get("_id")),
        "generated_at": timetable.get("generated_at").isoformat() if timetable.get("generated_at") else None,
        "entries": my_entries
    }


# =====================================================
# FILTER TIMETABLES BY METADATA (For Students)
# =====================================================
@router.get("/filter", response_model=dict)
async def filter_timetables(
    program_id: str = None,
    department_code: str = None,
    year: int = None,
    semester: str = None,
    section: str = None,
    current_user: User = Depends(get_current_active_user),
):
    """
    Filter timetables by department, year, semester, section.
    Returns the latest matching published timetable.
    
    Query Parameters:
    - program_id: MongoDB ObjectId of program (department) - optional
    - department_code: Program code (e.g., "CSE", "ECE") - preferred, more stable
    - year: Academic year (1, 2, 3, 4)
    - semester: Semester identifier (Odd/Even or 1-8)
    - section: Section identifier (A, B, C, etc.)
    """
    
    # Build query filter
    query = {"is_draft": False}
    
    # If department_code is provided, use it to find program_id
    if department_code:
        try:
            program = await db.db.programs.find_one({"code": department_code})
            if program:
                query["program_id"] = program.get("_id")
                query["department_code"] = department_code
        except Exception as e:
            print(f"Error finding program by code: {e}")
    
    # Fall back to program_id if provided and department_code wasn't used
    if program_id and "program_id" not in query:
        try:
            query["program_id"] = ObjectId(program_id)
        except Exception:
            query["program_id"] = program_id
    
    # If we have year, semester, section - validate they exist in student_groups
    # But don't filter timetable entries by them - just use for validation
    metadata_filter = {}
    if year is not None or semester is not None or section is not None:
        metadata_filter = {}
        if year is not None:
            metadata_filter["year"] = year
        if semester is not None:
            metadata_filter["semester"] = semester
        if section is not None:
            metadata_filter["section"] = section
        if department_code or program_id:
            if department_code:
                # Find program by code
                try:
                    program = await db.db.programs.find_one({"code": department_code})
                    if program:
                        metadata_filter["program_id"] = program.get("_id")
                except Exception:
                    pass
            elif program_id:
                try:
                    metadata_filter["program_id"] = ObjectId(program_id)
                except Exception:
                    metadata_filter["program_id"] = program_id
        
        # Verify student groups with this metadata exist
        matching_groups = await db.db.student_groups.find(metadata_filter).to_list(None)
        if not matching_groups:
            print(f"No student groups found for filters: {metadata_filter}")
            return {"message": "No timetable available for selected filters", "timetable": None, "entries": []}
        
        print(f"Found {len(matching_groups)} matching student groups")
    
    # Find latest matching timetable
    print(f"Timetable query: {query}")
    timetable = await db.db.timetables.find_one(query, sort=[("generated_at", -1)])
    
    if not timetable:
        print(f"No timetable found for query: {query}")
        return {"message": "No timetable available for selected filters", "timetable": None, "entries": []}
    
    print(f"Found timetable: {timetable.get('_id')}")
    
    # Convert ObjectIds to strings
    timetable = convert_objectid_to_str(timetable)
    entries = timetable.get("entries", [])
    print(f"Total entries in timetable: {len(entries)}")
    
    # Return all entries for the matching timetable
    # (No need to filter by group_id since the timetable was already matched)
    my_entries = entries
    print(f"Returning {len(my_entries)} entries to client")
    
    # Get department code from stored value or fetch from program
    dept_code = timetable.get("department_code")
    if not dept_code and timetable.get("program_id"):
        try:
            prog = await db.db.programs.find_one({"_id": ObjectId(timetable.get("program_id"))})
            if not prog:
                prog = await db.db.programs.find_one({"_id": timetable.get("program_id")})
        except Exception:
            prog = await db.db.programs.find_one({"_id": timetable.get("program_id")})
        if prog:
            dept_code = prog.get("code")
    
    return {
        "department_code": dept_code,
        "year": year,
        "semester": semester,
        "section": section,
        "timetable_id": str(timetable.get("_id")),
        "generated_at": timetable.get("generated_at").isoformat() if timetable.get("generated_at") else None,
        "entries": my_entries
    }


# =====================================================
# LIST ALL PUBLISHED TIMETABLES
# =====================================================
@router.get("/list/all", response_model=dict)
async def list_all_timetables(
    department_code: str = None,
    current_user: User = Depends(get_current_active_user),
):
    """
    List all published timetables, optionally filtered by department.
    Returns list of available timetables for browsing.
    """
    query = {"is_draft": False}
    
    # If department filter provided, find program by code
    if department_code:
        program = await db.db.programs.find_one({"code": department_code})
        if program:
            query["program_id"] = program.get("_id")
    
    # Get all matching published timetables
    timetables = await db.db.timetables.find(query).sort("generated_at", -1).to_list(None)
    
    # Format response with key info
    formatted = []
    for tt in timetables:
        formatted.append({
            "id": str(tt.get("_id")),
            "title": tt.get("title", "Untitled"),
            "department_code": tt.get("department_code", "?"),
            "semester": tt.get("semester"),
            "entries_count": len(tt.get("entries", [])),
            "generated_at": tt.get("generated_at").isoformat() if tt.get("generated_at") else None,
        })
    
    return {
        "count": len(formatted),
        "timetables": formatted
    }


# =====================================================
# GET TIMETABLE BY ID (PUBLIC - FOR BROWSING)
# =====================================================
@router.get("/public/{timetable_id}", response_model=dict)
async def get_timetable_public(
    timetable_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a published timetable by ID.
    Public endpoint - any authenticated user can view published timetables.
    No permission checks - allows students to browse all published timetables.
    """
    try:
        timetable = await db.db.timetables.find_one(
            {"_id": ObjectId(timetable_id), "is_draft": False}
        )
    except Exception:
        timetable = await db.db.timetables.find_one(
            {"_id": timetable_id, "is_draft": False}
        )

    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    # Convert all ObjectIds to strings
    timetable = convert_objectid_to_str(timetable)
    timetable["id"] = timetable.pop("_id", None)

    return timetable


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

    # Convert all ObjectIds to strings
    timetable = convert_objectid_to_str(timetable)
    timetable["id"] = timetable.pop("_id", None)

    return timetable


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
    
    # Fetch and store the program's department code
    try:
        program = await db.db.programs.find_one({"_id": ObjectId(timetable_dict["program_id"])})
    except Exception:
        program = await db.db.programs.find_one({"_id": timetable_dict["program_id"]})
    
    if program:
        timetable_dict["department_code"] = program.get("code")

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

