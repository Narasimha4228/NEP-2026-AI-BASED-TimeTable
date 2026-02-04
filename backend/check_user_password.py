import asyncio
from motor import motor_asyncio

async def check():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Get first user
    first_user = await db.users.find_one({'email': 'test2@example.com'})
    
    print("=" * 60)
    print("USER test2@example.com")
    print("=" * 60)
    
    if first_user:
        print(f'Email: {first_user.get("email")}')
        print(f'Role: {first_user.get("role")}')
        print(f'Is Active: {first_user.get("is_active")}')
        print(f'Password Hash: {first_user.get("password_hash")[:50]}...')
    else:
        print('User not found')

asyncio.run(check())
