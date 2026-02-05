import requests
import json

BASE_URL = 'http://localhost:8000/api/v1'

# Login
r = requests.post(f'{BASE_URL}/auth/login', data={'username': 'admin@example.com', 'password': 'admin123'})
if r.status_code != 200:
    print(f"Login failed")
    exit(1)
    
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get list of timetables first
print("Getting timetable list...")
r = requests.get(f'{BASE_URL}/timetable/', headers=headers)
timetables = r.json()
print(f"Found {len(timetables)} timetables\n")

# Find one with many entries
tt_with_most = None
max_entries = 0
for tt in timetables:
    entries_count = len(tt.get('entries', []))
    if entries_count > max_entries:
        max_entries = entries_count
        tt_with_most = tt

if tt_with_most:
    print(f"Timetable with most entries: {tt_with_most.get('id')}")
    print(f"Total entries: {len(tt_with_most['entries'])}\n")
    
    # Extract unique courses
    courses = {}
    for entry in tt_with_most['entries']:
        course_id = entry.get('course_id')
        course_code = entry.get('course_code')
        course_name = entry.get('course_name')
        
        if not course_id in courses:
            courses[course_id] = {
                'code': course_code,
                'name': course_name,
                'count': 0
            }
        courses[course_id]['count'] += 1
    
    print(f"Unique courses: {len(courses)}\n")
    for course_id, info in sorted(courses.items()):
        print(f"  {info['code']} ({course_id}): {info['name']} - {info['count']} entries")
