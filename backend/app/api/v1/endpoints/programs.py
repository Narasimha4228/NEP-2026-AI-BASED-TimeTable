from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import User
from app.models.program import Program, ProgramCreate, ProgramUpdate
from app.services.auth import get_current_active_user
from app.db.mongodb import db
from bson import ObjectId

router = APIRouter()

@router.get("/")
async def get_programs(
    skip: int = Query(0, ge=0, description="Number of programs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of programs to return"),
    program_type: Optional[str] = Query(None, description="Filter by program type"),
    department: Optional[str] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all academic programs with optional filtering.
    """
    filter_query = {}
    if program_type:
        filter_query["type"] = program_type
    if department:
        filter_query["department"] = department
    
    programs_data = await db.db.programs.find(filter_query).skip(skip).limit(limit).to_list(length=limit)
    
    print(f"📋 Found {len(programs_data)} programs in database")
    if programs_data:
        print(f"📋 First program before conversion: {programs_data[0]}")
    
    # Convert to list of Pydantic models and then to dicts with proper ID handling
    programs = []
    for program_data in programs_data:
        # Convert ObjectId to string before creating Pydantic model
        if "_id" in program_data:
            program_data["_id"] = str(program_data["_id"])
        
        program = Program(**program_data)
        # Convert to dict and handle ID field
        program_dict = program.model_dump()
        if "_id" in program_dict:
            program_dict["id"] = program_dict.pop("_id")
        programs.append(program_dict)
    
    if programs:
        print(f"📋 First program after conversion: {programs[0]}")
    
    return programs

@router.get("/{code}")
async def get_program(
    code: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific program by ID.
    """
    try:
        program_data = await db.db.programs.find_one({"_id": ObjectId(code)})
        if not program_data:
            raise HTTPException(status_code=404, detail="Program not found")
        
        # Convert ObjectId to string before creating Pydantic model
        if "_id" in program_data:
            program_data["_id"] = str(program_data["_id"])
        
        # Convert to Pydantic model and then to dict with proper ID handling
        program = Program(**program_data)
        program_dict = program.model_dump()
        if "_id" in program_dict:
            program_dict["id"] = program_dict.pop("_id")
        return program_dict
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/", response_model=Program)
async def create_program(
    program_data: ProgramCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new academic program.
    Only admins can create programs.
    """
    # Debug logging
    print(f"📝 Creating program - User: {current_user.email}, Role: {current_user.role}")
    print(f"📝 Program data received: {program_data.model_dump()}")
    
    if current_user.role!="admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if program with same code already exists
    existing_program = await db.db.programs.find_one({"code": program_data.code})
    if existing_program:
        print(f"❌ Program code '{program_data.code}' already exists")
        raise HTTPException(status_code=400, detail="Program with this code already exists")
    
    try:
        program_dict = program_data.model_dump()
        print(f"📝 Inserting program dict: {program_dict}")
        result = await db.db.programs.insert_one(program_dict)
        
        # Retrieve the created program and convert ObjectId to string
        program_doc = await db.db.programs.find_one({"_id": result.inserted_id})
        if program_doc:
            # Convert ObjectId to string for the response
            program_doc["id"] = str(program_doc["_id"])
            del program_doc["_id"]  # Remove the original _id field
            
        print(f"✅ Program created successfully with ID: {result.inserted_id}")
        return program_doc
    except Exception as e:
        print(f"❌ Error creating program: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create program: {str(e)}")

@router.put("/{code}", response_model=Program)
async def update_program(
    code: str,
    program_data: ProgramUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a program.
    Only admins can update programs.
    """
    if current_user.role!="admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if program exists
    program = await db.db.programs.find_one({"_id": ObjectId(code)})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Update program
    update_data = {k: v for k, v in program_data.model_dump().items() if v is not None}
    if update_data:
        await db.db.programs.update_one({"_id": ObjectId(code)}, {"$set": update_data})

    updated_program = await db.db.programs.find_one({"_id": ObjectId(code)})
    
    # Convert ObjectId to string
    if updated_program and "_id" in updated_program:
        updated_program["id"] = str(updated_program["_id"])
        del updated_program["_id"]
    
    return updated_program

@router.delete("/{code}")
async def delete_program(
    code: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a program.
    Only admins can delete programs.
    """
    # Correct permission check: only allow if role is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if program exists
    program = await db.db.programs.find_one({"_id": ObjectId(code)})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Check if program has associated timetables
    timetables = await db.db.timetables.find_one({"program_id": ObjectId(code)})
    if timetables:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete program with associated timetables"
        )
    
    # Delete program
    await db.db.programs.delete_one({"_id": ObjectId(code)})
    return {"message": "Program deleted successfully"}

@router.get("/{code}/courses")
async def get_program_courses(
    code: str,
    semester: Optional[int] = Query(None, description="Filter by semester"),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all courses for a specific program from the database.
    """
    try:
        # Check if program exists
        program = await db.db.programs.find_one({"_id": ObjectId(code)})
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        
        # Build filter query for courses
        filter_query = {"program_id": ObjectId(code)}
        if semester is not None:
            filter_query["semester"] = semester
        
        print(f"🔍 Looking for courses with filter: {filter_query}")
        
        # Query courses from database
        courses = await db.db.courses.find(filter_query).to_list(length=None)
        
        print(f"📚 Found {len(courses)} courses in database")
        
        # Convert ObjectId to string for JSON serialization
        for course in courses:
            if "_id" in course:
                course["id"] = str(course["_id"])
                del course["_id"]
            if "code" in course and isinstance(course["code"], ObjectId):
                course["code"] = str(course["code"])
            if "created_by" in course and isinstance(course["created_by"], ObjectId):
                course["created_by"] = str(course["created_by"])
            # Convert any other ObjectId fields that might exist
            for key, value in course.items():
                if isinstance(value, ObjectId):
                    course[key] = str(value)
                elif isinstance(value, list):
                    # Handle lists that might contain ObjectIds (like prerequisites)
                    course[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
        
        return courses
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_program_courses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get program courses: {str(e)}")

@router.get("/{code}/statistics")
async def get_program_statistics(
    code: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get statistics for a specific program.
    """
    # Check if program exists
    program = await db.db.programs.find_one({"_id": ObjectId(code)})
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Get program statistics
    total_courses = await db.db.courses.count_documents({"code": ObjectId(code)})
    total_timetables = await db.db.timetables.count_documents({"code": ObjectId(code)})
    
    # Get semester-wise course count
    semester_pipeline = [
        {"$match": {"program_id": ObjectId(code)}},
        {"$group": {"_id": "$semester", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    semester_stats = await db.db.courses.aggregate(semester_pipeline).to_list(length=None)
    
    # Convert ObjectId to string for program_info
    if program and "_id" in program:
        program["id"] = str(program["_id"])
        del program["_id"]
    
    return {
        "code": code,
        "total_courses": total_courses,
        "total_timetables": total_timetables,
        "courses_by_semester": semester_stats,
        "program_info": program
    }
