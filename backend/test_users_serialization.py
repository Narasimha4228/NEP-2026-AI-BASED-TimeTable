import asyncio
from motor import motor_asyncio

async def test_users_endpoint():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    print("Testing users endpoint logic...")
    
    # Get admin user
    admin_user = await db.users.find_one({'role': 'admin'})
    
    if admin_user:
        print(f"✅ Found admin user: {admin_user.get('email')}")
        print(f"   Role value: {admin_user.get('role')}")
        print(f"   Role type: {type(admin_user.get('role'))}")
        
        # Test the role comparison
        role = admin_user.get('role')
        if role == 'admin':
            print(f"✅ Role comparison works: {role} == 'admin'")
        else:
            print(f"❌ Role comparison failed: {role} != 'admin'")
    
    # Get all users to see format
    users = await db.users.find().to_list(100)
    print(f"\n✅ Total users in DB: {len(users)}")
    
    # Check the serialization
    def serialize_user(user: dict) -> dict:
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        return user
    
    serialized = [serialize_user(u) for u in users[:3]]
    
    print(f"\nSerialized sample:")
    for u in serialized:
        print(f"  - {u.get('email')}: role={u.get('role')}")

asyncio.run(test_users_endpoint())
