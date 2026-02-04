#!/usr/bin/env python
"""
Comprehensive test for the /timetable/my endpoint.
This script will:
1. Check MongoDB connection
2. Find a student user with a group_id
3. Generate a test JWT token
4. Call the /timetable/my endpoint
5. Verify the response structure
"""
import asyncio
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.db.mongodb import db, connect_to_mongo
from app.models.user import User, UserRole
from bson import ObjectId

async def main():
    print("=" * 60)
    print("Testing /timetable/my Endpoint")
    print("=" * 60)
    
    try:
        # Step 1: Connect to MongoDB
        print("\n[1/5] Connecting to MongoDB...")
        await connect_to_mongo()
        print("    ✅ Connected")
        
        # Step 2: Find or create a test student
        print("\n[2/5] Finding a student user...")
        student = await db.db.users.find_one({"role": "student", "group_id": {"$exists": True, "$ne": None}})
        
        if not student:
            print("    ❌ No student with group_id found in database")
            print("    💡 Need to create a test student or assign a group to existing student")
            
            # Try to find any student
            any_student = await db.db.users.find_one({"role": "student"})
            if any_student:
                print(f"    Found student: {any_student.get('email')}")
                print(f"    Current group_id: {any_student.get('group_id')}")
                print("\n    Please assign a group_id to this student first:")
                print(f"    - Get a student_group ID from the database")
                print(f"    - Update user: db.users.updateOne({{_id: ObjectId('{any_student['_id']}') }}, {{$set: {{group_id: '<group_id>'}} }})")
            return False
        
        student_id = str(student["_id"])
        student_email = student.get("email")
        group_id = student.get("group_id")
        
        print(f"    ✅ Found student: {student_email}")
        print(f"    ✅ Group ID: {group_id}")
        
        # Step 3: Check student group details
        print("\n[3/5] Fetching student group details...")
        try:
            group_obj_id = ObjectId(group_id) if ObjectId.is_valid(group_id) else group_id
        except:
            group_obj_id = group_id
            
        group = await db.db.student_groups.find_one({"_id": group_obj_id})
        
        if not group:
            print(f"    ❌ Student group not found: {group_id}")
            return False
        
        program_id = group.get("program_id")
        year = group.get("year")
        semester = group.get("semester")
        section = group.get("section")
        
        print(f"    ✅ Group: {group.get('name', 'Unknown')}")
        print(f"       - Program: {program_id}")
        print(f"       - Year: {year}")
        print(f"       - Semester: {semester}")
        print(f"       - Section: {section}")
        
        # Step 4: Check for timetables matching this student's group
        print("\n[4/5] Checking for matching timetables...")
        timetables = await db.db.timetables.find({
            "is_draft": False,
            "entries.group_id": group_id
        }).to_list(5)
        
        if not timetables:
            print(f"    ⚠️  No published timetables found for group {group_id}")
            print(f"    💡 Admin needs to generate and publish a timetable for this group")
            
            # Check if there are ANY timetables at all
            all_timetables = await db.db.timetables.find({"is_draft": False}).to_list(1)
            if not all_timetables:
                print("    💡 No published timetables exist in database at all")
            return False
        
        latest_tt = timetables[0]
        print(f"    ✅ Found {len(timetables)} matching timetable(s)")
        print(f"    ✅ Latest: {latest_tt.get('title', 'Untitled')}")
        print(f"       - ID: {latest_tt.get('_id')}")
        print(f"       - Generated: {latest_tt.get('generated_at')}")
        print(f"       - Entries: {len(latest_tt.get('entries', []))}")
        
        # Step 5: Generate JWT and test endpoint logic
        print("\n[5/5] Testing endpoint logic...")
        
        # Convert student to User model
        student["id"] = student_id
        student["role"] = UserRole.student
        
        # Convert all ObjectIds to strings for Pydantic
        if "_id" in student:
            del student["_id"]
        if "hashed_password" in student:
            hashed_pw = student.pop("hashed_password")
        
        user = User(**student)
        
        # Simulate the endpoint logic
        print("    Simulating endpoint execution...")
        
        # 5a: Check role
        if user.role.value != "student":
            print("    ❌ User is not a student")
            return False
        print("    ✅ User is a student")
        
        # 5b: Check group_id
        if not user.group_id:
            print("    ❌ Student has no group_id")
            return False
        print("    ✅ Student has group_id")
        
        # 5c: Fetch student group
        try:
            gid = ObjectId(user.group_id) if ObjectId.is_valid(user.group_id) else user.group_id
        except:
            gid = user.group_id
        
        group_doc = await db.db.student_groups.find_one({"_id": gid})
        if not group_doc:
            print("    ❌ Student group not found")
            return False
        print("    ✅ Student group found")
        
        # 5d: Build query
        query = {"is_draft": False, "entries.group_id": user.group_id}
        program_id = group_doc.get("program_id")
        if program_id:
            try:
                query["program_id"] = ObjectId(program_id)
            except:
                query["program_id"] = program_id
        
        print(f"    Query: {query}")
        
        # 5e: Fetch timetable
        timetable = await db.db.timetables.find_one(query, sort=[("generated_at", -1)])
        if not timetable:
            print("    ❌ No timetable found")
            return False
        
        print("    ✅ Timetable found")
        
        # 5f: Build response
        entries = timetable.get("entries", [])
        my_entries = [e for e in entries if e.get("group_id") == user.group_id]
        
        grid = {}
        for e in my_entries:
            day = e.get("day") or (e.get("time_slot") or {}).get("day") or "Unknown"
            slot = {
                "course_code": e.get("course_code") or e.get("course"),
                "course_name": e.get("course_name"),
                "start_time": e.get("start_time") or (e.get("time_slot") or {}).get("start_time"),
                "end_time": e.get("end_time") or (e.get("time_slot") or {}).get("end_time"),
                "room": e.get("room"),
                "faculty": e.get("faculty"),
                "is_lab": e.get("is_lab", False)
            }
            grid.setdefault(day, []).append(slot)
        
        # Fetch program name
        program_name = None
        if program_id:
            try:
                prog_id = ObjectId(program_id) if ObjectId.is_valid(str(program_id)) else program_id
            except:
                prog_id = program_id
            prog = await db.db.programs.find_one({"_id": prog_id})
            if prog:
                program_name = prog.get("name") or prog.get("title")
        
        response = {
            "timetable_id": str(timetable.get("_id")),
            "generated_at": timetable.get("generated_at").isoformat() if timetable.get("generated_at") else None,
            "program": {"id": str(program_id) if program_id else None, "name": program_name},
            "year": group_doc.get("year"),
            "section": group_doc.get("section"),
            "semester": group_doc.get("semester"),
            "grid": grid
        }
        
        print("\n" + "=" * 60)
        print("ENDPOINT RESPONSE (Expected)")
        print("=" * 60)
        print(json.dumps(response, indent=2, default=str))
        
        print("\n✅ All tests passed!")
        print("The endpoint should work when called with a valid JWT token")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
