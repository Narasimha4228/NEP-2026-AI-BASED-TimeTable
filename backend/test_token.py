import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzAxMjc4MDYsInN1YiI6IjY5NzA3MzhkNTcxNDIwZjIwMTJkODgwZiJ9.XrmPoGiKnfqqe14aHdjH-qymb2kPxDRYLg7eOBrcgmE"

print("=" * 60)
print("TEST 1: With Authorization header")
print("=" * 60)
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/users", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

print("\n" + "=" * 60)
print("TEST 2: Without Authorization header")
print("=" * 60)
response = requests.get("http://localhost:8000/api/v1/users")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
