import asyncio
from motor import motor_asyncio
from bson import ObjectId
from datetime import datetime
from app.services.timetable.advanced_generator import AdvancedTimetableGenerator
from app.db.mongodb import db as database

async def generate_timetables():
    """Generate multiple timetables for the student group"""
    
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db_conn = client['timetable_db']
    
    # Initialize database connection
    database.client = client
    database.db = db_conn
    
    print("[1] Getting programs...")
    programs = await db_conn.programs.find().to_list(100)
    print(f"    Found {len(programs)} programs")
    
    group_id = ObjectId('6971b4b3d91cfa375761779f')
    print(f"\n[2] Generating timetables for group: {group_id}")
    
    generator = AdvancedTimetableGenerator()
    
    generated_count = 0
    for program in programs[:3]:  # Generate for first 3 programs
        print(f"\n[3.{generated_count+1}] Generating for program: {program.get('name')}")
        
        try:
            # Get all semesters for this program
            for semester in range(1, program.get('total_semesters', 8) + 1):
                print(f"    Generating for semester {semester}...")
                
                # Get courses for this semester
                courses = await db_conn.courses.find({
                    'program_id': program['_id'],
                    'semester': semester
                }).to_list(100)
                
                if not courses:
                    print(f"    No courses found for semester {semester}, skipping...")
                    continue
                
                print(f"    Found {len(courses)} courses")
                
                # Create a timetable
                timetable_doc = {
                    'program_id': program['_id'],
                    'semester': semester,
                    'academic_year': '2025-2026',
                    'title': f"{program.get('name')} - Semester {semester}",
                    'is_draft': False,
                    'entries': [],
                    'created_by': ObjectId('67f5fa7a0d0000000000001'),  # Admin user
                    'generated_at': datetime.utcnow(),
                    'generation_method': 'advanced_generator',
                    'metadata': {
                        'total_sessions': 0,
                        'conflicts': 0
                    }
                }
                
                # Generate entries using the advanced generator
                try:
                    result = await generator.generate_for_group(
                        program_id=program['_id'],
                        semester=semester,
                        group_id=group_id
                    )
                    
                    if result and result.get('entries'):
                        timetable_doc['entries'] = result['entries']
                        timetable_doc['metadata']['total_sessions'] = len(result['entries'])
                        
                        # Insert timetable
                        insert_result = await db_conn.timetables.insert_one(timetable_doc)
                        print(f"    ✓ Timetable created: {insert_result.inserted_id}")
                        generated_count += 1
                    else:
                        print(f"    ✗ Generation failed for semester {semester}")
                        
                except Exception as e:
                    print(f"    Error generating for semester {semester}: {e}")
                    continue
                
        except Exception as e:
            print(f"    Error processing program: {e}")
            continue
    
    print(f"\n[4] Summary:")
    print(f"    Generated {generated_count} new timetables")
    
    # Verify
    total_timetables = await db_conn.timetables.count_documents({'is_draft': False})
    student_timetables = await db_conn.timetables.count_documents({
        'entries.group_id': group_id,
        'is_draft': False
    })
    
    print(f"\n[5] Final counts:")
    print(f"    Total generated timetables: {total_timetables}")
    print(f"    Timetables for student group: {student_timetables}")

if __name__ == '__main__':
    asyncio.run(generate_timetables())
