import asyncio
from motor import motor_asyncio

async def fix():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    # Count timetables by status
    draft = await db.timetables.count_documents({'is_draft': True})
    generated = await db.timetables.count_documents({'is_draft': False})
    print(f'[1] Current timetable status:')
    print(f'    Draft: {draft}')
    print(f'    Generated: {generated}')
    
    # Update all timetables with the correct group_id to be generated (not draft)
    correct_group_id = '6971b4b3d91cfa375761779f'
    
    result = await db.timetables.update_many(
        {'entries.group_id': correct_group_id},
        {'$set': {'is_draft': False}}
    )
    
    print(f'\n[2] Updated {result.modified_count} timetables to is_draft: False')
    
    # Verify
    generated_now = await db.timetables.count_documents({
        'entries.group_id': correct_group_id,
        'is_draft': False
    })
    print(f'\n[3] Timetables now available for students: {generated_now}')

asyncio.run(fix())
