import asyncio
from motor import motor_asyncio
from bson import ObjectId

async def check():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Get total timetables
    total_tt = await db.timetables.count_documents({})
    print(f'[1] Total timetables in DB: {total_tt}')
    
    # Get all groups
    groups = await db.groups.find().to_list(100)
    print(f'[2] Total groups: {len(groups)}')
    for i, g in enumerate(groups[:3]):
        print(f'    Group {i+1}: {g["_id"]} - {g.get("name", "Unknown")}')
    
    # Check which groups have timetables
    print(f'\n[3] Timetables by group:')
    for group in groups[:5]:
        gid = group['_id']
        count = await db.timetables.count_documents({'entries.group_id': gid, 'is_draft': False})
        print(f'    Group {group.get("name", "Unknown")}: {count} timetables')
    
    # Check a student
    student = await db.users.find_one({'role': 'student'})
    if student:
        print(f'\n[4] Sample student: {student.get("email", student.get("_id"))}')
        print(f'    group_id in DB: {student.get("group_id")}')
        
        if student.get('group_id'):
            gid = student['group_id']
            count = await db.timetables.count_documents({'entries.group_id': gid, 'is_draft': False})
            print(f'    Timetables for this group: {count}')
            
            tt = await db.timetables.find_one({'entries.group_id': gid, 'is_draft': False}, sort=[('generated_at', -1)])
            if tt:
                entries_for_group = [e for e in tt.get('entries', []) if str(e.get('group_id')) == str(gid)]
                print(f'    Entries in latest timetable for this group: {len(entries_for_group)}')
    
    # Check is_draft flag
    print(f'\n[5] Timetable status:')
    draft_count = await db.timetables.count_documents({'is_draft': True})
    generated_count = await db.timetables.count_documents({'is_draft': False})
    print(f'    Draft timetables: {draft_count}')
    print(f'    Generated timetables: {generated_count}')

asyncio.run(check())
