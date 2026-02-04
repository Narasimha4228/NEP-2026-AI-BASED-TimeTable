#!/usr/bin/env python3
"""Simple filter endpoint test"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

token_file = os.path.join(os.path.dirname(__file__), "backend", "admin_token_fresh.txt")
token = open(token_file).read().strip() if os.path.exists(token_file) else None

BASE_URL = "http://localhost:8000/api/v1"
headers = {"Authorization": f"Bearer {token}"} if token else {}

# Test filter with all parameters
print("Testing filter with program + year + semester + section...")
params = {
    "program_id": "68b5c517e73858dcb11d37e4",
    "year": 1,
    "semester": "Odd",
    "section": "A"
}

response = requests.get(f"{BASE_URL}/timetable/filter", params=params, headers=headers)
data = response.json()

if response.status_code == 200:
    entries = data.get("entries", [])
    print(f"✅ Status: {response.status_code}")
    print(f"  Entries: {len(entries)}")
    if entries:
        print(f"  ✅ SUCCESS! Entries are being returned!")
    else:
        print(f"  ❌ FAIL! No entries returned")
        print(f"  Response: {data}")
else:
    print(f"❌ Status: {response.status_code}")
    print(f"  Response: {data}")
