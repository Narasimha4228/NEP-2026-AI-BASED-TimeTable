#!/usr/bin/env python3
"""Debug what data exists in the database via API"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Get admin token
token_file = os.path.join(os.path.dirname(__file__), "backend", "admin_token_fresh.txt")
token = None

if os.path.exists(token_file):
    with open(token_file, 'r') as f:
        token = f.read().strip()

BASE_URL = "http://localhost:8000/api/v1"

headers = {
    "Content-Type": "application/json",
}

if token:
    headers["Authorization"] = f"Bearer {token}"

print("🔍 Debugging database content via API...\n")

# Try to get a student's timetable
print("📋 Test 1: Getting current user (to understand structure)...")
try:
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"✅ Current user: {user.get('username')}")
        print(f"  Role: {user.get('role')}")
        print(f"  Student Group: {user.get('student_group_id')}")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Try to get student's timetable
print("\n📊 Test 2: Getting student's auto-assigned timetable...")
try:
    response = requests.get(f"{BASE_URL}/timetable/my", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        tt_data = response.json()
        print(f"✅ Student timetable found!")
        print(f"  Program ID: {tt_data.get('program_id')}")
        print(f"  Year: {tt_data.get('year')}")
        print(f"  Semester: {tt_data.get('semester')}")
        print(f"  Section: {tt_data.get('section')}")
        
        entries = tt_data.get("entries", [])
        print(f"  📥 Entries: {len(entries)}")
        
        if entries:
            print(f"\n  Sample entry:")
            entry = entries[0]
            print(f"    - Course: {entry.get('course_name')} ({entry.get('course_code')})")
            print(f"    - Day: {entry.get('day')}")
            print(f"    - Time: {entry.get('start_time')} - {entry.get('end_time')}")
            print(f"    - Group ID: {entry.get('group_id')}")
    elif response.status_code == 404:
        print(f"⚠️  Student has no assigned timetable")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Try different filter combinations
print("\n🔎 Test 3: Trying different filter combinations...")

test_filters = [
    {"program_id": "68b5c517e73858dcb11d37e4"},  # Just program
    {"year": 1},  # Just year
    {"section": "A"},  # Just section
    {"semester": "Odd"},  # Just semester
    {"program_id": "68b5c517e73858dcb11d37e4", "year": 1},  # Program + year
    {"program_id": "68b5c517e73858dcb11d37e4", "year": 2},  # Different year
    {"program_id": "68b5c517e73858dcb11d37e4", "year": 1, "semester": "Odd", "section": "A"},  # All
    {"program_id": "68b5c517e73858dcb11d37e4", "year": 1, "semester": "3", "section": "A"},  # Different semester
]

for i, filters in enumerate(test_filters, 1):
    try:
        response = requests.get(
            f"{BASE_URL}/timetable/filter",
            params=filters,
            headers=headers
        )
        
        result = response.json()
        entries_count = len(result.get("entries", []))
        timetable_id = result.get("timetable_id")
        
        filter_str = ", ".join([f"{k}={v}" for k, v in filters.items()])
        status = "✅" if entries_count > 0 else "❌"
        print(f"{i}. {status} {filter_str}")
        print(f"   → Found {entries_count} entries, TT: {timetable_id[:8] if timetable_id else 'None'}...")
    except Exception as e:
        print(f"{i}. ❌ Error: {e}")
