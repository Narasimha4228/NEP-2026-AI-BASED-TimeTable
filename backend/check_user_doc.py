import asyncio
from motor import motor_asyncio
from bson import ObjectId

async def check():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Get the user
    user = await db.users.find_one({'_id': ObjectId('6970738d571420f2012d880f')})
    
    print("=" * 60)
    print("USER DOCUMENT FROM DATABASE")
    print("=" * 60)
    
    if user:
        for key, value in user.items():
            if key == 'hashed_password':
                print(f'{key}: {str(value)[:50]}...')
            else:
                print(f'{key}: {value}')
    else:
        print('User not found')

asyncio.run(check())
