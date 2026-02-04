import json

# Fresh token (valid for 24 hours)
fresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzAxMjc4MDYsInN1YiI6IjY5NzA3MzhkNTcxNDIwZjIwMTJkODgwZiJ9.XrmPoGiKnfqqe14aHdjH-qymb2kPxDRYLg7eOBrcgmE"

# Zustand persist format
auth_store_data = {
    "state": {
        "user": {
            "id": "6970738d571420f2012d880f",
            "email": "test2@example.com",
            "name": "Test User 2",
            "full_name": "Test User 2",
            "is_active": True,
            "is_admin": True,
            "role": "admin"
        },
        "token": fresh_token,
        "isAuthenticated": True
    }
}

print("=" * 60)
print("INSTRUCTIONS TO UPDATE FRONTEND AUTH")
print("=" * 60)
print("\n1. Open browser DevTools (F12)")
print("2. Go to Application → Local Storage → http://localhost:5173")
print("3. Find the key 'auth-storage' and click it")
print("4. Replace the value with this JSON:\n")
print(json.dumps(auth_store_data, indent=2))
print("\n5. Press Enter and refresh the page")
print("\n6. Go to Access Management page - users should now load!")
