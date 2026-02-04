import asyncio
from motor import motor_asyncio
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_password():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Set password for test2@example.com
    new_password = "Test@2024"
    hashed = pwd_context.hash(new_password)
    
    result = await db.users.update_one(
        {'email': 'test2@example.com'},
        {'$set': {'hashed_password': hashed}}
    )
    
    print("=" * 60)
    print("PASSWORD RESET")
    print("=" * 60)
    print(f"Email: test2@example.com")
    print(f"New Password: {new_password}")
    print(f"Updated: {result.modified_count} document(s)")
    print(f"\n✅ You can now log in with these credentials!")

asyncio.run(reset_password())
