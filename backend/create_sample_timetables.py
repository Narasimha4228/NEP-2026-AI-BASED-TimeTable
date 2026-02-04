import asyncio
from motor import motor_asyncio
from bson import ObjectId
from datetime import datetime

async def create_timetables():
    """Create sample timetables for students"""
    
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    group_id = ObjectId('6971b4b3d91cfa375761779f')
    
    print("[1] Getting courses...")
    courses = await db.courses.find().to_list(100)
    print(f"    Found {len(courses)} courses")
    
    # Get a program
    program = await db.programs.find_one({'is_active': True})
    print(f"\n[2] Using program: {program.get('name')}")
    
    # Get rooms
    rooms = await db.rooms.find({'is_active': True}).to_list(20)
    print(f"[3] Found {len(rooms)} rooms")
    
    # Get faculty
    faculty = await db.faculty.find().to_list(20)
    print(f"[4] Found {len(faculty)} faculty members")
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    time_slots = ['08:00', '09:00', '10:00', '11:00', '14:00', '15:00']
    
    # Create 5 timetables for different semesters
    new_timetables = []
    for sem in range(1, 6):
        print(f"\n[5.{sem}] Creating timetable for semester {sem}...")
        
        # Get courses for this semester
        sem_courses = await db.courses.find({
            'program_id': program['_id'],
            'semester': sem
        }).to_list(50)
        
        if not sem_courses:
            print(f"    No courses for semester {sem}, creating with random courses...")
            sem_courses = courses[:5]
        
        entries = []
        for idx, course in enumerate(sem_courses[:6]):  # Max 6 courses per semester
            # Create 2 sessions per course (theory + lab)
            for session_type in ['theory', 'lab']:
                entry = {
                    'course_code': course.get('code', f'C{idx}'),
                    'course_name': course.get('name', f'Course {idx}'),
                    'day': days[(idx + len(entries)) % len(days)],
                    'start_time': time_slots[(idx + len(entries)) % len(time_slots)],
                    'end_time': time_slots[(idx + len(entries) + 1) % len(time_slots)],
                    'room': rooms[len(entries) % len(rooms)].get('code', 'A-101'),
                    'faculty': faculty[len(entries) % len(faculty)].get('name', 'Dr. Unknown'),
                    'faculty_id': faculty[len(entries) % len(faculty)].get('_id'),
                    'is_lab': session_type == 'lab',
                    'duration_minutes': 50,
                    'group': 'CSE',
                    'group_id': group_id
                }
                entries.append(entry)
        
        timetable = {
            'program_id': program['_id'],
            'semester': sem,
            'academic_year': '2025-2026',
            'title': f"{program.get('name')} - Semester {sem}",
            'is_draft': False,
            'entries': entries,
            'created_by': ObjectId('67f5fa7a0d000000000000d0'),
            'generated_at': datetime.utcnow(),
            'generation_method': 'manual_creation',
            'metadata': {
                'total_sessions': len(entries),
                'conflicts': 0
            }
        }
        new_timetables.append(timetable)
        print(f"    Created with {len(entries)} entries")
    
    # Insert all new timetables
    print(f"\n[6] Inserting {len(new_timetables)} new timetables...")
    result = await db.timetables.insert_many(new_timetables)
    print(f"[7] ✓ Created {len(result.inserted_ids)} timetables successfully")
    
    # Verify
    total_count = await db.timetables.count_documents({'is_draft': False})
    student_count = await db.timetables.count_documents({
        'entries.group_id': group_id,
        'is_draft': False
    })
    
    print(f"\n[8] Final counts:")
    print(f"    Total generated timetables: {total_count}")
    print(f"    Timetables for student group: {student_count}")
    print(f"\n✅ Timetables have been added successfully!")

asyncio.run(create_timetables())
