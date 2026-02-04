import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def fix_ece_timetable():
    client = AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/')
    db = client['timetable_db']
    
    # Get the ECE Semester 3 timetable
    tt = await db.timetables.find_one({'_id': ObjectId('69785f725ed0b92c970dbe87')})
    if not tt:
        print('Timetable not found')
        return
    
    # Create proper ECE entries for Semester 3
    entries = [
        {
            'course_code': 'EC301',
            'course_name': 'Digital Systems',
            'day': 'Monday',
            'start_time': '09:00',
            'end_time': '10:00',
            'room': 'Room 201',
            'faculty': 'Dr. Smith',
            'is_lab': False
        },
        {
            'course_code': 'EC302',
            'course_name': 'Signals and Systems',
            'day': 'Tuesday',
            'start_time': '10:00',
            'end_time': '11:00',
            'room': 'Room 202',
            'faculty': 'Dr. Johnson',
            'is_lab': False
        },
        {
            'course_code': 'EC303L',
            'course_name': 'Electronics Lab',
            'day': 'Wednesday',
            'start_time': '09:00',
            'end_time': '11:00',
            'room': 'Lab 103',
            'faculty': 'Prof. Williams',
            'is_lab': True
        },
        {
            'course_code': 'EC304',
            'course_name': 'Communication Systems',
            'day': 'Thursday',
            'start_time': '11:00',
            'end_time': '12:00',
            'room': 'Room 301',
            'faculty': 'Dr. Brown',
            'is_lab': False
        },
        {
            'course_code': 'EC305',
            'course_name': 'Microprocessors',
            'day': 'Friday',
            'start_time': '09:00',
            'end_time': '10:00',
            'room': 'Room 305',
            'faculty': 'Dr. Davis',
            'is_lab': False
        },
    ]
    
    # Update timetable with new entries
    result = await db.timetables.update_one(
        {'_id': tt['_id']},
        {
            '$set': {
                'entries': entries,
                'department_code': 'ECE'
            }
        }
    )
    
    print(f'Updated timetable with {len(entries)} ECE entries')
    print(f'Matched: {result.matched_count}, Modified: {result.modified_count}')
    
    # Verify
    tt = await db.timetables.find_one({'_id': tt['_id']})
    print(f'Timetable now has {len(tt.get("entries", []))} entries')
    print(f'Department code: {tt.get("department_code")}')
    if tt.get('entries'):
        for e in tt['entries'][:3]:
            print(f'  - {e["course_name"]} on {e["day"]} at {e["start_time"]}')

asyncio.run(fix_ece_timetable())
