# Debugging Guide: React Student Timetable

## How to Verify the Fix

### Step 1: Check Browser Console
Open DevTools (F12) and look for these logs:

#### ✅ Successful Load
```javascript
// Initial page load
📥 StudentTimetable: Starting load...
📥 StudentTimetable: Current user: [User Object]
📥 StudentTimetable: Token present: true
✅ Filter options loaded: {programs: [...], years: [...], ...}
📥 StudentTimetable: /timetable/my API returned: {department: "CS", year: 1, ...}
📥 Entries count: 6
📥 First entry sample: {
  day: "Monday",
  start_time: "09:00",
  end_time: "10:00",
  course_name: "Programming Fundamentals",
  faculty: "Dr. Smith",
  room: "101"
}
```

#### ❌ Problem Indicators
```javascript
// No entries returned
⚠️ No valid entries in initial load: {
  hasData: true,
  hasEntries: false,           // ← entries field missing/null
  isArray: false,               // ← entries is not an array
  length: 0                      // ← entry count is 0
}

// Bad response structure
⚠️ No valid entries in initial load: {
  hasData: false,               // ← No response at all
  hasEntries: false,
  isArray: false,
  length: undefined
}
```

---

## Expected UI States

### State 1: Data Loaded Successfully
**What you'll see:**
```
📌 Metadata Box (gray background):
  Department: Computer Science and Engineering - AI & ML
  Year: 1
  Semester: Odd
  Section: A

📋 Filter Controls (yellow background):
  [Department dropdown] [Year dropdown] [Semester dropdown] [Section dropdown] [Search button]

📊 Timetable Grid:
  | Day / Time    | 09:00-10:00            | 10:00-11:00 | ... |
  | Monday        | Programming Fund...    | ...         | ... |
  | Tuesday       | Data Structures        | LUNCH BREAK | ... |
  | ...           | ...                    | ...         | ... |

✅ Success Box (green background):
  ✅ Timetable loaded with 6 entries
```

**Console shows:**
```
✅ Filter options loaded: {...}
📥 Entries count: 6
📥 First entry sample: {...}
```

### State 2: No Data Available
**What you'll see:**
```
🔍 Student – My Timetable
No timetable available

📊 Timetable Grid:
  | Day / Time    | 09:00-10:00 | 10:00-11:00 | ... |
  | Monday        | (empty)     | (empty)     | ... |
  | Tuesday       | (empty)     | (empty)     | ... |
  | ...           | ...         | ...         | ... |

ℹ️ Debug Info: No Entries Loaded (orange background)
  No timetable entries available. Check browser console and response below:
  
  {
    "message": "No timetable available for selected filters",
    "timetable": null
  }
```

**Console shows:**
```
⚠️ No valid entries in initial load: {
  hasData: true,
  hasEntries: false,
  isArray: false,
  length: 0
}
```

### State 3: Filter Applied Successfully
**What you'll see:**
```
🔍 Student – My Timetable
Filtered Timetable

📌 Metadata Box:
  Department: Computer Science and Engineering - AI & ML
  Year: 2
  Semester: Even
  Section: B

📋 Filter Controls:
  [CS selected] [Year 2 selected] [Even selected] [B selected] [Search button]

📊 Timetable Grid:
  (Updates to show 3 courses for year 2, section B)

✅ Success Box:
  ✅ Timetable loaded with 3 entries
```

**Console shows:**
```
🔍 Filtering timetable with: {
  program_id: "68b5c517e73858dcb11d37e4",
  year: 2,
  semester: "Even",
  section: "B"
}
📥 Filter response: {...}
📥 Filtered entries count: 3
📥 First filtered entry sample: {...}
✅ Setting entries from filter response
```

---

## Troubleshooting Checklist

### Problem: "No timetable available" appears but console shows entries exist

**Diagnosis:**
```javascript
// You see in console:
📥 Entries count: 6
📥 First entry sample: {...}

// But UI shows:
ℹ️ Debug Info: No Entries Loaded
```

**Root Cause:**
Entry validation might be failing due to data type mismatch.

**Check:**
1. Open DevTools → Network tab
2. Look for `/api/v1/timetable/filter` or `/api/v1/timetable/my`
3. Click on the request → Response tab
4. Verify structure:
   ```json
   {
     "department": "CS",
     "year": 1,
     "entries": [        // ← Must be array
       {
         "day": "Monday",
         "start_time": "09:00",
         ...
       }
     ]
   }
   ```

**Fix:**
- If `entries` is `null` → Backend not returning entries
- If `entries` is not an array → Backend sending wrong format
- Check backend `/api/v1/timetable/filter` implementation

### Problem: Table is empty but success box shows entries

**Diagnosis:**
```javascript
✅ Timetable loaded with 6 entries

// But table is completely empty
```

**Root Cause:**
Entries might exist but `getCell()` isn't matching them to slots.

