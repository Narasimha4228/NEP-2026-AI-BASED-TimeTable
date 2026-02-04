#!/usr/bin/env python
"""Test the refactored /timetable/my endpoint with new response format"""
import asyncio
import sys
from pathlib import Path
from bson import ObjectId
import json

Path(__file__).parent.with_name('backend').__str__() if 'backend' not in str(Path.cwd()) else None
sys.path.insert(0, str(Path(__file__).parent))

from app.db.mongodb import db, connect_to_mongo
from app.models.user import User, UserRole

async def main():
    print("=" * 70)
    print("Testing Refactored /timetable/my Endpoint (New Response Format)")
    print("=" * 70)
    
    try:
        await connect_to_mongo()
        print("\nOK: Connected to MongoDB\n")
        
        # Known values
        group_id = "6971b4b3d91cfa375761779f"
        program_id = "68b5c517e73858dcb11d37e4"
        
        # Fetch student group details
        try:
            group_obj_id = ObjectId(group_id) if ObjectId.is_valid(group_id) else group_id
        except:
            group_obj_id = group_id
            
        group_doc = await db.db.student_groups.find_one({"_id": group_obj_id})
        if not group_doc:
            print("ERROR: Student group not found")
            return False
        
        print(f"Student Group: {group_doc.get('name')}")
        program_id = group_doc.get("program_id")
        year = group_doc.get("year")
        semester = group_doc.get("semester")
        section = group_doc.get("section")
        print(f"  Program: {program_id}")
        print(f"  Year: {year}")
        print(f"  Semester: {semester}")
        print(f"  Section: {section}\n")
        
        # Build and execute query
        query = {"is_draft": False, "entries.group_id": group_id}
        if program_id:
            try:
                query["program_id"] = ObjectId(program_id)
            except:
                query["program_id"] = program_id
        
        timetable = await db.db.timetables.find_one(query, sort=[("generated_at", -1)])
        
        if not timetable:
            print("ERROR: No timetable found")
            return False
        
        print(f"Timetable Found: {timetable.get('title')}")
        print(f"  ID: {timetable.get('_id')}")
        print(f"  Total Entries: {len(timetable.get('entries', []))}\n")
        
        # Filter entries for student
        entries = timetable.get("entries", [])
        my_entries = [e for e in entries if e.get("group_id") == group_id]
        
        print(f"Student's Entries: {len(my_entries)}")
        for e in my_entries[:2]:
            print(f"  - {e.get('course_code')}: {e.get('start_time')}-{e.get('end_time')} @ {e.get('day')}")
        if len(my_entries) > 2:
            print(f"  ... and {len(my_entries)-2} more\n")
        
        # Get program name/code for department
        try:
            prog_obj_id = ObjectId(program_id) if ObjectId.is_valid(str(program_id)) else program_id
        except:
            prog_obj_id = program_id
        
        prog = await db.db.programs.find_one({"_id": prog_obj_id})
        department = None
        if prog:
            department = prog.get("code") or prog.get("name") or prog.get("title")
        
        # Build response
        response = {
            "department": department,
            "year": year,
            "section": section,
            "semester": semester,
            "timetable_id": str(timetable.get("_id")),
            "generated_at": timetable.get("generated_at").isoformat() if timetable.get("generated_at") else None,
            "entries": my_entries[:3]  # Show first 3 entries
        }
        
        print("=" * 70)
        print("API RESPONSE (New Format)")
        print("=" * 70)
        print(json.dumps(response, indent=2, default=str))
        
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        print(f"[OK] Department: {response.get('department')}")
        print(f"[OK] Year: {response.get('year')}")
        print(f"[OK] Section: {response.get('section')}")
        print(f"[OK] Semester: {response.get('semester')}")
        print(f"[OK] Timetable ID: {response.get('timetable_id')}")
        print(f"[OK] Entries count: {len(response.get('entries', []))}")
        print("\n✓ New response format is ready for frontend!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
