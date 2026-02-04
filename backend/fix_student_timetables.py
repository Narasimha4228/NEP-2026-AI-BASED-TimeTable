import asyncio
from motor import motor_asyncio
from bson import ObjectId
from datetime import datetime

async def fix_timetables():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Step 1: Get all unique group_ids from users
    students = await db.users.find({'role': 'student'}).to_list(1000)
    group_ids_set = set()
    for student in students:
        if student.get('group_id'):
            group_ids_set.add(student['group_id'])
    
    print(f'[1] Found {len(group_ids_set)} unique group_ids from students')
    
    # Step 2: Create groups collection if it doesn't exist
    existing_groups = await db.groups.find().to_list(1000)
    print(f'[2] Existing groups: {len(existing_groups)}')
    
    if len(existing_groups) == 0:
        print('[3] Creating groups from student assignments...')
        groups_to_insert = []
        for idx, gid in enumerate(group_ids_set, 1):
            groups_to_insert.append({
                '_id': gid,
                'name': f'Group {idx}',
                'is_active': True,
                'created_at': datetime.utcnow()
            })
        
        if groups_to_insert:
            result = await db.groups.insert_many(groups_to_insert)
            print(f'[4] Inserted {len(result.inserted_ids)} groups')
    
    # Step 3: Check timetables and add group_id to entries if missing
    print(f'\n[5] Checking timetables...')
    all_timetables = await db.timetables.find().to_list(100)
    print(f'    Total timetables: {len(all_timetables)}')
    
    timetables_needing_fix = 0
    for tt in all_timetables:
        entries = tt.get('entries', [])
        has_group_id = False
        for entry in entries:
            if 'group_id' in entry:
                has_group_id = True
                break
        
        if not has_group_id and entries:
            timetables_needing_fix += 1
            # Try to infer group_id from the program or use first group
            if group_ids_set:
                group_id = list(group_ids_set)[0]
                # Add group_id to all entries
                for entry in entries:
                    entry['group_id'] = group_id
                
                # Update in database
                await db.timetables.update_one(
                    {'_id': tt['_id']},
                    {'$set': {'entries': entries, 'is_draft': False}}
                )
    
    print(f'[6] Fixed {timetables_needing_fix} timetables by adding group_id to entries')
    
    # Step 4: Verify
    print(f'\n[7] Verification:')
    for student in students[:3]:
        gid = student.get('group_id')
        if gid:
            count = await db.timetables.count_documents({'entries.group_id': gid, 'is_draft': False})
            print(f'    Student {student.get("email", "unknown")}: {count} timetables')

asyncio.run(fix_timetables())
