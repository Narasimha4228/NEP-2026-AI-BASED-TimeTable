#!/usr/bin/env python
"""Test the /users endpoint directly"""

import asyncio
import httpx
from app.db.mongodb import connect_to_mongo

async def test_users_endpoint():
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Test without auth (should fail with 403)
    print("\n❌ TEST 1: GET /api/v1/users WITHOUT TOKEN")
    print("-" * 60)
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            response = await client.get("/api/v1/users", timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_users_endpoint())
