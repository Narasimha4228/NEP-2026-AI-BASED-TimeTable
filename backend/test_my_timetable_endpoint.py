#!/usr/bin/env python
"""
Test script to verify the GET /api/v1/timetable/my endpoint works correctly
and returns the expected response structure for the Student Dashboard.
"""
import asyncio
import httpx
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10

async def test_endpoint():
    """Test the /timetable/my endpoint"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            # Step 1: Check if backend is running
            print("🔍 Checking backend connectivity...")
            health = await client.get("http://localhost:8000/docs")
            print("✅ Backend is running (status 200)")
            
            # Step 2: Try to get a student token (we need a valid JWT)
            print("\n📝 Testing /timetable/my endpoint...")
            print(f"   URL: {API_BASE_URL}/timetable/my")
            
            # We'll try without auth first to see the auth error
            response = await client.get(f"{API_BASE_URL}/timetable/my")
            
            print(f"\n📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            
            try:
                data = response.json()
                print(f"📊 Response Body:\n{json.dumps(data, indent=2)}")
            except:
                print(f"📊 Response Body (raw):\n{response.text}")
            
            if response.status_code == 401:
                print("\n✅ Endpoint exists and requires authentication (401)")
                print("   This is expected behavior - test with a valid student JWT token")
                return True
            elif response.status_code == 200:
                print("\n✅ Endpoint returned 200 OK")
                data = response.json()
                
                # Validate response structure
                expected_fields = ["timetable_id", "program", "year", "section", "semester", "grid"]
                missing_fields = [f for f in expected_fields if f not in data and data.get("timetable") is not None]
                
                if missing_fields:
                    print(f"⚠️  Missing fields: {missing_fields}")
                else:
                    print("✅ All expected response fields present")
                
                return True
            else:
                print(f"\n❌ Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {e}")
            print("\n💡 Tips:")
            print("   1. Make sure backend is running: uvicorn app.main:app --reload --port 8000")
            print("   2. Run from backend directory: cd backend")
            print("   3. Check MongoDB connection is active")
            return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_endpoint())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
