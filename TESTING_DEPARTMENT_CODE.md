# Testing Guide: Department Code Consistency

## Quick Test Scenarios

### Scenario 1: Student Dashboard Initial Load

**Steps:**
1. Navigate to Student Timetable page
2. Observe page loads with "My Timetable"

**Expected Results:**
- ✅ Department field shows program code (e.g., "CSE")
- ✅ Filter dropdown shows "CSE - Computer Science Engineering"
- ✅ Filter field is pre-filled with "CSE"
- ✅ Table shows timetable entries if student has assigned group

**Browser Console Check:**
```
📥 StudentTimetable: /timetable/my API returned: {
  department_code: "CSE",
  department: "CSE",
  year: 1,
  section: "A",
  semester: "Odd",
  entries: [...]
}
```

---

### Scenario 2: Filter by Department Code

**Steps:**
1. Go to Student Timetable page
2. Click "Select a Different Timetable" section
3. Select a different department from dropdown (e.g., "ECE - Electronics and Communication Engineering")
4. Click "🔍 Search Timetable"

**Expected Results:**
- ✅ Filter request sent with `department_code: "ECE"`
- ✅ API returns timetable for ECE department
- ✅ Table updates instantly with new courses
- ✅ Department metadata section shows "ECE"
- ✅ No errors in console

**Browser Console Check:**
```
🔍 Filtering timetable with: {
  department_code: "ECE",
  year: 1,
  semester: "Odd",
  section: "A"
}

✅ Setting entries from filter response
Returning 12 entries to client
```

---

### Scenario 3: No Entries Scenario

**Steps:**
1. Filter for a department/year/semester/section combination with no timetable
2. Observe response

**Expected Results:**
- ✅ Table remains empty
- ✅ Debug info box appears showing "No Entries Loaded"
- ✅ Console shows filtering attempt
- ✅ Response structure visible in debug box

---

### Scenario 4: Admin Creates Timetable

**Steps:**
1. Go to Admin > Create Timetable
2. Select Program: "Computer Science Engineering (CSE)"
3. Fill remaining fields
4. Save timetable

**Expected Results:**
- ✅ Timetable created successfully
- ✅ Backend stores both `program_id` and `department_code`
- ✅ Database entry contains `department_code: "CSE"`

**Verification:**
Check MongoDB:
```javascript
db.timetables.findOne({}, {program_id: 1, department_code: 1})
// Should show:
// {
//   _id: ObjectId("..."),
//   program_id: ObjectId("..."),
//   department_code: "CSE"
// }
```

---

## Backend API Testing

### Test 1: Get Filter Options

**Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/timetable/options/filters
```

**Expected Response:**
```json
{
  "programs": [
    {
      "id": "60a7c5e1f2c4d8e0a8b1c2d3",
      "code": "CSE",
      "name": "Computer Science Engineering"
    }
  ],
  "years": [1, 2, 3, 4],
  "semesters": ["Odd", "Even"],
  "sections": ["A", "B", "C"]
}
```

---

### Test 2: Filter by Department Code

**Request (Preferred - Using department_code):**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/timetable/filter?department_code=CSE&year=1&semester=Odd&section=A"
```

**Expected Response:**
```json
{
  "department_code": "CSE",
  "year": 1,
  "semester": "Odd",
  "section": "A",
  "timetable_id": "60a7c5e1f2c4d8e0a8b1c2d5",
  "entries": [
    {
      "group_id": "...",
      "course_code": "CS101",
      "course_name": "Programming Fundamentals",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "10:00",
      "faculty": "Dr. Smith",
      "room": "Room 101"
    }
  ]
}
```

---

### Test 3: Backward Compatibility (Using program_id)

**Request (Old format - Should still work):**
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/timetable/filter?program_id=60a7c5e1f2c4d8e0a8b1c2d3&year=1&semester=Odd&section=A"
```

**Expected Response:**
- ✅ Returns same timetable as Test 2
- ✅ Confirms backward compatibility

---

### Test 4: Get My Timetable

**Request:**
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/timetable/my
```

**Expected Response:**
```json
{
  "department": "CSE",
  "department_code": "CSE",
  "year": 1,
  "section": "A",
  "semester": "Odd",
  "timetable_id": "...",
  "generated_at": "2026-02-03T10:30:00",
  "entries": [...]
}
```

---

## Database Verification

### Check New Timetables Have department_code

```javascript
// Connect to MongoDB
db.timetables.aggregate([
  {$match: {is_draft: false}},
  {$group: {
    _id: null,
    with_dept_code: {$sum: {$cond: ["$department_code", 1, 0]}},
    without_dept_code: {$sum: {$cond: ["$department_code", 0, 1]}},
    total: {$sum: 1}
  }}
])

// Sample result should show:
// {
//   _id: null,
//   with_dept_code: 5,
//   without_dept_code: 3,  // Old timetables
//   total: 8
// }
```

### Check Specific Timetable

```javascript
db.timetables.findOne(
  {is_draft: false},
  {program_id: 1, department_code: 1, title: 1}
)

// Should return:
// {
//   _id: ObjectId("..."),
//   title: "CSE Year 1 Timetable",
//   program_id: ObjectId("60a7c5e1f2c4d8e0a8b1c2d3"),
//   department_code: "CSE"
// }
```

---

## Console Logs to Verify

### Student Dashboard Load

Look for these in browser DevTools Console:

```
✅ Filter options loaded: {programs: Array(4), years: Array(4), ...}
📥 StudentTimetable: /timetable/my API returned: {department_code: "CSE", ...}
📥 Entries count: 12
✅ Setting entries from filter response
```

### After Filter

```
🔍 Filtering timetable with: {department_code: "CSE", year: 1, semester: "Odd", section: "A"}
📥 Filter response: {department_code: "CSE", entries: Array(12), ...}
📥 Filtered entries count: 12
✅ Setting entries from filter response
✅ Timetable loaded with 12 entries
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "No timetable available" appears | No timetable for selected filters | Check backend logs for matching student groups |
| Department shows ObjectId | Old response format | Backend update may not be deployed |
| Filter dropdown empty | No programs with published timetables | Create and publish a timetable first |
| Entries don't update | Frontend not refreshing | Check that `department_code` is being sent in filter request |

---

## Rollback Instructions (If Needed)

If the department_code implementation causes issues:

1. Revert StudentTimetable.tsx to use `program_id` instead of `department_code`
2. Backend still accepts both, so filter endpoint will continue working
3. Update filter handler:
   ```tsx
   if (selectedProgram) filters.program_id = selectedProgram;  // Revert to program_id
   ```

---

## Sign-Off Checklist

- [ ] Student dashboard loads timetable with department code
- [ ] Filter by department code works correctly
- [ ] Timetable entries display instantly
- [ ] Admin can create timetables
- [ ] New timetables store department_code in database
- [ ] Old timetables still work (backward compatibility)
- [ ] All console logs show expected values
- [ ] No JavaScript errors in browser console
