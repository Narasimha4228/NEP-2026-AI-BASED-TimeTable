import asyncio
from motor import motor_asyncio

async def fix():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    correct_group_id = '6971b4b3d91cfa375761779f'
    
    # Get all timetables
    all_tts = await db.timetables.find().to_list(100)
    print(f'[1] Total timetables: {len(all_tts)}')
    
    # Group by their current group_ids
    group_id_counts = {}
    for tt in all_tts:
        tt_group_id = None
        for entry in tt.get('entries', []):
            tt_group_id = entry.get('group_id')
            if tt_group_id:
                break
        
        if tt_group_id:
            key = str(tt_group_id)
            group_id_counts[key] = group_id_counts.get(key, 0) + 1
    
    print(f'\n[2] Timetables by group_id:')
    for gid, count in group_id_counts.items():
        print(f'    {gid}: {count} timetables')
    
    # Update ALL timetables to have the correct group_id in all entries
    print(f'\n[3] Updating all timetable entries to use correct group_id...')
    
    updated = 0
    for tt in all_tts:
        entries = tt.get('entries', [])
        if not entries:
            # Skip empty timetables
            continue
            
        has_changes = False
        for entry in entries:
            if entry.get('group_id') != correct_group_id:
                entry['group_id'] = correct_group_id
                has_changes = True
        
        if has_changes or tt.get('is_draft'):
            await db.timetables.update_one(
                {'_id': tt['_id']},
                {'$set': {
                    'entries': entries,
                    'is_draft': False
                }}
            )
            updated += 1
    
    print(f'    Updated {updated} timetables')
    
    # Verify
    final_count = await db.timetables.count_documents({
        'entries.group_id': correct_group_id,
        'is_draft': False
    })
    print(f'\n[4] Timetables now available for students: {final_count}')

asyncio.run(fix())
