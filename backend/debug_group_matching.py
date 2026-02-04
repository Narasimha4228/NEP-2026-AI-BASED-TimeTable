import asyncio
from motor import motor_asyncio
from bson import ObjectId

async def check():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Get group_ids from timetable entries
    tt_sample = await db.timetables.find_one({'entries.group_id': {'$exists': True}})
    if tt_sample:
        tt_group_ids = set()
        for entry in tt_sample.get('entries', []):
            if 'group_id' in entry:
                tt_group_ids.add(str(entry['group_id']))
        print(f'Group IDs in timetable entries: {tt_group_ids}')
    
    # Get group_ids from students
    student = await db.users.find_one({'role': 'student'})
    if student:
        print(f'Student group_id: {student.get("group_id")} (type: {type(student.get("group_id")).__name__})')
        
        # Check if they match
        student_gid = student.get('group_id')
        if tt_sample:
            for entry in tt_sample.get('entries', [])[:2]:
                tt_gid = entry.get('group_id')
                print(f'\nTimetable entry group_id: {tt_gid} (type: {type(tt_gid).__name__})')
                print(f'Match: {str(student_gid) == str(tt_gid)}')
                
        # Try direct query
        print(f'\n[Trying direct query with string]')
        count = await db.timetables.count_documents({
            'entries.group_id': ObjectId(str(student_gid))
        })
        print(f'Timetables with student group_id (as ObjectId): {count}')
        
        print(f'\n[Trying direct query with string comparison]')
        # This won't work well, but let's see
        all_tts = await db.timetables.find().to_list(100)
        count2 = 0
        for tt in all_tts:
            for entry in tt.get('entries', []):
                if str(entry.get('group_id')) == str(student_gid):
                    count2 += 1
                    break
        print(f'Timetables with matching group_id (string compare): {count2}')

asyncio.run(check())
