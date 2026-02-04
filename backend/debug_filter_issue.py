import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def check():
    client = AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/')
    db = client['timetable_db']
    
    # Get the ECE Semester 3 timetable
    tt = await db.timetables.find_one({'_id': ObjectId('69785f725ed0b92c970dbe87')})
    if tt:
        print('Timetable found:')
        print(f'  Semester: {tt.get("semester")}')
        print(f'  Year field: {tt.get("year")}')
        print(f'  Program ID: {tt.get("program_id")}')
        print(f'  Department Code: {tt.get("department_code")}')
        print(f'  Is Draft: {tt.get("is_draft")}')
        print(f'  Entries count: {len(tt.get("entries", []))}')
        if tt.get('entries'):
            print(f'  First entry: {tt["entries"][0]}')
    
    # Check student groups for ECE
    prog = await db.programs.find_one({'code': 'ECE'})
    if prog:
        print(f'\nECE Program ID: {prog["_id"]}')
        groups = await db.student_groups.find({'program_id': prog['_id']}).to_list(None)
        print(f'Found {len(groups)} student groups for ECE')
        if groups:
            for g in groups[:5]:
                print(f'  - Year: {g.get("year")}, Semester: {g.get("semester")}, Section: {g.get("section")}')

asyncio.run(check())
