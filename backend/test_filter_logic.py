import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def test_filter():
    client = AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/')
    db = client['timetable_db']
    
    # Simulate the filter query
    department_code = 'ECE'
    year = 1
    semester = 'Odd'
    section = 'A'
    
    # Build query filter (same as backend)
    query = {"is_draft": False}
    
    # Find program by code
    program = await db.programs.find_one({"code": department_code})
    if program:
        query["program_id"] = program.get("_id")
        query["department_code"] = department_code
    
    # Find timetable
    timetable = await db.timetables.find_one(query, sort=[("generated_at", -1)])
    
    if timetable:
        print('✅ Timetable found!')
        print(f'  ID: {timetable.get("_id")}')
        print(f'  Department Code: {timetable.get("department_code")}')
        print(f'  Entries: {len(timetable.get("entries", []))}')
        print(f'  Entries sample:')
        for e in timetable.get('entries', [])[:3]:
            print(f'    - {e["course_name"]} ({e["day"]} {e["start_time"]})')
        
        # Check student groups
        metadata_filter = {
            'program_id': program.get('_id'),
            'year': year,
            'semester': semester,
            'section': section
        }
        
        groups = await db.student_groups.find(metadata_filter).to_list(None)
        print(f'\n✅ Student groups found: {len(groups)}')
        if groups:
            for g in groups[:2]:
                print(f'    - Year {g["year"]} {g["semester"]} Section {g["section"]}')
    else:
        print('❌ Timetable not found')

asyncio.run(test_filter())
