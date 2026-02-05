"""
Debug script to check if timetable is in database and working
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.mongodb import db, connect_to_mongo, close_mongo_connection


async def debug_timetable():
    """Check timetable in database"""
    await connect_to_mongo()
    
    print("\n" + "="*60)
    print("DEBUGGING TIMETABLE STATUS")
    print("="*60)
    
    try:
        # Check connection
        print("\n✓ Database connected")
        
        # Count timetables
        total_count = await db.db.timetables.count_documents({})
        print(f"\nTotal timetables in DB: {total_count}")
        
        # Count published timetables
        published_count = await db.db.timetables.count_documents({"is_draft": False})
        print(f"Published timetables: {published_count}")
        
        # Get the timetable we just created
        timetable = await db.db.timetables.find_one({"is_draft": False})
        
        if not timetable:
            print("\n❌ NO PUBLISHED TIMETABLE FOUND!")
            return
        
        print(f"\n✓ Found timetable!")
        print(f"  Name: {timetable.get('name')}")
        print(f"  ID: {timetable.get('_id')}")
        print(f"  Published: {not timetable.get('is_draft')}")
        print(f"  Entries count: {len(timetable.get('entries', []))}")
        
        # Show first few entries
        entries = timetable.get('entries', [])
        if entries:
            print(f"\n📋 First 3 entries:")
            for i, entry in enumerate(entries[:3]):
                print(f"\n  Entry {i+1}:")
                print(f"    Course: {entry.get('course_name')} ({entry.get('course_code')})")
                print(f"    Room: {entry.get('room_number')}")
                print(f"    Time: {entry.get('day_of_week')} {entry.get('start_time')}-{entry.get('end_time')}")
                print(f"    Instructor: {entry.get('instructor_name')}")
        else:
            print("\n⚠️  WARNING: Timetable has NO entries!")
        
        print("\n" + "="*60)
        print(f"✓ TIMETABLE ID TO USE: {timetable.get('_id')}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(debug_timetable())
