import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def check_timetables():
    client = AsyncIOMotorClient(settings.MONGODB_URL, tls=True, tlsAllowInvalidCertificates=True)
    db = client[settings.DATABASE_NAME]
    
    timetables = db['timetables']
    
    # Get first timetable
    tt = await timetables.find_one()
    if tt:
        print("=" * 80)
        print("Timetable Document Structure:")
        print("=" * 80)
        tt['_id'] = str(tt['_id'])
        
        # Show all keys
        print(f"\nKeys in document: {list(tt.keys())}")
        print(f"\nDocument size: {len(json.dumps(tt, default=str))} bytes")
        
        # Check entries
        entries = tt.get('entries', [])
        print(f"\nEntries count: {len(entries)}")
        
        if entries:
            print(f"\nFirst entry structure:")
            print(json.dumps(entries[0], indent=2, default=str))
        else:
            print("\n⚠️  NO ENTRIES FOUND IN TIMETABLE")
            
        # Show metadata
        print(f"\nMetadata:")
        print(f"  - is_draft: {tt.get('is_draft')}")
        print(f"  - name: {tt.get('name')}")
        print(f"  - program_id: {tt.get('program_id')}")
        print(f"  - semester: {tt.get('semester')}")
        print(f"  - academic_year: {tt.get('academic_year')}")
        
    else:
        print("❌ No timetables found in database")
    
    client.close()

asyncio.run(check_timetables())
