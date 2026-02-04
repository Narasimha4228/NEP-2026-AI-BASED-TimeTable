from app.models.user import User
from app.db.mongodb import db
import asyncio
from motor import motor_asyncio
from bson import ObjectId

async def test():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db_client = client['timetable_db']
    
    # Get the user
    user = await db_client.users.find_one({'_id': ObjectId('6970738d571420f2012d880f')})
    
    print("=" * 60)
    print("USER CREATION TEST")
    print("=" * 60)
    
    if user:
        print("Document from DB:")
        print(f"  Fields: {list(user.keys())}")
        
        # Try to create User model
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        
        # Convert ObjectId fields to strings
        if "faculty_id" in user and user["faculty_id"]:
            user["faculty_id"] = str(user["faculty_id"]) if not isinstance(user["faculty_id"], str) else user["faculty_id"]
        if "group_id" in user and user["group_id"]:
            user["group_id"] = str(user["group_id"]) if not isinstance(user["group_id"], str) else user["group_id"]
        
        user_data = {k: v for k, v in user.items() if k != "hashed_password"}
        
        print(f"\nData for User creation: {list(user_data.keys())}")
        print(f"group_id value: {user_data.get('group_id')} (type: {type(user_data.get('group_id'))})")
        
        try:
            user_obj = User(**user_data)
            print(f"✅ User created successfully!")
            print(f"  Email: {user_obj.email}")
            print(f"  Role: {user_obj.role}")
        except Exception as e:
            print(f"❌ Error creating User: {e}")

asyncio.run(test())
