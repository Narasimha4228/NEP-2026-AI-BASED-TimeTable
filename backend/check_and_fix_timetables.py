import asyncio
from motor import motor_asyncio
from bson import ObjectId

async def check_and_fix():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    print("=" * 60)
    print("[1] CHECKING USERS")
    print("=" * 60)
    users = await db.users.find().to_list(10)
    print(f'Total users: {len(users)}\n')
    for u in users:
        print(f"Email: {u.get('email')}")
        print(f"  Role: {u.get('role')}")
        print(f"  Group ID: {u.get('group_id')}")
        print(f"  ID: {u.get('_id')}\n")
    
    # Get first user (the logged-in one)
    if users:
        current_user = users[0]
        user_group_id = current_user.get('group_id')
        print(f"Current user group_id: {user_group_id}")
    
    print("\n" + "=" * 60)
    print("[2] CHECKING TIMETABLES")
    print("=" * 60)
    
    # Check total timetables
    tt_count = await db.timetables.count_documents({})
    print(f'Total timetables in DB: {tt_count}\n')
    
    # Check timetables with entries
    timetables = await db.timetables.find({'entries': {'$exists': True}}).to_list(5)
    print(f'Timetables with entries: {len(timetables)}')
    
    if timetables:
        for idx, tt in enumerate(timetables[:2]):
            print(f"\n  Timetable {idx+1}:")
            entries = tt.get('entries', [])
            print(f"    Entry count: {len(entries)}")
            if entries:
                print(f"    First entry group_id: {entries[0].get('group_id')}")
                print(f"    First entry faculty_id: {entries[0].get('faculty_id')}")
    
    print("\n" + "=" * 60)
    print("[3] FIXING ISSUE")
    print("=" * 60)
    
    # If current user has no group_id, assign them to a group from a timetable
    if not user_group_id and timetables:
        first_entry_group = timetables[0]['entries'][0].get('group_id')
        print(f"User has no group_id. Assigning: {first_entry_group}")
        
        await db.users.update_one(
            {'_id': current_user['_id']},
            {'$set': {'group_id': first_entry_group}}
        )
        print("✅ User updated with group_id")
    
    # Check if timetables have the right group_id
    if timetables and user_group_id:
        matching_tts = await db.timetables.count_documents({'entries.group_id': user_group_id})
        print(f"\nTimetables with user's group_id ({user_group_id}): {matching_tts}")
    
    print("\n" + "=" * 60)
    print("✅ Check complete!")
    print("=" * 60)

asyncio.run(check_and_fix())
