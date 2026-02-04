#!/usr/bin/env python3
"""
Test script for the /api/v1/timetable/my endpoint
"""
import asyncio
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = "http://localhost:8000/api/v1"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

async def test_endpoint():
    """Test the /timetable/my endpoint"""
    print("\n" + "="*80)
    print("TEST: /api/v1/timetable/my endpoint")
    print("="*80)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.timetable_db
    
    try:
        # 1. Find a student with a group_id
        print("\n[1] Finding a student with group_id...")
        student = await db.users.find_one({"role": "student", "group_id": {"$exists": True, "$ne": None}})
        
        if not student:
            print("❌ No student with group_id found in database")
            print("   Hint: Create a student user and assign them to a student group")
            return
        
        student_id = str(student.get("_id"))
        group_id = student.get("group_id")
        print(f"✅ Found student: {student.get('email')} (ID: {student_id})")
        print(f"   Group ID: {group_id}")
        
        # 2. Check the student group
        print(f"\n[2] Checking student group {group_id}...")
        from bson import ObjectId
        try:
            group_doc = await db.student_groups.find_one({"_id": ObjectId(group_id)})
        except Exception:
            group_doc = await db.student_groups.find_one({"_id": group_id})
        
        if not group_doc:
            print(f"❌ Student group {group_id} not found")
            return
        
        print(f"✅ Student group: {group_doc.get('name')}")
        print(f"   Program: {group_doc.get('program_id')}")
        print(f"   Year: {group_doc.get('year')}")
        print(f"   Section: {group_doc.get('section')}")
        print(f"   Semester: {group_doc.get('semester')}")
        
        # 3. Check for timetables with this group
        print(f"\n[3] Checking for timetables with group_id {group_id}...")
        tt_count = await db.timetables.count_documents({"entries.group_id": group_id, "is_draft": False})
        print(f"   Found {tt_count} published timetable(s) with this group")
        
        if tt_count > 0:
            latest_tt = await db.timetables.find_one(
                {"entries.group_id": group_id, "is_draft": False},
                sort=[("generated_at", -1)]
            )
            if latest_tt:
                print(f"✅ Latest timetable ID: {latest_tt.get('_id')}")
                print(f"   Generated at: {latest_tt.get('generated_at')}")
                entry_count = len(latest_tt.get('entries', []))
                print(f"   Entries: {entry_count}")
        else:
            print("   No published timetables found for this group yet")
        
        # 4. Generate a test token
        print(f"\n[4] Generating a test JWT token for student...")
        # For testing, we'll look for an admin token in admin_token.txt or create a minimal one
        token_file = "admin_token.txt"
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                admin_token = f.read().strip()
                print(f"   (Using token from {token_file})")
        else:
            print(f"❌ No {token_file} found")
            print("   Hint: Run generate_admin_token.py first")
            return
        
        # For this test, we'll use the admin token (not ideal, but OK for testing)
        # A better approach would be to create a student token, but that requires
        # knowing how your auth system works
        
        # 5. Call the endpoint
        print(f"\n[5] Calling GET /api/v1/timetable/my (student endpoint)...")
        async with httpx.AsyncClient() as client_http:
            response = await client_http.get(
                f"{BACKEND_URL}/timetable/my",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint returned data:")
                print(f"   Message: {data.get('message')}")
                print(f"   Timetable ID: {data.get('timetable_id')}")
                print(f"   Program: {data.get('program')}")
                print(f"   Year: {data.get('year')}")
                print(f"   Section: {data.get('section')}")
                print(f"   Semester: {data.get('semester')}")
                
                grid = data.get('grid', {})
                if grid:
                    print(f"   Grid days: {list(grid.keys())}")
                    for day, slots in grid.items():
                        print(f"     {day}: {len(slots)} slot(s)")
                        for slot in slots[:2]:  # Show first 2
                            print(f"       - {slot.get('course_code')}: {slot.get('start_time')}-{slot.get('end_time')}")
                else:
                    print(f"   No grid data (expected if no timetable published)")
            
            elif response.status_code == 403:
                print(f"❌ Forbidden (403): {response.json()}")
                print("   Hint: Make sure you're testing with a student user, not admin")
            
            elif response.status_code == 404:
                print(f"⚠️  Not Found (404): Endpoint may not exist")
                print(f"   Response: {response.json()}")
            
            elif response.status_code == 400:
                print(f"❌ Bad Request (400): {response.json()}")
            
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
    
    finally:
        client.close()
        print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(test_endpoint())
