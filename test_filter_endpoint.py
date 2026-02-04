#!/usr/bin/env python3
"""Test the filter endpoint to debug entry handling"""

import sys
import json
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_filter_logic():
    """Test the filter endpoint logic directly"""
    
    # Connect to MongoDB
    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.timetable_db
    
    print("🔍 Testing filter endpoint logic...\n")
    
    # Find all student groups to understand the structure
    print("📋 Sample Student Groups:")
    groups = await db.student_groups.find().limit(3).to_list(None)
    for group in groups:
        print(f"  Group: {group.get('_id')} - Year: {group.get('year')}, Semester: {group.get('semester')}, Section: {group.get('section')}")
    
    if not groups:
        print("  ❌ No student groups found!")
        client.close()
        return
    
    # Test filter with first group
    test_group = groups[0]
    year = test_group.get("year")
    semester = test_group.get("semester")
    section = test_group.get("section")
    program_id = test_group.get("program_id")
    
    print(f"\n🎯 Testing filter with:")
    print(f"  Program ID: {program_id}")
    print(f"  Year: {year}")
    print(f"  Semester: {semester}")
    print(f"  Section: {section}")
    
    # Build the query like the endpoint does
    group_filter = {}
    if year is not None:
        group_filter["year"] = year
    if semester is not None:
        group_filter["semester"] = semester
    if section is not None:
        group_filter["section"] = section
    if program_id:
        group_filter["program_id"] = program_id
    
    print(f"\n🔎 Looking for student groups with filter: {group_filter}")
    matching_groups = await db.student_groups.find(group_filter).to_list(None)
    print(f"✅ Found {len(matching_groups)} matching student groups")
    
    # Get group IDs
    group_ids = [str(g.get("_id")) for g in matching_groups]
    print(f"📌 Group IDs: {group_ids}")
    
    # Build timetable query
    timetable_query = {
        "is_draft": False,
        "entries.group_id": {"$in": group_ids}
    }
    
    if program_id:
        try:
            timetable_query["program_id"] = ObjectId(program_id)
        except Exception:
            timetable_query["program_id"] = program_id
    
    print(f"\n🔎 Looking for timetables with query: {json.dumps(str(timetable_query), indent=2)}")
    
    # Find timetable
    timetable = await db.timetables.find_one(timetable_query, sort=[("generated_at", -1)])
    
    if not timetable:
        print("❌ No timetable found!")
    else:
        print(f"✅ Found timetable: {timetable.get('_id')}")
        entries = timetable.get("entries", [])
        print(f"📊 Total entries in timetable: {len(entries)}")
        
        if entries:
            print(f"\n📋 Sample entry (first 2):")
            for i, entry in enumerate(entries[:2]):
                print(f"\n  Entry {i+1}:")
                print(f"    group_id: {entry.get('group_id')}")
                print(f"    course_code: {entry.get('course_code')}")
                print(f"    course_name: {entry.get('course_name')}")
                print(f"    faculty: {entry.get('faculty')}")
                print(f"    day: {entry.get('day')}")
                print(f"    start_time: {entry.get('start_time')}")
                print(f"    end_time: {entry.get('end_time')}")
                print(f"    room: {entry.get('room')}")
        else:
            print("⚠️  No entries in timetable!")
    
    client.close()
    print("\n✅ Test complete")

if __name__ == "__main__":
    asyncio.run(test_filter_logic())
