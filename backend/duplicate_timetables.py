import asyncio
from motor import motor_asyncio
from bson import ObjectId
from datetime import datetime

async def duplicate_timetables():
    """Duplicate the existing timetable for multiple semesters"""
    
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    print("[1] Getting existing timetable...")
    existing_tt = await db.timetables.find_one(
        {'entries.0': {'$exists': True}, 'is_draft': False}
    )
    
    if not existing_tt:
        print("No existing timetable found!")
        return
    
    print(f"[2] Found timetable with {len(existing_tt.get('entries', []))} entries")
    
    # Create 4 duplicate timetables with different semesters
    new_timetables = []
    for sem in range(1, 5):
        new_tt = {
            'program_id': existing_tt['program_id'],
            'semester': sem,
            'academic_year': '2025-2026',
            'title': f"Semester {sem} - 2025-2026",
            'is_draft': False,
            'entries': [
                {**entry, 'group_id': entry.get('group_id')}
                for entry in existing_tt.get('entries', [])
            ],
            'created_by': existing_tt.get('created_by', ObjectId('67f5fa7a0d0000000000001')),
            'generated_at': datetime.utcnow(),
            'generation_method': 'duplication',
            'metadata': {
                'total_sessions': len(existing_tt.get('entries', [])),
                'conflicts': 0
            }
        }
        new_timetables.append(new_tt)
    
    # Insert all new timetables
    print(f"[3] Inserting {len(new_timetables)} new timetables...")
    result = await db.timetables.insert_many(new_timetables)
    print(f"[4] Created {len(result.inserted_ids)} new timetables")
    
    # Verify
    total_count = await db.timetables.count_documents({'is_draft': False})
    group_id = existing_tt['entries'][0].get('group_id')
    student_count = await db.timetables.count_documents({
        'entries.group_id': group_id,
        'is_draft': False
    })
    
    print(f"\n[5] Final counts:")
    print(f"    Total generated timetables: {total_count}")
    print(f"    Timetables for student group: {student_count}")

asyncio.run(duplicate_timetables())
