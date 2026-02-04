from app.core.config import settings
import hmac
import hashlib

print("=" * 60)
print("SECRET KEY CHECK")
print("=" * 60)
print(f"SECRET_KEY: {settings.SECRET_KEY}")
print(f"Algorithm: {settings.ALGORITHM}")

# Try to verify the token signature manually
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzAxMjc4MDYsInN1YiI6IjY5NzA3MzhkNTcxNDIwZjIwMTJkODgwZiJ9.XrmPoGiKnfqqe14aHdjH-qymb2kPxDRYLg7eOBrcgmE"

parts = token.split('.')
header_payload = f"{parts[0]}.{parts[1]}"
signature = parts[2]

# Calculate expected signature
import json
import base64

expected_sig = hmac.new(
    settings.SECRET_KEY.encode(),
    header_payload.encode(),
    hashlib.sha256
).digest()

# Base64 encode without padding
import base64
expected_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')

print(f"\nToken signature check:")
print(f"  Provided signature: {signature}")
print(f"  Expected signature: {expected_b64}")
print(f"  Match: {signature == expected_b64}")
