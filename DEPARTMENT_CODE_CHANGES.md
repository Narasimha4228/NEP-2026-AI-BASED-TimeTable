# Department Code Consistency - Changes Summary

## What Was Changed

This implementation ensures that all timetable operations use `department_code` (program code like "CSE", "ECE") consistently across the system, eliminating the need for data transformation and enabling instant timetable reflection.

---

## Files Modified

### Backend

#### 1. `backend/app/models/timetable.py`
**Changes:**
- Added `department_code: Optional[str]` field to `TimetableBase` class
- Added `department_code: Optional[str]` field to `Timetable` class

**Purpose:** Store program code directly in timetable documents for direct filtering

---

#### 2. `backend/app/api/v1/endpoints/timetable.py`

**Change 1: CREATE TIMETABLE ENDPOINT (Lines 369-391)**
- Fetches program document when creating timetable
- Extracts program's `code` field
- Stores it as `department_code` in timetable document

**Code:**
```python
# Fetch and store the program's department code
try:
    program = await db.db.programs.find_one({"_id": ObjectId(timetable_dict["program_id"])})
except Exception:
    program = await db.db.programs.find_one({"_id": timetable_dict["program_id"]})

if program:
    timetable_dict["department_code"] = program.get("code")
```

**Change 2: FILTER TIMETABLES ENDPOINT (Lines 223-348)**
- Updated to accept both `program_id` and `department_code` parameters
- Prefers `department_code` when provided
- Falls back to `program_id` for backward compatibility
- Returns `department_code` in response instead of `department`

**Key improvements:**
- Direct query by department code (e.g., "CSE")
- Looks up program_id from program code for filtering
- Returns department_code in response for frontend use

**Change 3: MY TIMETABLE ENDPOINT (Lines 161-195)**
- Returns both `department` and `department_code` fields
- Extracts department code from stored value or fetches from program
- Ensures backward compatibility while providing new field

**Change 4: FILTER OPTIONS ENDPOINT (Lines 87-106)**
- Returns `code` field in program objects
- Updated order to prioritize `code` in response

---

### Frontend

#### 3. `frontend/src/components/pages/StudentTimetable.tsx`

**Change 1: Department Dropdown Display (Line 332)**
```tsx
// OLD:
{(filterOptions.programs || []).map((prog: any) => (
  <MenuItem key={prog.id} value={prog.id}>
    {prog.code} - {prog.name}
  </MenuItem>
))}

// NEW:
{(filterOptions.programs || []).map((prog: any) => (
  <MenuItem key={prog.code} value={prog.code}>
    {prog.code} - {prog.name}
  </MenuItem>
))}
```
**Impact:** Uses department code as the value instead of MongoDB ObjectId

**Change 2: Filter Handler (Line 140)**
```tsx
// OLD:
if (selectedProgram) filters.program_id = selectedProgram;

// NEW:
if (selectedProgram) filters.department_code = selectedProgram;  // Use department_code
```
**Impact:** Sends department code in API request instead of program_id

**Change 3: Initial Load Pre-fill (Lines 104-106)**
```tsx
// OLD:
if (data.department) {
  const prog = filterOptions.programs?.find((p: any) => p.code === data.department);
  if (prog) setSelectedProgram(prog.id);
}

// NEW:
if (data.department_code || data.department) {
  const deptCode = data.department_code || data.department;
  setSelectedProgram(deptCode);  // department_code is the value
}
```
**Impact:** Uses department_code directly from API response without mapping

---

## Data Flow Changes

### Old Flow (Program ID Based)
```
API Response:
  department: "CSE" (actual code)
  ↓
Frontend tries to map to program.id using p.code === "CSE"
  ↓
Filter sends program.id (ObjectId) to backend
  ↓
Potential mismatch if format changes
```

### New Flow (Department Code Based)
```
API Response:
  department_code: "CSE"
  ↓
Frontend uses department_code directly
  ↓
Filter sends department_code: "CSE" to backend
  ↓
Backend looks up program.code = "CSE" → gets program_id → filters
  ↓
No transformation needed, instant results
```

---

## API Contract Changes

### GET /timetable/options/filters

**Program Object (Updated):**
```json
{
  "id": "60a7c5e1f2c4d8e0a8b1c2d3",
  "code": "CSE",
  "name": "Computer Science Engineering"
}
```
*`code` field is now prominently returned*

---

### GET /timetable/filter

**New Query Parameters:**
- `department_code` (NEW, PREFERRED): Program code like "CSE"
- `program_id` (OLD, SUPPORTED): MongoDB ObjectId for backward compatibility

