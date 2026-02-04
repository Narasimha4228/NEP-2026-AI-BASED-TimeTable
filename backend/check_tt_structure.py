import asyncio
from motor import motor_asyncio
import json

async def check_timetable_structure():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    tt = await db.timetables.find_one({'entries.0': {'$exists': True}})
    if tt:
        print(f'Timetable ID: {tt["_id"]}')
        print(f'is_draft: {tt.get("is_draft")}')
        print(f'Number of entries: {len(tt.get("entries", []))}')
        if tt.get('entries'):
            entry = tt['entries'][0]
            print(f'\nFirst entry structure:')
            for key in sorted(entry.keys()):
                print(f'  {key}: {entry[key]}')

asyncio.run(check_timetable_structure())
