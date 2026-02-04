#!/usr/bin/env python3
import asyncio
from app.db.mongodb import connect_to_mongo, db
from bson import ObjectId

async def assign_students_to_default_group():
    await connect_to_mongo()
    # Get first available student group
    group = await db.db.student_groups.find_one({})
    if not group:
        print('No student groups found in the database.')
        return
    default_group_id = str(group['_id'])
    print(f'Using default group: {group.get("name", "Unnamed Group")} (ID: {default_group_id})')

    # Find all student users without a group_id
    students = await db.db.users.find({
        'role': 'student',
        '$or': [
            {'group_id': {'$exists': False}},
            {'group_id': None},
            {'group_id': ''}
        ]
    }).to_list(length=None)
    print(f'Found {len(students)} students without a group_id.')

    # Assign each student to the default group
    for student in students:
        result = await db.db.users.update_one(
            {'_id': student['_id']},
            {'$set': {'group_id': default_group_id}}
        )
        print(f"Assigned student {student.get('full_name', student.get('email', str(student['_id'])))} to group {default_group_id}")

    print('Done.')

if __name__ == '__main__':
    asyncio.run(assign_students_to_default_group())
