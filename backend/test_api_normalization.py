import requests
import json

BASE_URL = 'http://localhost:8000/api/v1'

# Login
r = requests.post(f'{BASE_URL}/auth/login', data={'username': 'admin@example.com', 'password': 'admin123'})
if r.status_code != 200:
    print(f"Login failed: {r.status_code}")
    print(r.text)
    exit(1)
    
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get list of timetables first
print("Getting timetable list...")
r = requests.get(f'{BASE_URL}/timetable/', headers=headers)
timetables = r.json()
print(f"Found {len(timetables)} timetables")

# Find one with entries
for tt in timetables:
    if len(tt.get('entries', [])) > 0:
        print(f"\nTimetable with entries: {tt.get('id')}")
        print(f"Entries count: {len(tt['entries'])}")
        
        entry = tt['entries'][0]
        print("\n✓ First entry from LIST endpoint:")
        print(json.dumps(entry, indent=2))
        break
