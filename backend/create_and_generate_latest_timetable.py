#!/usr/bin/env python3
import asyncio
from app.db.mongodb import connect_to_mongo, db
from bson import ObjectId
from datetime import datetime

async def create_and_generate_latest_timetable():
    await connect_to_mongo()
    # Get first available student group
    group = await db.db.student_groups.find_one({})
    if not group:
        print('No student groups found in the database.')
        return
    default_group_id = str(group['_id'])
    print(f'Using default group: {group.get("name", "Unnamed Group")} (ID: {default_group_id})')

    # Get program and semester from group
    program_id = group.get('program_id')
    semester = group.get('semester')
    if not program_id or not semester:
        print('Group missing program_id or semester.')
        return

    # Find admin user
    admin_user = await db.db.users.find_one({'role': 'admin'})
    if not admin_user:
        print('No admin user found.')
        return
    admin_id = str(admin_user['_id'])

    # Create timetable document
    timetable_doc = {
        'program_id': ObjectId(program_id),
        'semester': semester,
        'group_id': default_group_id,
        'created_by': ObjectId(admin_id),
        'created_at': datetime.utcnow(),
        'is_draft': True,
        'entries': [],
        'validation_status': 'draft',
    }
    result = await db.db.timetables.insert_one(timetable_doc)
    timetable_id = str(result.inserted_id)
    print(f'Created timetable with ID: {timetable_id}')

    # Simulate admin context for generation
    from app.services.timetable.advanced_generator import AdvancedTimetableGenerator
    generator = AdvancedTimetableGenerator()
    await generator.load_from_database_with_setup(str(program_id), semester, None)
    loop = asyncio.get_running_loop()
    gen_result = await loop.run_in_executor(None, generator.generate_timetable, str(program_id), semester)

    if not gen_result.get('success'):
        print(f"Generation failed: {gen_result.get('error')}")
        return

    # Save generated entries into timetable document
    entries = gen_result.get('schedule', [])
    update_doc = {
        'entries': entries,
        'is_draft': False,
        'generated_at': datetime.utcnow(),
        'generation_method': 'advanced',
        'validation_status': 'generated',
        'optimization_score': gen_result.get('score'),
        'metadata': {
            'generation_attempts': gen_result.get('attempts_made'),
            'statistics': gen_result.get('statistics'),
            'validation': gen_result.get('validation')
        }
    }
    await db.db.timetables.update_one({'_id': ObjectId(timetable_id)}, {'$set': update_doc})
    print('Timetable generated and updated successfully.')

if __name__ == '__main__':
    asyncio.run(create_and_generate_latest_timetable())
