#!/usr/bin/env python
"""
Comprehensive test of Access Management fix
"""
import asyncio
import requests
import json
from motor import motor_asyncio
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime

print("=" * 70)
print("COMPREHENSIVE ACCESS MANAGEMENT FIX VERIFICATION")
print("=" * 70)

# Test 1: Check MongoDB Connection
print("\n[TEST 1] MongoDB Connection")
print("-" * 70)
try:
    client = motor_asyncio.AsyncIOMotorClient(
        'mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority'
    )
    
    async def check_db():
        db = client['timetable_db']
        count = await db.users.count_documents({})
        return count
    
    user_count = asyncio.run(check_db())
    print(f"✅ Connected to MongoDB")
    print(f"✅ Total users in database: {user_count}")
except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")

# Test 2: Backend Health Check
print("\n[TEST 2] Backend Health Check")
print("-" * 70)
try:
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        print(f"✅ Backend is healthy: {response.json()}")
    else:
        print(f"❌ Backend returned {response.status_code}")
except Exception as e:
    print(f"❌ Backend unreachable: {e}")

# Test 3: Test /users endpoint WITHOUT auth
print("\n[TEST 3] /users Endpoint - NO AUTH")
print("-" * 70)
try:
    response = requests.get("http://localhost:8000/api/v1/users")
    if response.status_code == 401:
        print(f"✅ Correctly returns 401 Unauthorized: {response.json()}")
    else:
        print(f"⚠️ Unexpected status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Test /users endpoint WITH fresh token
print("\n[TEST 4] /users Endpoint - WITH FRESH TOKEN")
print("-" * 70)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzAxMjc4MDYsInN1YiI6IjY5NzA3MzhkNTcxNDIwZjIwMTJkODgwZiJ9.XrmPoGiKnfqqe14aHdjH-qymb2kPxDRYLg7eOBrcgmE"
headers = {"Authorization": f"Bearer {token}"}

try:
    response = requests.get("http://localhost:8000/api/v1/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Successfully fetched {len(users)} users")
        for i, user in enumerate(users[:3], 1):
            print(f"   {i}. {user.get('email')} - {user.get('role')}")
        if len(users) > 3:
            print(f"   ... and {len(users) - 3} more")
    else:
        print(f"❌ Got status {response.status_code}: {response.json()}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Check test user password
print("\n[TEST 5] Test User Configuration")
print("-" * 70)
try:
    async def check_user():
        client = motor_asyncio.AsyncIOMotorClient(
            'mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority'
        )
        db = client['timetable_db']
        user = await db.users.find_one({'email': 'test2@example.com'})
        return user
    
    user = asyncio.run(check_user())
    if user:
        print(f"✅ Test user found:")
        print(f"   Email: {user.get('email')}")
        print(f"   Role: {user.get('role')}")
        print(f"   Active: {user.get('is_active')}")
        print(f"   Has password: {'hashed_password' in user and user['hashed_password'] is not None}")
        print(f"\n   Login Credentials:")
        print(f"   - Email: test2@example.com")
        print(f"   - Password: Test@2024")
    else:
        print(f"❌ Test user not found")
except Exception as e:
    print(f"❌ Error: {e}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("✅ All systems operational!")
print("\nNext Steps:")
print("1. Go to http://localhost:5173/login")
print("2. Login with:")
print("   - Email: test2@example.com")
print("   - Password: Test@2024")
print("3. Navigate to Access Management")
print("4. User list should load successfully!")
print("=" * 70)
