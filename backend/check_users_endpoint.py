import asyncio
from motor import motor_asyncio
import json

async def check():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    print("=" * 60)
    print("[1] CHECKING USERS IN DATABASE")
    print("=" * 60)
    
    users = await db.users.find().to_list(20)
    print(f'Total users: {len(users)}\n')
    
    for idx, u in enumerate(users[:5], 1):
        print(f"User {idx}:")
        print(f"  ID: {u.get('_id')}")
        print(f"  Email: {u.get('email')}")
        print(f"  Full Name: {u.get('full_name')}")
        print(f"  Role: {u.get('role')}")
        print()
    
    print("=" * 60)
    print("[2] CHECKING USERS ENDPOINT")
    print("=" * 60)
    
    # Try to call the users endpoint
    import httpx
    
    # First, get a token
    try:
        async with httpx.AsyncClient() as client_http:
            # Login as admin
            login_data = {
                'username': 'test2@example.com',
                'password': 'test123'
            }
            
            response = await client_http.post(
                'http://localhost:8000/api/v1/auth/login',
                data=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get('access_token')
                print(f"✅ Login successful, got token")
                
                # Now call users endpoint
                headers = {'Authorization': f'Bearer {token}'}
                users_response = await client_http.get(
                    'http://localhost:8000/api/v1/users',
                    headers=headers
                )
                
                print(f"Users endpoint status: {users_response.status_code}")
                print(f"Response: {users_response.json()}")
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(check())
