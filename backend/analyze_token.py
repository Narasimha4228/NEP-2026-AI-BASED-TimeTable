import json
import base64

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzAxMjc4MDYsInN1YiI6IjY5NzA3MzhkNTcxNDIwZjIwMTJkODgwZiJ9.XrmPoGiKnfqqe14aHdjH-qymb2kPxDRYLg7eOBrcgmE"

parts = token.split('.')
print("=" * 60)
print("TOKEN ANALYSIS")
print("=" * 60)

# Decode header
header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
print(f"Header: {header}")

# Decode payload
payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
print(f"Payload: {payload}")

# Check expiration
import time
exp = payload.get('exp')
now = time.time()
print(f"\nExpiration check:")
print(f"  Current time: {now}")
print(f"  Token exp: {exp}")
print(f"  Expired: {exp < now}")
print(f"  Time remaining: {exp - now:.0f} seconds ({(exp - now)/3600:.1f} hours)")

# Get sub (user ID)
print(f"\nUser ID (sub): {payload.get('sub')}")
