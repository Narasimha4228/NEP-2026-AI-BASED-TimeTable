"""
Direct test of the API endpoint
Requires: requests, running backend, running database
"""
print("\n1. Checking if requests is installed...")

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.run([__import__('sys').executable, "-m", "pip", "install", "requests"], 
                   capture_output=True)
    import requests

print("✓ requests imported\n")

BASE_URL = "http://localhost:8000/api/v1"

print("="*70)
print("TESTING API WITH HTTP REQUESTS")
print("="*70)

# Step 1: Login
print("\n1️⃣  Logging in...")
try:
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin@example.com", "password": "admin123"},
        timeout=5
    )
    print(f"Status: {login_resp.status_code}")
    
    if login_resp.status_code == 200:
        login_data = login_resp.json()
        token = login_data.get('access_token')
        print(f"✓ Got token: {token[:30]}...")
    else:
        print(f"❌ Login failed: {login_resp.text}")
        token = None
except Exception as e:
    print(f"❌ Connection error: {e}")
    token = None

# Step 2: Get timetables
if token:
    print("\n2️⃣  Getting timetables...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/timetable/", headers=headers, timeout=5)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            timetables = resp.json()
            print(f"✓ Got {len(timetables)} timetables")
            
            if timetables:
                print("\nFirst timetable:")
                tt = timetables[0]
                print(f"  ID: {tt.get('id') or tt.get('_id')}")
                print(f"  Name: {tt.get('name')}")
                print(f"  Entries: {len(tt.get('entries', []))}")
            else:
                print("⚠️  Empty timetables list returned")
        else:
            print(f"❌ API error: {resp.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No token, skipping API call")

print("\n" + "="*70)
