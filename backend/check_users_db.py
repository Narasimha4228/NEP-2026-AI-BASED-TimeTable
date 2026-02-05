#!/usr/bin/env python3
"""Check admin users and credentials in database"""

import asyncio
from app.db.mongodb import connect_to_mongo, db
from bson import ObjectId

async def check_users():
    await connect_to_mongo()
    
    print("Checking users in database...")
    users = await db.db.users.find({}).to_list(length=None)
    
    print(f"\nTotal users: {len(users)}\n")
    for user in users:
        print(f"ID: {user.get('_id')}")
        print(f"  Email: {user.get('email')}")
        print(f"  Username: {user.get('username')}")
        print(f"  Role: {user.get('role')}")
        print(f"  Is Active: {user.get('is_active')}")
        print()

asyncio.run(check_users())
