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
# HELPER: Normalize timetable entries format
# =====================================================
def normalize_timetable_entry(entry: Dict) -> Dict:
    """
    Normalize entry format from database to frontend format.
    Handles both flat entries (day, start_time, end_time) and nested (time_slot object).
    """
    if not entry:
        return entry
    
    # If already has time_slot, return as-is
    if "time_slot" in entry:
        return entry
    
    # Transform flat structure to nested time_slot
    normalized = {k: v for k, v in entry.items() if k not in ['day', 'start_time', 'end_time']}
    
    # Create time_slot object
    normalized["time_slot"] = {
        "day": entry.get("day", "Monday"),
        "start_time": entry.get("start_time", "09:00"),
        "end_time": entry.get("end_time", "10:00"),
        "duration_minutes": entry.get("duration_minutes", 50)
    }
    
    # Ensure course_id and faculty_id exist (use codes if IDs not available)
    if "course_id" not in normalized and "course_code" in normalized:
        normalized["course_id"] = normalized["course_code"]
    if "faculty_id" not in normalized and "faculty" in normalized:
        normalized["faculty_id"] = normalized["faculty"]
    if "room_id" not in normalized and "room" in normalized:
        normalized["room_id"] = normalized["room"]
    
    return normalized

# =====================================================
# GET TIMETABLES (ROLE BASED FILTERING)
# =====================================================
@router.get("/")
async def get_timetables(
    current_user: User = Depends(get_current_active_user),
):
    try:
        role = current_user.role.value  # ✅ FIX HERE

        if role == "admin":
            # Admin sees ALL timetables (both drafts and published)
            # Show both drafts and published for editing purposes
            query = {}

        elif role == "faculty":
            # If no faculty_id assigned, return empty list
            if not current_user.faculty_id:
                return []

            query = {
                "entries.faculty_id": current_user.faculty_id,
                "is_draft": False  # Faculty only sees published timetables
            }

        elif role == "student":
            # Students see published timetables
            # If group_id is assigned, filter by group; otherwise show all published timetables
            if current_user.group_id:
                query = {
                    "$or": [
                        {"entries.group_id": current_user.group_id},
                        {"entries.student_ids": ObjectId(current_user.id)}
                    ],
                    "is_draft": False
                }
            else:
                # If no group assigned, show all published timetables
                query = {
                    "is_draft": False
                }

        else:
            raise HTTPException(status_code=403, detail="Invalid role")

        timetables = await db.db.timetables.find(query).sort("created_at", -1).to_list(None)

        result = []
        for t in timetables:
            # Convert all ObjectIds to strings recursively
            t = convert_objectid_to_str(t)
            t["id"] = t.pop("_id", None)
            
            # Normalize entries format for frontend
            if "entries" in t and t["entries"]:
                t["entries"] = [normalize_timetable_entry(entry) for entry in t["entries"]]
            
            result.append(t)

        return result
    except Exception as e:
        logging.error(f"❌ Error in get_timetables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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
    
    # Normalize entries format for frontend
    my_entries = [normalize_timetable_entry(entry) for entry in my_entries]

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
    
    # Normalize entries format for frontend
    my_entries = [normalize_timetable_entry(entry) for entry in my_entries]
    
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
    
    # Normalize entries format for frontend
    if "entries" in timetable and timetable["entries"]:
        timetable["entries"] = [normalize_timetable_entry(entry) for entry in timetable["entries"]]

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
    
    # Normalize entries format for frontend
    if "entries" in timetable and timetable["entries"]:
        timetable["entries"] = [normalize_timetable_entry(entry) for entry in timetable["entries"]]

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
    try:
        print(f"🔧 DEBUG: Creating timetable with data: {timetable_data.dict()}")
        timetable_dict = timetable_data.model_dump()
        
        # Convert program_id to ObjectId for database storage
        try:
            timetable_dict["program_id"] = ObjectId(timetable_dict["program_id"])
        except Exception:
            pass  # Already an ObjectId
        
        timetable_dict["created_by"] = ObjectId(current_user.id)  # Store as ObjectId in DB
        timetable_dict["created_at"] = datetime.utcnow()
        
        # Preserve is_draft status
        if "is_draft" not in timetable_dict:
            timetable_dict["is_draft"] = True
        
        # Fetch and store the program's department code
        try:
            program = await db.db.programs.find_one({"_id": timetable_dict["program_id"]})
            if program:
                timetable_dict["department_code"] = program.get("code")
        except Exception as e:
            print(f"⚠️ DEBUG: Could not fetch program: {str(e)}")

        result = await db.db.timetables.insert_one(timetable_dict)
        timetable_dict["_id"] = str(result.inserted_id)  # Convert to string immediately
        
        # Convert back to strings for response
        timetable_dict["id"] = str(result.inserted_id)
        timetable_dict["created_by"] = str(timetable_dict["created_by"])  # Convert to string for response
        timetable_dict["program_id"] = str(timetable_dict["program_id"])  # Convert to string for response
        
        print(f"✅ DEBUG: Timetable created with ID: {timetable_dict['id']}")

        return Timetable(**timetable_dict)
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.exception("Error creating timetable")
        print(f"❌ DEBUG: Error creating timetable: {str(e)}")
        print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error creating timetable: {str(e)}")


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
    try:
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

        # Prepare update data
        update_dict = {**timetable_data, "updated_at": datetime.utcnow()}
        
        # Convert program_id to ObjectId if it's a string
        if "program_id" in update_dict and isinstance(update_dict["program_id"], str):
            try:
                update_dict["program_id"] = ObjectId(update_dict["program_id"])
            except Exception:
                pass

        # Update the timetable
        update_data = {"$set": update_dict}
        await db.db.timetables.update_one({"_id": ObjectId(timetable_id)}, update_data)

        # Return updated timetable
        updated = await db.db.timetables.find_one({"_id": ObjectId(timetable_id)})
        updated["id"] = str(updated["_id"])
        updated["created_by"] = str(updated["created_by"]) if isinstance(updated.get("created_by"), ObjectId) else updated.get("created_by")
        updated["program_id"] = str(updated["program_id"]) if isinstance(updated.get("program_id"), ObjectId) else updated.get("program_id")

        return Timetable(**updated)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ DEBUG: Error updating timetable: {str(e)}")
        print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating timetable: {str(e)}")


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
    request_body: dict = None,
    current_user: User = Depends(get_current_active_user),
):
    """Generate timetable entries using AI/optimization with user-provided data"""
    # Check if timetable exists
    try:
        existing = await db.db.timetables.find_one({"_id": ObjectId(timetable_id)})
    except Exception:
        existing = await db.db.timetables.find_one({"_id": timetable_id})
    
    if not existing:
        raise HTTPException(status_code=404, detail="Timetable not found")

    # Only admin can generate timetables
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can generate timetables")

    # Extract generation options and user data
    opts = request_body or {}
    method = opts.get("method", "advanced")
    semester = existing.get("semester")
    program_id = str(existing.get("program_id")) if existing.get("program_id") else None
    
    # Get academic setup (user-provided data from frontend)
    academic_setup = opts.get("academic_setup", {})
    user_courses = academic_setup.get("courses", [])
    user_faculty = academic_setup.get("faculty", [])
    user_rooms = academic_setup.get("rooms", [])
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 Generation request - User courses count: {len(user_courses)}, Faculty count: {len(user_faculty)}")

    try:
        if method == "advanced":
            # Use AdvancedTimetableGenerator
            generator = AdvancedTimetableGenerator()

            # If user provided data, use it; otherwise load from database
            if user_courses and len(user_courses) > 0:
                logger.info(f"📥 Using user-provided data: {len(user_courses)} courses")
                # Load with user-provided setup data
                await generator.load_from_database_with_setup(program_id, semester, academic_setup)
            else:
                # Fallback to database data
                logger.info("📥 Using database data (no user courses provided)")
                await generator.load_from_database_with_setup(program_id, semester, academic_setup)

            # Run the synchronous generation in a threadpool to avoid blocking event loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, generator.generate_timetable, program_id, semester)

            if not result.get("success"):
                logger.error(f"Advanced generator failed: {result.get('error')}")
                raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))

            # Save generated entries into timetable document
            entries = result.get("schedule", [])
            
            # ✅ NEW: Validate faculty max periods per day constraint
            faculty_max_per_day = 1  # Default to 1, can be overridden by metadata
            if "metadata" in existing and isinstance(existing["metadata"], dict):
                constraints = existing["metadata"].get("constraints", {})
                faculty_max_per_day = constraints.get("faculty_max_periods_per_day", 1)
            
            # Check constraint: faculty max periods per day
            faculty_periods_by_day = {}  # {faculty_id: {day: count}}
            for entry in entries:
                faculty_id = entry.get("faculty_id") or entry.get("faculty")
                day = entry.get("day") or (entry.get("time_slot", {}).get("day") if isinstance(entry.get("time_slot"), dict) else None)
                
                if faculty_id and day:
                    if faculty_id not in faculty_periods_by_day:
                        faculty_periods_by_day[faculty_id] = {}
                    if day not in faculty_periods_by_day[faculty_id]:
                        faculty_periods_by_day[faculty_id][day] = 0
                    faculty_periods_by_day[faculty_id][day] += 1
            
            # Check for violations
            violations = []
            for faculty_id, days_dict in faculty_periods_by_day.items():
                for day, count in days_dict.items():
                    if count > faculty_max_per_day:
                        violations.append(f"Faculty {faculty_id} has {count} periods on {day} (max: {faculty_max_per_day})")
            
            if violations:
                logger.warning(f"⚠️ Faculty constraint violations detected: {violations}")
                print(f"⚠️ Faculty constraint violations: {violations}")
            
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
                    "validation": result.get("validation"),
                    "constraint_violations": violations if violations else []
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
    try:
        # Convert program_id to ObjectId
        if "program_id" in draft_data and isinstance(draft_data["program_id"], str):
            try:
                draft_data["program_id"] = ObjectId(draft_data["program_id"])
            except Exception:
                pass
        
        draft_data["created_by"] = ObjectId(current_user.id)
        draft_data["created_at"] = datetime.utcnow()
        draft_data["is_draft"] = True

        result = await db.db.timetables.insert_one(draft_data)
        draft_data["id"] = str(result.inserted_id)
        draft_data["_id"] = result.inserted_id
        draft_data["created_by"] = str(draft_data["created_by"])
        draft_data["program_id"] = str(draft_data.get("program_id", ""))
        
        # Return the full timetable object instead of just a message
        return {
            "id": draft_data["id"],
            "_id": str(draft_data["_id"]),
            "title": draft_data.get("title"),
            "program_id": draft_data.get("program_id"),
            "semester": draft_data.get("semester"),
            "academic_year": draft_data.get("academic_year"),
            "is_draft": True,
            "created_by": draft_data["created_by"],
            "created_at": draft_data["created_at"],
            "entries": draft_data.get("entries", []),
            "metadata": draft_data.get("metadata", {}),
        }
    except Exception as e:
        import traceback
        print(f"❌ DEBUG: Error saving draft: {str(e)}")
        print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error saving draft: {str(e)}")

