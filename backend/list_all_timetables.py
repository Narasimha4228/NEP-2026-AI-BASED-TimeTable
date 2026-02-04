import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def list_all_timetables():
    client = AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/')
    db = client['timetable_db']
    
    # Get all published timetables
    timetables = await db.timetables.find({'is_draft': False}).to_list(None)
    print(f'Total Published Timetables: {len(timetables)}')
    print()
    
    # Group by program and semester
    by_program = {}
    for tt in timetables:
        prog_id = str(tt.get('program_id', 'unknown'))
        sem = tt.get('semester', 'unknown')
        entries_count = len(tt.get('entries', []))
        dept_code = tt.get('department_code', '?')
        
        if prog_id not in by_program:
            by_program[prog_id] = []
        by_program[prog_id].append({
            'semester': sem,
            'entries': entries_count,
            'dept_code': dept_code,
            'id': str(tt.get('_id'))
        })
    
    # Print organized
    for prog_id, timetables_list in sorted(by_program.items()):
        print(f'Program {prog_id}:')
        for tt in sorted(timetables_list, key=lambda x: x['semester']):
            print(f'  - Semester {tt["semester"]} ({tt["dept_code"]}): {tt["entries"]} entries')

asyncio.run(list_all_timetables())
