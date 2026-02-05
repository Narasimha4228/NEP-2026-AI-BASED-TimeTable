import requests
import json

BASE_URL = 'http://localhost:8000/api/v1'

# Login
r = requests.post(f'{BASE_URL}/auth/login', data={'username': 'admin@example.com', 'password': 'admin123'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get a timetable with entries
r = requests.get(f'{BASE_URL}/timetable/69841c56a880b99357f15b1f', headers=headers)
tt = r.json()

print('📋 Timetable Structure:')
print(f'Title: {tt.get("title")}')
print(f'Entries: {len(tt.get("entries", []))}')

if tt.get('entries'):
    print('\nFirst entry structure:')
    entry = tt['entries'][0]
    print(f'  Course: {entry.get("course_name")} ({entry.get("course_code")})')
    print(f'  Faculty: {entry.get("faculty")}')
    print(f'  Room: {entry.get("room")}')
    timeslot = entry.get('time_slot', {})
    print(f'  Time: {timeslot.get("day")} {timeslot.get("start_time")}-{timeslot.get("end_time")}')
    print('\nFull entry for debugging (JSON):')
    print(json.dumps(entry, indent=2))
else:
    print('No entries found')
