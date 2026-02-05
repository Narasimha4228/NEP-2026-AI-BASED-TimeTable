"""
Test the getAllTimetables API endpoint
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.mongodb import db, connect_to_mongo, close_mongo_connection


async def test_get_timetables():
    """Test get timetables endpoint"""
    await connect_to_mongo()
    
    print("\n" + "="*70)
    print("TESTING GET TIMETABLES ENDPOINT")
    print("="*70)
    
    try:
        # Simulate admin user
        print("\n✓ Connected to database")
        
        # Count all timetables
        all_count = await db.db.timetables.count_documents({})
        print(f"\nTotal timetables in DB: {all_count}")
        
        # Count published timetables
        published_count = await db.db.timetables.count_documents({"is_draft": False})
        print(f"Published timetables: {published_count}")
        
        # Count draft timetables
        draft_count = await db.db.timetables.count_documents({"is_draft": True})
        print(f"Draft timetables: {draft_count}")
        
        # Get all published timetables (what students/faculty would see)
        query = {"is_draft": False}
        timetables = await db.db.timetables.find(query).to_list(10)
        
        print(f"\n📋 Published timetables fetched: {len(timetables)}")
        
        if timetables:
            print("\n✓ First timetable:")
            tt = timetables[0]
            print(f"  ID: {tt.get('_id')}")
            print(f"  Name: {tt.get('name')}")
            print(f"  Entries: {len(tt.get('entries', []))}")
            print(f"  Draft: {tt.get('is_draft')}")
        else:
            print("\n⚠️  WARNING: No published timetables found!")
            print("   This is why the frontend shows empty.")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(test_get_timetables())
