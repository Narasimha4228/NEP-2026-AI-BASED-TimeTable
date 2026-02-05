import asyncio
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import json

async def check_entry_structure():
    client = AsyncIOMotorClient(settings.MONGODB_URL, tls=True, tlsAllowInvalidCertificates=True)
    db = client[settings.DATABASE_NAME]
    
    # Get the specific timetable
    try:
        tt = await db['timetables'].find_one({'_id': ObjectId('69841c56a880b99357f15b1f')})
    except:
        tt = await db['timetables'].find_one({'_id': '69841c56a880b99357f15b1f'})
    
    if tt:
        print("✓ Found timetable")
        print(f"Entries count: {len(tt.get('entries', []))}")
        
        if tt.get('entries'):
            entry = tt['entries'][0]
            print("\nFirst entry from database (raw):")
            # Convert ObjectIds to strings for JSON serialization
            def convert_oid(obj):
                if isinstance(obj, ObjectId):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_oid(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_oid(v) for v in obj]
                return obj
            entry_clean = convert_oid(entry)
            print(json.dumps(entry_clean, indent=2))
            
            print("\nEntry fields:")
            for key in sorted(entry.keys()):
                val = entry[key]
                print(f"  {key}: {type(val).__name__} = {val}")
    else:
        print("❌ Timetable not found")
    
    client.close()

asyncio.run(check_entry_structure())
