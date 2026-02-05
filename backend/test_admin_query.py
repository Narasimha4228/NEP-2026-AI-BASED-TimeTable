"""
Create a test endpoint to debug the timetables API
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.mongodb import db, connect_to_mongo, close_mongo_connection


async def test_admin_query():
    """Simulate what the admin API call should return"""
    await connect_to_mongo()
    
    print("\n" + "="*70)
    print("SIMULATING API QUERY (Admin Role)")
    print("="*70)
    
    try:
        print("\n📋 Query: Admin should see all timetables (drafts + published)")
        
        # Admin query
        query = {}  # Admin sees all
        timetables = await db.db.timetables.find(query).sort("created_at", -1).to_list(None)
        
        print(f"✓ Found {len(timetables)} timetables for admin")
        
        # Show first 5
        print("\nFirst 5 timetables:")
        for i, tt in enumerate(timetables[:5], 1):
            print(f"\n{i}. {tt.get('name') or 'Unnamed'}")
            print(f"   ID: {tt.get('_id')}")
            print(f"   Draft: {tt.get('is_draft')}")
            print(f"   Entries: {len(tt.get('entries', []))}")
        
        print("\n" + "="*70)
        print("✓ API SHOULD RETURN these timetables to admin users")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(test_admin_query())
