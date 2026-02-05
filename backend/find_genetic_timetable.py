"""
Find and check our genetic model timetable
"""
import asyncio
import sys
from pathlib import Path
from bson import ObjectId

sys.path.insert(0, str(Path(__file__).parent))

from app.db.mongodb import db, connect_to_mongo, close_mongo_connection


async def find_genetic_timetable():
    """Find the timetable we just created from genetic model"""
    await connect_to_mongo()
    
    print("\n" + "="*70)
    print("LOOKING FOR GENETIC MODEL TIMETABLE")
    print("="*70)
    
    try:
        # Look for timetables with genetic algorithm metadata
        genetic_tt = await db.db.timetables.find_one(
            {"metadata.genetic_algorithm": {"$exists": True}}
        )
        
        if genetic_tt:
            print(f"\n✓ Found genetic model timetable!")
            print(f"  ID: {genetic_tt.get('_id')}")
            print(f"  Name: {genetic_tt.get('name')}")
            print(f"  Entries: {len(genetic_tt.get('entries', []))}")
            print(f"  Published: {not genetic_tt.get('is_draft')}")
            
            entries = genetic_tt.get('entries', [])
            if entries:
                print(f"\n📋 First entry details:")
                entry = entries[0]
                for key, value in entry.items():
                    print(f"  {key}: {value}")
            
            print(f"\n{'='*70}")
            print(f"GENETIC TIMETABLE ID: {genetic_tt.get('_id')}")
            print(f"{'='*70}")
        else:
            print("\n❌ NO GENETIC MODEL TIMETABLE FOUND")
            
            # Show all published timetables
            print("\n📋 All published timetables:")
            all_published = await db.db.timetables.find({"is_draft": False}).to_list(10)
            for i, tt in enumerate(all_published, 1):
                print(f"\n{i}. ID: {tt.get('_id')}")
                print(f"   Name: {tt.get('name')}")
                print(f"   Entries: {len(tt.get('entries', []))}")
                if tt.get('entries'):
                    first = tt.get('entries')[0]
                    print(f"   First entry: {first.get('course_name', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(find_genetic_timetable())
