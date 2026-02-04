import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def create_groups():
    client = AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/')
    db = client['timetable_db']
    
    # Get ECE program
    prog = await db.programs.find_one({'code': 'ECE'})
    if not prog:
        print('ECE program not found')
        return
    
    prog_id = prog['_id']
    print(f'ECE Program ID: {prog_id}')
    
    # Create student groups for ECE Year 1-4, Semester Odd/Even, Sections A/B/C
    groups_to_create = []
    for year in [1, 2, 3, 4]:
        for semester in ['Odd', 'Even']:
            for section in ['A', 'B', 'C']:
                groups_to_create.append({
                    'program_id': prog_id,
                    'year': year,
                    'semester': semester,
                    'section': section,
                    'created_at': asyncio.get_event_loop().time()
                })
    
    result = await db.student_groups.insert_many(groups_to_create)
    print(f'Created {len(result.inserted_ids)} student groups for ECE')
    
    # Verify
    groups = await db.student_groups.find({'program_id': prog_id}).to_list(None)
    print(f'Total ECE student groups now: {len(groups)}')
    print('Sample groups:')
    for g in groups[:5]:
        print(f'  - Year: {g.get("year")}, Semester: {g.get("semester")}, Section: {g.get("section")}')

asyncio.run(create_groups())
