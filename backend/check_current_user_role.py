import asyncio
from motor import motor_asyncio

async def check():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Get first user (test2@example.com)
    first_user = await db.users.find_one({'email': 'test2@example.com'})
    
    print("=" * 60)
    print("CHECKING FIRST USER ROLE")
    print("=" * 60)
    
    if first_user:
        email = first_user.get('email')
        role = first_user.get('role')
        is_active = first_user.get('is_active')
        
        print(f'Email: {email}')
        print(f'Role: {role}')
        print(f'Is Active: {is_active}')
        print(f'Role == "admin": {role == "admin"}')
        print(f'Role == admin (without quotes): {role == admin if "admin" in str(role) else "N/A"}')
    else:
        print('User test2@example.com not found')
        
        # List all users
        users = await db.users.find().to_list(5)
        print(f'\nFirst 5 users:')
        for u in users:
            print(f"  - {u.get('email')}: {u.get('role')}")

asyncio.run(check())
