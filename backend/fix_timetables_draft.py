import asyncio
from motor import motor_asyncio
from bson import ObjectId

async def fix_timetables():
    client = motor_asyncio.AsyncIOMotorClient('mongodb+srv://Reddy:Reddy@cluster0.ot3jl.mongodb.net/?retryWrites=true&w=majority')
    db = client['timetable_db']
    
    group_id = ObjectId('6971b4b3d91cfa375761779f')
    
    print("=" * 60)
    print("[1] CHECKING TIMETABLES")
    print("=" * 60)
    
    # Check all timetables
    all_tts = await db.timetables.find({}).to_list(20)
    print(f"Total timetables: {len(all_tts)}")
    
    for idx, tt in enumerate(all_tts[:3]):
        print(f"\n  Timetable {idx+1}:")
        print(f"    ID: {tt.get('_id')}")
        print(f"    is_draft: {tt.get('is_draft')}")
        print(f"    entries: {len(tt.get('entries', []))}")
        print(f"    generated_at: {tt.get('generated_at')}")
    
    print("\n" + "=" * 60)
    print("[2] CHECKING FOR GROUP_ID MATCHES")
    print("=" * 60)
    
    # Check with group_id
    tts_with_group = await db.timetables.find({
        'entries.group_id': group_id
    }).to_list(20)
    print(f"Timetables with group_id {group_id}: {len(tts_with_group)}")
    
    # Check with is_draft=False
    tts_not_draft = await db.timetables.find({
        'is_draft': False
    }).to_list(20)
    print(f"Timetables with is_draft=False: {len(tts_not_draft)}")
    
    # Check both conditions
    tts_match = await db.timetables.find({
        'entries.group_id': group_id,
        'is_draft': False
    }).to_list(20)
    print(f"Timetables matching BOTH conditions: {len(tts_match)}")
    
    print("\n" + "=" * 60)
    print("[3] FIXING TIMETABLES")
    print("=" * 60)
    
    # Update all timetables to have is_draft=False and generated_at
    from datetime import datetime
    result = await db.timetables.update_many(
        {},
        {
            '$set': {
                'is_draft': False,
                'generated_at': datetime.utcnow()
            }
        }
    )
    
    print(f"✅ Updated {result.modified_count} timetables")
    
    # Verify
    tts_verify = await db.timetables.find({
        'entries.group_id': group_id,
        'is_draft': False
    }).to_list(20)
    
    print(f"✅ Timetables now matching: {len(tts_verify)}")
    
    if tts_verify:
        tt = tts_verify[0]
        print(f"\nFirst matching timetable:")
        print(f"  Entries: {len(tt.get('entries', []))}")
        print(f"  is_draft: {tt.get('is_draft')}")
        print(f"  generated_at: {tt.get('generated_at')}")

asyncio.run(fix_timetables())
