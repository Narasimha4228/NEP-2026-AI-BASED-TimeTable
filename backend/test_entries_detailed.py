import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Login
print("📥 Logging in...")
r = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "admin@example.com", "password": "admin123"},
    timeout=5
)
print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(f"Response: {r.text}")
    print("❌ Login failed!")
    exit(1)
token = r.json()["access_token"]
print(f"✓ Token: {token[:50]}...")

# Get timetables
headers = {"Authorization": f"Bearer {token}"}
print("\n📥 Getting timetables...", end=" ")
r = requests.get(f"{BASE_URL}/timetable/", headers=headers)
print(f"Status: {r.status_code}")

timetables = r.json()
print(f"✓ Total timetables: {len(timetables)}")

if timetables:
    # Find a timetable with entries
    tt_with_entries = None
    for tt in timetables:
        if len(tt.get('entries', [])) > 0:
            tt_with_entries = tt
            break
    
    if tt_with_entries is None:
        print("⚠️ No timetables with entries found in list. Trying specific IDs...")
        # Try specific IDs we know have entries
        specific_ids = ['69841c56a880b99357f15b1f', '6984140ea880b99357f15b16']
        for tid in specific_ids:
            r = requests.get(f"{BASE_URL}/timetable/{tid}", headers=headers)
            if r.status_code == 200:
                tt_with_entries = r.json()
                print(f"Found timetable with ID {tid}")
                break
    
    if tt_with_entries:
        tt = tt_with_entries
        print(f"\nTimetable details:")
        print(f"  ID: {tt.get('id')}")
        print(f"  Title: {tt.get('title')}")
        print(f"  Entries count: {len(tt.get('entries', []))}")
        
        if tt.get('entries'):
            entry = tt['entries'][0]
            print(f"\nFirst entry structure:")
            print(json.dumps(entry, indent=2))
        else:
            print(f"  ⚠️ No entries in this timetable")
    else:
        print("❌ Could not find any timetable with entries")
