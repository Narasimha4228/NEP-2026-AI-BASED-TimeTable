"""
Test the API endpoint directly
"""
import asyncio
import aiohttp
import json

async def test_api():
    """Test the API endpoint"""
    
    timetable_id = "6984411e61c6ef3ed8284460"
    base_url = "http://localhost:8000/api/v1"
    
    print("\n" + "="*70)
    print("TESTING API ENDPOINT")
    print("="*70)
    
    try:
        async with aiohttp.ClientSession() as session:
            # First, get a token (use a default test user)
            print("\n1️⃣  Getting authentication token...")
            
            login_url = f"{base_url}/auth/login"
            login_data = {
                "email": "admin@example.com",
                "password": "admin123"
            }
            
            try:
                async with session.post(login_url, json=login_data) as resp:
                    if resp.status == 200:
                        auth_response = await resp.json()
                        token = auth_response.get("access_token")
                        print(f"✓ Token received: {token[:20]}...")
                    else:
                        print(f"⚠️  Login failed ({resp.status}), trying without token...")
                        token = None
            except Exception as e:
                print(f"⚠️  Login error: {e}, continuing without token...")
                token = None
            
            # Now test the timetable endpoint
            print(f"\n2️⃣  Fetching timetable {timetable_id}...")
            
            timetable_url = f"{base_url}/timetable/public/{timetable_id}"
            
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            print(f"URL: {timetable_url}")
            print(f"Headers: {headers}")
            
            async with session.get(timetable_url, headers=headers) as resp:
                print(f"\n✓ Response status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ API returned timetable!")
                    print(f"  Name: {data.get('name')}")
                    print(f"  Entries: {len(data.get('entries', []))}")
                    
                    # Show first entry
                    if data.get('entries'):
                        entry = data.get('entries')[0]
                        print(f"\n  First entry:")
                        print(f"    Course: {entry.get('course_name')}")
                        print(f"    Room: {entry.get('room_number')}")
                        print(f"    Day: {entry.get('day_of_week')}")
                        print(f"    Time: {entry.get('start_time')}")
                        
                    print(f"\n✅ API WORKING CORRECTLY!")
                    print(f"\n📋 Use this ID in frontend: {timetable_id}")
                    
                else:
                    error_text = await resp.text()
                    print(f"❌ Error response:")
                    print(error_text)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(test_api())
