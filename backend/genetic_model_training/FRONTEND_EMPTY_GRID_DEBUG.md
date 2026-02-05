# Frontend Empty Grid - Complete Diagnosis & Fix

## 🔍 THE PROBLEM (3 Possible Causes)

### Backend Side ✓
```
✓ Database has timetable: 6984411e61c6ef3ed8284460
✓ Timetable has 40 complete entries
✓ API endpoint exists: /timetable/public/{id}
✓ Data is ready to serve
```

### API Side ✗
```
❌ API requires authentication (JWT token)
❌ Endpoint checks: Depends(get_current_active_user)
❌ If no valid token → Returns: {"detail":"Not authenticated"}
❌ Frontend doesn't show error message
```

### Frontend Side ✗
Possible causes:
1. User not logged in
2. Token expired
3. Auth not properly stored in localStorage
4. Silent error (no error display to user)

---

## 🔧 HOW TO FIX - STEP BY STEP

### STEP 1: Check if User is Logged In

**In Browser (F12 → Console), run:**
```javascript
// Check if user has auth token
const auth = localStorage.getItem('auth-storage');
console.log('Auth Storage:', auth);
console.log('Token exists:', !!auth);
if (auth) {
    const parsed = JSON.parse(auth);
    console.log('Token:', parsed?.state?.token?.substring(0, 30) + '...');
    console.log('Authenticated:', parsed?.state?.isAuthenticated);
}
```

### Expected Output if LOGGED IN ✓:
```
Auth Storage: {"state":{"token":"eyJhbGc...", "isAuthenticated": true, ...}}
Token exists: true
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6...
Authenticated: true
```

### If Output Shows:
```
Auth Storage: null
Token exists: false
```
**→ User is NOT logged in! Need to log in first.**

---

### STEP 2: Log In If Needed

**Option A: In Frontend UI**
1. Go to login page
2. Enter credentials (admin@example.com / admin123)
3. Click Login
4. Wait for redirect to dashboard

**Option B: Via API (Terminal)**
```bash
# Get auth token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Response will include "access_token"
```

---

### STEP 3: Check Browser Console Logs

**Open Network Tab (F12 → Network):**
1. Refresh page
2. Look for request to `/timetable/public/6984411e61c6ef3ed8284460`
3. Check response:
   - ✓ Status 200 = working
   - ❌ Status 401 = not authenticated
   - ❌ Status 404 = not found

**In Console (F12 → Console):**
1. Look for these messages:
   ```
   ✅ TimetableService - Authorization header added
   📥 Fetching timetable by ID from: http://localhost:8000/api/v1/timetable/public/...
   📦 Timetable response: {...}
   ```
2. Or error messages:
   ```
   ❌ getTimetableById error: 401
   ⚠️ TimetableService - No auth-storage in localStorage
   ```

---

## 🚀 COMPLETE QUICK FIX (Do These Steps)

### 1. Log Out & Log Back In
```
The token might be expired. Clear everything and re-authenticate:

Browser (F12 → Console):
localStorage.clear()  // Clear all storage

Then refresh page and login again
```

### 2. Manually Set Token (If you have a fresh token)
```javascript
// In browser console (F12):
const token = "YOUR_TOKEN_HERE"; // Get from API login response
localStorage.setItem('auth-storage', JSON.stringify({
  state: {
    token: token,
    isAuthenticated: true,
    user: { email: "admin@example.com" }
  }
}));
location.reload(); // Refresh page
```

### 3. Try With Direct API Call
```javascript
// In browser console (F12):
const token = JSON.parse(localStorage.getItem('auth-storage'))?.state?.token;
fetch('http://localhost:8000/api/v1/timetable/public/6984411e61c6ef3ed8284460', {
  headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(data => {
  console.log('Timetable data:', data);
  console.log('Entries:', data.entries?.length);
})
.catch(e => console.error('Error:', e));
```

---

## 📋 DEBUGGING CHECKLIST

- [ ] **Backend Running?**
  - Open terminal: `curl http://localhost:8000/api/v1/health`
  - Should work (or return data)

- [ ] **Frontend Running?**
  - Visit: `http://localhost:5173`
  - Should load without errors

- [ ] **User Logged In?**
  - Browser F12 → Console
  - Run: `JSON.parse(localStorage.getItem('auth-storage'))?.state?.isAuthenticated`
  - Should show: `true`

- [ ] **Token in LocalStorage?**
  - Browser F12 → Console
  - Run: `localStorage.getItem('auth-storage')`
  - Should NOT be `null`

- [ ] **API Returns Data?**
  - Browser F12 → Network tab
  - Load timetable page
  - Find request to: `/api/v1/timetable/public/6984411e61c6ef3ed8284460`
  - Status should be: `200` (not 401)

- [ ] **Timetable ID Correct?**
  - Use: `6984411e61c6ef3ed8284460`
  - (This is the genetic model timetable we imported)

---

## 🧪 TEST WITH TERMINAL

### Get Valid Token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | python -m json.tool
```

Save the `access_token` from response.

### Test API With Token:
```bash
TIMETABLE_ID="6984411e61c6ef3ed8284460"
TOKEN="<paste_token_here>"

curl "http://localhost:8000/api/v1/timetable/public/$TIMETABLE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
```

### Expected Response:
```json
{
  "name": "AI Generated Timetable - 2026-02-05 12:35",
  "entries": [
    {
      "course_name": "CSE Course Year 1 - 1",
      "room_number": "Building A-205",
      "day_of_week": "Monday",
      "start_time": "08:00",
      "end_time": "09:00"
    },
    ...
  ]
}
```

---

## 📊 SUMMARY

| Item | Status | What To Do |
|------|--------|-----------|
| **Database** | ✓ Has timetable | Nothing |
| **API** | ✓ Endpoint exists | Nothing |
| **API Auth** | ❌ Requires token | **← Check frontend's token** |
| **Frontend** | ❔ Unknown | **← Run browser console commands** |
| **Frontend Token** | ❔ Unknown | **← Check localStorage** |

---

## 🎯 NEXT ACTION

1. **Open browser F12 → Console**
2. **Run this command:**
   ```javascript
   console.log(JSON.parse(localStorage.getItem('auth-storage'))?.state)
   ```
3. **Share what you see with the result**
4. If null → Log in
5. If token exists → Check Network tab for API response

This will tell us exactly what's wrong!