**Example Requests:**
```bash
# NEW (Recommended)
GET /api/v1/timetable/filter?department_code=CSE&year=1&semester=Odd&section=A

# OLD (Still Works)
GET /api/v1/timetable/filter?program_id=60a7c5e1f2c4d8e0a8b1c2d3&year=1&semester=Odd&section=A
```

**Response Changes:**
```json
{
  "department_code": "CSE",      // NEW field
  "year": 1,
  "semester": "Odd",
  "section": "A",
  "timetable_id": "...",
  "entries": [...]
}
```

---

### GET /timetable/my

**Response Changes:**
```json
{
  "department": "CSE",             // Kept for compatibility
  "department_code": "CSE",        // NEW field
  "year": 1,
  "section": "A",
  "semester": "Odd",
  "timetable_id": "...",
  "entries": [...]
}
```

---

## Database Schema Changes

### New Timetables
```javascript
{
  _id: ObjectId("..."),
  title: "CSE Year 1 Timetable",
  program_id: ObjectId("60a7c5e1f2c4d8e0a8b1c2d3"),
  department_code: "CSE",              // NEW FIELD
  semester: 1,
  academic_year: "2025-2026",
  is_draft: false,
  entries: [...],
  created_by: ObjectId("..."),
  created_at: ISODate("2026-02-03T10:00:00Z"),
  generated_at: ISODate("2026-02-03T10:30:00Z")
}
```

### Old Timetables (Still Work)
```javascript
{
  _id: ObjectId("..."),
  title: "CSE Year 1 Timetable",
  program_id: ObjectId("60a7c5e1f2c4d8e0a8b1c2d3"),
  // department_code field missing - will be fetched from program on demand
  semester: 1,
  academic_year: "2025-2026",
  is_draft: false,
  entries: [...]
}
```

**Backward Compatibility:**
- Old timetables without `department_code` still work
- Backend fetches department_code from Program document on demand
- Frontend receives `department_code` in response regardless

---

## Benefit Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Filter Identifier** | `program_id` (ObjectId) | `department_code` (String code) |
| **Data Stability** | Object IDs can change | Codes are stable |
| **Transformation** | Frontend maps code to ID | Direct code usage |
| **Display** | Requires lookup | Instant, no lookup |
| **User Experience** | ObjectIds in URLs | Readable codes in UI |
| **Query Speed** | ObjectId comparison | String comparison (faster) |
| **Backward Compat** | N/A | Full support via fallback |

---

## Testing Quick Links

- See `TESTING_DEPARTMENT_CODE.md` for complete test scenarios
- See `DEPARTMENT_CODE_CONSISTENCY.md` for technical details

---

## Deployment Checklist

- [ ] Deploy backend changes
- [ ] Restart API server
- [ ] Deploy frontend changes
- [ ] Clear browser cache
- [ ] Test all scenarios in `TESTING_DEPARTMENT_CODE.md`
- [ ] Monitor logs for any errors
- [ ] Verify database has new timetables with `department_code`

---

## Rollback Plan

If critical issues arise:

1. **Frontend Rollback**: Change StudentTimetable.tsx line 140 back to `filters.program_id = selectedProgram`
2. **Backend Rollback**: Not needed - endpoint accepts both parameters
3. **Verification**: Test that filter still works with `program_id`

---

## Questions & Answers

**Q: Will old timetables stop working?**
A: No. Backend automatically fetches department_code from program data if not stored.

**Q: Do I need to update existing timetables?**
A: No. They work as-is. New ones automatically get the department_code field.

**Q: Why not just use ObjectId?**
A: ObjectIds can change, codes are stable. Codes are also human-readable.

**Q: Can I still use program_id in API calls?**
A: Yes, the filter endpoint accepts both `program_id` and `department_code` for backward compatibility.

**Q: Does this affect the Admin dashboard?**
A: Admin still uses program_id for selection (unchanged), but backend now stores both fields.

---

## Monitoring

Watch for these in logs after deployment:

**Good Signs:**
```
Found program by code: CSE
Timetable query: {'is_draft': False, 'program_id': ObjectId(...), 'department_code': 'CSE'}
Found timetable: 60a7c5e1f2c4d8e0a8b1c2d5
Returning 12 entries to client
```

**Issues to Investigate:**
```
Error finding program by code: [error message]
No student groups found for filters: [metadata]
No timetable found for query: [query]
```

---

## Success Criteria

✅ All new timetables store `department_code`
✅ Student dashboard filters return entries instantly
✅ Department dropdown shows program code prominently
✅ No transformation needed on frontend
✅ Old timetables still accessible (backward compatible)
✅ Browser console shows expected log messages
✅ All tests in TESTING_DEPARTMENT_CODE.md pass
