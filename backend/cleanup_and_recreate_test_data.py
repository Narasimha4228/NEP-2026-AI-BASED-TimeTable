#!/usr/bin/env python
"""
Clean up and recreate test timetable data with correct schema
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from bson import ObjectId

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.db.mongodb import db, connect_to_mongo

async def main():
    print("=" * 60)
    print("Cleaning up and recreating test data")
    print("=" * 60)
    
    try:
        await connect_to_mongo()
        print("OK: Connected to MongoDB\n")
        
        # Delete old test timetable
        result = await db.db.timetables.delete_many({
            "title": "Test Timetable - CSE Year 1"
        })
        print(f"Deleted {result.deleted_count} old test timetable(s)")
        
        # Known values from test
        group_id = "6971b4b3d91cfa375761779f"
        program_id = "68b5c517e73858dcb11d37e4"
        admin_id = "68b5c493b2adfdb5c89a37c7"
        
        # Create new test timetable with correct schema
        sample_timetable = {
            "title": "Test Timetable - CSE Year 1",
            "program_id": ObjectId(program_id),
            "semester": 1,  # Integer as per model
            "academic_year": "2025-2026",
            "group_ids": [group_id],
            "is_draft": False,
            "created_by": ObjectId(admin_id),
            "created_at": datetime.utcnow(),
            "generated_at": datetime.utcnow(),
            "status": "published",
            "entries": [
                {
                    "group_id": group_id,
                    "course_code": "CS101",
                    "course_name": "Programming Fundamentals",
                    "faculty": "Dr. Smith",
                    "day": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "room": "Room 101",
                    "is_lab": False
                },
                {
                    "group_id": group_id,
                    "course_code": "CS102",
                    "course_name": "Data Structures",
                    "faculty": "Prof. Johnson",
                    "day": "Monday",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "room": "Room 102",
                    "is_lab": False
                },
                {
                    "group_id": group_id,
                    "course_code": "CS103",
                    "course_name": "Programming Lab",
                    "faculty": "Dr. Williams",
                    "day": "Tuesday",
                    "start_time": "11:00",
                    "end_time": "13:00",
                    "room": "Lab 1",
                    "is_lab": True
                },
                {
                    "group_id": group_id,
                    "course_code": "CS104",
                    "course_name": "Database Systems",
                    "faculty": "Prof. Brown",
                    "day": "Wednesday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "room": "Room 103",
                    "is_lab": False
                },
                {
                    "group_id": group_id,
                    "course_code": "CS105",
                    "course_name": "Web Development",
                    "faculty": "Dr. Davis",
                    "day": "Thursday",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "room": "Room 104",
                    "is_lab": False
                },
                {
                    "group_id": group_id,
                    "course_code": "CS106",
                    "course_name": "Data Structures Lab",
                    "faculty": "Prof. Miller",
                    "day": "Friday",
                    "start_time": "09:00",
                    "end_time": "11:00",
                    "room": "Lab 2",
                    "is_lab": True
                }
            ]
        }
        
        # Insert the test timetable
        print(f"Creating test timetable for group: {group_id}")
        result = await db.db.timetables.insert_one(sample_timetable)
        timetable_id = result.inserted_id
        
        print(f"OK: Test timetable created!")
        print(f"    ID: {timetable_id}")
        print(f"    Title: {sample_timetable['title']}")
        print(f"    Semester: {sample_timetable['semester']} (int)")
        print(f"    Entries: {len(sample_timetable['entries'])}")
        
        # Verify it was inserted
        verify = await db.db.timetables.find_one({"_id": timetable_id})
        if verify:
            print(f"\nOK: Timetable exists in database")
            print(f"    Created by: {verify.get('created_by')}")
            print(f"    Is draft: {verify.get('is_draft')}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
