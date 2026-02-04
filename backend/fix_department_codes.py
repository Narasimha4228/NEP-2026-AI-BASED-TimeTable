import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_all_timetables():
    client = AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/')
    db = client['timetable_db']
    
    # Get all programs with their codes
    programs = await db.programs.find().to_list(None)
    prog_map = {str(p['_id']): p['code'] for p in programs}
    
    print(f'Program mapping: {prog_map}')
    print()
    
    # Get all timetables and update missing department_code
    timetables = await db.timetables.find({'is_draft': False}).to_list(None)
    
    updated_count = 0
    for tt in timetables:
        # If no department_code, add it from program
        if not tt.get('department_code'):
            prog_id = str(tt.get('program_id', 'unknown'))
            dept_code = prog_map.get(prog_id, 'UNKNOWN')
            
            result = await db.timetables.update_one(
                {'_id': tt['_id']},
                {'$set': {'department_code': dept_code}}
            )
            if result.modified_count > 0:
                updated_count += 1
                print(f'Updated {dept_code} Semester {tt.get("semester")}: Added department_code')
    
    print(f'\nTotal updated: {updated_count}')
    
    # Verify
    timetables = await db.timetables.find({'is_draft': False}).to_list(None)
    print(f'\nVerification - All timetables now have department_code:')
    for tt in sorted(timetables, key=lambda x: (x.get('program_id'), x.get('semester'))):
        dept = tt.get('department_code', '?')
        sem = tt.get('semester', '?')
        entries = len(tt.get('entries', []))
        print(f'  {dept} Semester {sem}: {entries} entries')

asyncio.run(fix_all_timetables())
