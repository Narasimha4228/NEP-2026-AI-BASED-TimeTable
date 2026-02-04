import asyncio
from motor import motor_asyncio
from bson import ObjectId

async def fix():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Get the group_id from timetables
    tt = await db.timetables.find_one({'entries.group_id': {'$exists': True}})
    if not tt:
        print('No timetables found')
        return
    
    correct_group_id = tt['entries'][0].get('group_id')
    print(f'[1] Correct group_id from timetables: {correct_group_id} (type: {type(correct_group_id).__name__})')
    
    # Update all students to use this group_id
    # First try: assume all timetables are for all students (no group differentiation yet)
    # So assign everyone to the same group
    
    result = await db.users.update_many(
        {'role': 'student'},
        {'$set': {'group_id': correct_group_id}}
    )
    
    print(f'[2] Updated {result.modified_count} students with correct group_id')
    
    # Verify
    print(f'\n[3] Verification:')
    students = await db.users.find({'role': 'student'}).to_list(3)
    for s in students:
        print(f'    Student {s.get("email")}: group_id = {s.get("group_id")}')
    
    # Check timetable count now
    print(f'\n[4] Timetable count:')
    if correct_group_id:
        count = await db.timetables.count_documents({
            'entries.group_id': correct_group_id,
            'is_draft': False
        })
        print(f'    Generated timetables for this group: {count}')

asyncio.run(fix())
