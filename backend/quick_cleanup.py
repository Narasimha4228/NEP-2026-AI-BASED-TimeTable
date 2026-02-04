#!/usr/bin/env python
"""Quick cleanup of bad test data"""
import asyncio, sys
from pathlib import Path
from bson import ObjectId
Path(__file__).parent.with_name('backend').__str__() if 'backend' not in str(Path.cwd()) else None
sys.path.insert(0, str(Path(__file__).parent))
from app.db.mongodb import db, connect_to_mongo

async def main():
    await connect_to_mongo()
    # Delete old bad timetable
    r = await db.db.timetables.delete_many({"title": "Test Timetable - CSE Year 1"})
    print(f"Deleted {r.deleted_count} timetables")
    # Verify
    count = await db.db.timetables.count_documents({"title": "Test Timetable - CSE Year 1"})
    print(f"Remaining: {count}")

asyncio.run(main())