**Check:**
1. Console → In Network tab, look at response entries:
   ```json
   "entries": [
     {
       "day": "monday",      // ← Might be lowercase
       "start_time": " 09:00",  // ← Might have extra spaces
       "course_name": "..."
     }
   ]
   ```

2. Check time slot format in table:
   ```
   SLOTS = ['09:00-10:00', '10:00-11:00', ...]  // Format: "HH:MM-HH:MM"
   ```

**Fix:**
The `getCell()` function handles case-insensitive matching:
```javascript
const entryDay = (entry.day || '').toString().toLowerCase().trim();
const targetDay = day.toLowerCase().trim();
```

Should work, but if not:
- Check if `start_time` has spaces: `entry.start_time.trim()`
- Check if day format is different (e.g., "MON" vs "Monday")
- Compare exact values in console

### Problem: Filter returns 0 entries

**Diagnosis:**
```javascript
🔍 Filtering timetable with: {
  program_id: "...",
  year: 1,
  semester: "Odd",
  section: "A"
}
📥 Filtered entries count: 0
⚠️ No valid entries in filter response: {...}
```

**Root Cause:**
No student groups exist for that year/semester/section combination, OR backend has no timetable entries for that group.

**Check:**
1. In Network tab, look at filter response:
   ```json
   {
     "message": "No timetable available for selected filters",
     "timetable": null
   }
   ```

2. Backend logs should show:
   ```
   No student groups found for filters: {...}
   ```

**Fix:**
- Verify test data exists for that year/semester/section
- Backend: Run `/api/v1/timetable/options/filters` to see available options
- Select only from available options

### Problem: Wrong course appears in wrong time slot

**Diagnosis:**
```
Table shows:
| Monday, 09:00-10:00 | Data Structures (should be Programming Fundamentals) |
```

**Root Cause:**
- Entry day name format mismatch
- Entry start_time has extra spaces/formatting
- Multiple entries match same slot (getCell() returns first match)

**Check:**
1. Console → Add temporary log in `getCell()`:
   ```javascript
   const getCell = (day, slot) => {
     const slotStart = slot.split('-')[0].trim(); // "09:00"
     console.log(`Looking for: day="${day}" (${day.toLowerCase()}), time="${slotStart}"`);
     
     const matches = entries.filter((entry: any) => {
       const entryDay = (entry.day || '').toString().toLowerCase().trim();
       const entStart = (entry.start_time || entry.start || '').toString().trim();
       const match = entryDay === day.toLowerCase() && entStart === slotStart;
       console.log(`  Entry: day="${entry.day}" → "${entryDay}", time="${entry.start_time}" → "${entStart}" = ${match}`);
       return match;
     });
     // ...
   }
   ```

2. Open console and look for log pattern:
   ```
   Looking for: day="Monday" (monday), time="09:00"
     Entry: day="monday" → "monday", time="09:00" → "09:00" = true ✓
     Entry: day="Monday" → "monday", time="09:00" → "09:00" = true ✓  ← Duplicate!
   ```

**Fix:**
- If multiple entries match, backend data might be corrupted (duplicate entries)
- Or entries belong to different student groups (use group_id to filter)

---

## Quick Reference: Console Commands

### Check current state
```javascript
// In browser console
// Get entries currently loaded
JSON.stringify(document.querySelector('[data-testid="timetable-entries"]')?.innerText || 'Not found')

// Or check React component state (if using React DevTools)
$r.state.entries  // Shows loaded entries
```

### Inspect API response manually
```javascript
// In browser console
fetch('http://localhost:8000/api/v1/timetable/my', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token')  // If using localStorage
  }
}).then(r => r.json()).then(data => {
  console.log('Response:', data);
  console.log('Entries count:', data?.entries?.length || 0);
  console.log('First entry:', data?.entries?.[0]);
})
```

### Test time matching
```javascript
// In browser console
const SLOTS = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '01:00-02:00'];
const entry = { day: 'Monday', start_time: '09:00', course_name: 'Test' };

// Check if entry matches first slot on Monday
const slot = SLOTS[0];  // "09:00-10:00"
const slotStart = slot.split('-')[0].trim();  // "09:00"
const match = entry.day.toLowerCase() === 'Monday'.toLowerCase() && entry.start_time === slotStart;
console.log(`Entry matches slot? ${match}`);
```

---

## Getting Help

If you see errors you don't understand:

1. **Screenshot the console output**
   - F12 → Console tab
   - Copy all error messages

2. **Check Network tab**
   - F12 → Network tab
   - Filter for `/api/v1/timetable`
   - Click on request → Response tab
   - Verify JSON structure

3. **Check backend logs**
   - Backend terminal should show:
     ```
     Timetable query: {...}
     Found X matching student groups
     Total entries in timetable: Y
     Returning Y entries to client
     ```

4. **Provide**:
   - Browser console screenshot
   - Network response JSON
   - Backend console logs
   - What you expected vs what you see
