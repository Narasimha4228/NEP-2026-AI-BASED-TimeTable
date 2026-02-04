#!/usr/bin/env python3
"""Test the filter endpoint via HTTP"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Get admin token from file
token_file = os.path.join(os.path.dirname(__file__), "backend", "admin_token_fresh.txt")
token = None

if os.path.exists(token_file):
    with open(token_file, 'r') as f:
        token = f.read().strip()
    print(f"✅ Loaded admin token from file (length: {len(token)})")
else:
    print("⚠️  Admin token file not found, trying without token")

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# Headers
headers = {
    "Content-Type": "application/json",
}

if token:
    headers["Authorization"] = f"Bearer {token}"

print("\n🔍 Testing filter endpoint...\n")

# Test 1: Get filter options
print("📋 Test 1: Getting filter options...")
try:
    response = requests.get(f"{BASE_URL}/timetable/options/filters", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Filter options retrieved:")
        print(f"  Programs: {len(data.get('programs', []))} available")
        print(f"  Years: {data.get('years', [])}")
        print(f"  Semesters: {data.get('semesters', [])}")
        print(f"  Sections: {data.get('sections', [])}")
        
        # Get first program for testing
        programs = data.get("programs", [])
        if programs:
            first_prog = programs[0]
            program_id = first_prog.get("id")
            print(f"\n  Sample program for testing: {first_prog.get('name')} (ID: {program_id})")
            
            # Test 2: Filter with first program
            print("\n📊 Test 2: Filtering timetables...")
            filter_params = {
                "program_id": program_id,
                "year": 1,
                "semester": "Odd",
                "section": "A"
            }
            print(f"Filter parameters: {filter_params}")
            
            response = requests.get(
                f"{BASE_URL}/timetable/filter",
                params=filter_params,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            
            if response.status_code == 200:
                print(f"✅ Filter response:")
                print(f"  Department: {data.get('department')}")
                print(f"  Year: {data.get('year')}")
                print(f"  Semester: {data.get('semester')}")
                print(f"  Section: {data.get('section')}")
                print(f"  Timetable ID: {data.get('timetable_id')}")
                
                entries = data.get("entries", [])
                print(f"  📥 Entries count: {len(entries)}")
                
                if entries:
                    print(f"\n  ✅ ENTRIES ARE BEING RETURNED!")
                    print(f"  Sample entry (first one):")
                    entry = entries[0]
                    print(f"    - Course Code: {entry.get('course_code')}")
                    print(f"    - Course Name: {entry.get('course_name')}")
                    print(f"    - Faculty: {entry.get('faculty')}")
                    print(f"    - Day: {entry.get('day')}")
                    print(f"    - Start Time: {entry.get('start_time')}")
                    print(f"    - End Time: {entry.get('end_time')}")
                    print(f"    - Room: {entry.get('room')}")
                    print(f"    - Group ID: {entry.get('group_id')}")
                else:
                    print(f"\n  ❌ NO ENTRIES RETURNED BY FILTER")
                    print(f"  Full response: {json.dumps(data, indent=2)}")
            else:
                print(f"❌ Filter failed: {data}")
    else:
        print(f"❌ Failed to get filter options: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
