import asyncio
from motor import motor_asyncio
from app.services.auth import create_access_token
from datetime import timedelta

async def gen_token():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Get admin user
    admin = await db.users.find_one({'email': 'test2@example.com'})
    
    if not admin:
        print("Admin user not found!")
        return
    
    print("=" * 60)
    print("GENERATING NEW ADMIN TOKEN")
    print("=" * 60)
    print(f"User ID: {admin['_id']}")
    print(f"Email: {admin['email']}")
    print(f"Role: {admin.get('role')}")
    
    # Generate token valid for 24 hours
    token = create_access_token(
        subject=str(admin['_id']),
        expires_delta=timedelta(hours=24)
    )
    
    print(f"\n✅ NEW TOKEN (valid for 24 hours):")
    print(token)
    
    # Save to file
    with open('admin_token_fresh.txt', 'w') as f:
        f.write(token)
    print(f"\n💾 Token saved to admin_token_fresh.txt")

asyncio.run(gen_token())
