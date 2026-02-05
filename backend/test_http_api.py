"""
Test HTTP API call to timetables endpoint
Must be run while backend is running!
"""
import subprocess
import json

print("\n" + "="*70)
print("TESTING HTTP API CALL TO /timetable/")
print("="*70)

# Step 1: Login to get token
print("\n1️⃣  Getting auth token...")

login_cmd = [
    "powershell", "-Command",
    """
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/login" `
      -Method POST `
      -ContentType "application/json" `
      -Body '{"email":"admin@example.com","password":"admin123"}' -ErrorAction SilentlyContinue
    $response.Content
    """
]

try:
    result = subprocess.run(login_cmd, capture_output=True, text=True, timeout=10)
    login_response = result.stdout.strip()
    print(f"Response: {login_response[:200]}...")
    
    # Parse token
    try:
        login_data = json.loads(login_response)
        token = login_data.get('access_token')
        if token:
            print(f"✓ Got token: {token[:30]}...")
        else:
            print("❌ No token in response")
            print(f"Full response: {login_data}")
    except:
        print(f"❌ Failed to parse login response")
        print(f"Raw response: {login_response}")
        token = None
        
except Exception as e:
    print(f"❌ Error: {e}")
    token = None

# Step 2: Call timetables endpoint
if token:
    print("\n2️⃣  Calling /timetable/ with auth token...")
    
    timetables_cmd = [
        "powershell", "-Command",
        f"""
        $headers = @{{
            "Authorization" = "Bearer {token}"
            "Content-Type" = "application/json"
        }}
        
        try {{
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/timetable/" `
              -Headers $headers -ErrorAction Stop
            $response.StatusCode
            $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 2
        }} catch {{
            "Error: $($_.Exception.Response.StatusCode)"
            $_.Exception.Response.Content.ReadAsStringAsync()
        }}
        """
    ]
    
    try:
        result = subprocess.run(timetables_cmd, capture_output=True, text=True, timeout=10)
        print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("\n❌ Cannot test API without token")

print("\n" + "="*70)
