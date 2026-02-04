from jose import jwt, JWTError

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzAxMjc4MDYsInN1YiI6IjY5NzA3MzhkNTcxNDIwZjIwMTJkODgwZiJ9.XrmPoGiKnfqqe14aHdjH-qymb2kPxDRYLg7eOBrcgmE"
secret_key = "your-secret-key-here-change-in-production"
algorithm = "HS256"

print("=" * 60)
print("JWT DECODE TEST")
print("=" * 60)

try:
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    print(f"✅ Decoded successfully!")
    print(f"Payload: {payload}")
except JWTError as e:
    print(f"❌ JWT Error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
