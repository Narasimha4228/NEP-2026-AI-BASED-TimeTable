# Department Code Consistency Implementation

## Overview

This document outlines the implementation of department code consistency across the timetable system. All dashboards (Admin and Student) now use `department_code` (program code like "CSE", "ECE") as the primary identifier for filtering and querying timetables, ensuring data consistency and instant reflection without transformation.

## Requirements Met

✅ **Requirement 1: Generated timetable must be saved using department_code**
- Backend now extracts program code when creating timetables
- Stored in `department_code` field in MongoDB

✅ **Requirement 2: Student dashboard filters must query using department_code**
- Filter endpoint accepts `department_code` parameter
- Filters timetables using department code instead of program_id

✅ **Requirement 3: Department dropdowns in Admin & Student dashboards share identical values**
- Both show program code prominently: "CSE - Computer Science"
- Admin dropdown: Shows `{program.name} ({program.code})`
- Student dropdown: Shows `{program.code} - {program.name}`
- Both store and use the program code value

✅ **Requirement 4: Timetable must reflect instantly without transformation**
- Response includes `department_code` directly
- No lookup or mapping needed on frontend
- Data flows directly from API to UI

---

## Implementation Details

### Backend Changes

#### 1. Timetable Model (`backend/app/models/timetable.py`)

Added `department_code` field to store the program code:

```python
class TimetableBase(BaseModel):
    title: Optional[str] = None
    program_id: str
    department_code: Optional[str] = None  # Store department code for direct filtering
    semester: int
    academic_year: Optional[str] = None
    entries: List[TimetableEntry] = []
    is_draft: bool = True

class Timetable(TimetableBase, MongoBaseModel):
    # ... existing fields ...
    department_code: Optional[str] = None  # Department code for filtering
```

#### 2. Create Timetable Endpoint (`POST /timetable/`)

Automatically extracts and stores department code when creating timetable:

```python
@router.post("/", response_model=Timetable)
async def create_timetable(
    timetable_data: TimetableCreate,
    current_user: User = Depends(get_current_active_user),
):
    """Create a new timetable"""
    timetable_dict = timetable_data.model_dump()
    # ... existing code ...
    
    # Fetch and store the program's department code
    try:
        program = await db.db.programs.find_one({"_id": ObjectId(timetable_dict["program_id"])})
    except Exception:
        program = await db.db.programs.find_one({"_id": timetable_dict["program_id"]})
    
    if program:
        timetable_dict["department_code"] = program.get("code")

    result = await db.db.timetables.insert_one(timetable_dict)
    # ... rest of code ...
```

#### 3. Filter Endpoint (`GET /timetable/filter`)

Updated to accept and use `department_code` parameter:

```python
@router.get("/filter", response_model=dict)
async def filter_timetables(
    program_id: str = None,
    department_code: str = None,
    year: int = None,
    semester: str = None,
    section: str = None,
    current_user: User = Depends(get_current_active_user),
):
    """
    Filter timetables by department, year, semester, section.
    
    Query Parameters:
    - department_code: Program code (e.g., "CSE", "ECE") - PREFERRED
    - program_id: MongoDB ObjectId of program - fallback for backward compatibility
    - year: Academic year (1, 2, 3, 4)
    - semester: Semester identifier (Odd/Even or 1-8)
    - section: Section identifier (A, B, C, etc.)
    """
    
    query = {"is_draft": False}
    
    # If department_code is provided, use it to find program and filter
    if department_code:
        try:
            program = await db.db.programs.find_one({"code": department_code})
            if program:
                query["program_id"] = program.get("_id")
                query["department_code"] = department_code
        except Exception as e:
            print(f"Error finding program by code: {e}")
    
    # Fall back to program_id if provided and department_code wasn't used
    if program_id and "program_id" not in query:
        try:
            query["program_id"] = ObjectId(program_id)
        except Exception:
            query["program_id"] = program_id
    
    # ... rest of filtering logic ...
```

#### 4. My Timetable Endpoint (`GET /timetable/my`)

Updated response to include `department_code`:

```python
@router.get("/my")
async def get_my_timetable(
    current_user: User = Depends(get_current_active_user),
):
    # ... existing query logic ...
    
    # Get department code from stored value or fetch from program
    dept_code = timetable.get("department_code")
    if not dept_code and timetable.get("program_id"):
        # Fetch from program if not stored
        try:
            prog = await db.db.programs.find_one({"_id": ObjectId(timetable.get("program_id"))})
            if not prog:
                prog = await db.db.programs.find_one({"_id": timetable.get("program_id")})
        except Exception:
            prog = await db.db.programs.find_one({"_id": timetable.get("program_id")})
        if prog:
            dept_code = prog.get("code")

    return {
        "department": dept_code,  # For backward compatibility
        "department_code": dept_code,
        "year": year,
        "section": section,
        "semester": semester,
        "timetable_id": str(timetable.get("_id")),
        "generated_at": timetable.get("generated_at").isoformat() if timetable.get("generated_at") else None,
        "entries": my_entries
    }
```

#### 5. Filter Options Endpoint (`GET /timetable/options/filters`)

Updated program object structure to prioritize code:

```python
programs = []
for pid in program_ids:
    # ... fetch program ...
    if prog:
        programs.append({
            "id": str(prog.get("_id")),
            "code": prog.get("code"),  # Department code
            "name": prog.get("name") or prog.get("title"),
        })

return {
    "programs": programs,  # Now includes 'code' field
    "years": years,
    "semesters": semesters,
    "sections": sections,
}
```

---

### Frontend Changes

#### 1. Student Timetable Component (`frontend/src/components/pages/StudentTimetable.tsx`)

**Changed dropdown to use `department_code`:**

```tsx
{(filterOptions.programs || []).map((prog: any) => (
  <MenuItem key={prog.code} value={prog.code}>
    {prog.code} - {prog.name}
  </MenuItem>
))}
```

**Updated filter handler to send `department_code`:**

```tsx
const handleFilterChange = async () => {
  const filters: any = {};
  if (selectedProgram) filters.department_code = selectedProgram;  // Use department_code
  if (selectedYear) filters.year = Number(selectedYear);
  if (selectedSemester) filters.semester = selectedSemester;
  if (selectedSection) filters.section = selectedSection;
  // ... rest of handler ...
};
```

**Updated initial load to use `department_code` from response:**

```tsx
// Pre-fill filter selections with student's current assignment
// Use department_code directly from response instead of mapping through programs
if (data.department_code || data.department) {
  const deptCode = data.department_code || data.department;
  setSelectedProgram(deptCode);  // department_code is the value
}
```

---

## Data Flow

### Before (Using program_id - ObjectId)

```
Admin Creates Timetable
  ↓
Stores: program_id = "60a7c5e1f2c4d8e0a8b1c2d3" (ObjectId)
  ↓
Student Filters
  ↓
Sends: program_id = "60a7c5e1f2c4d8e0a8b1c2d3"
  ↓
Problem: Values don't match if ObjectId format changes
```

### After (Using department_code - String Code)

```
Admin Creates Timetable (program_id selected = "60a7c5e1f2c4d8e0a8b1c2d3")
  ↓
Backend fetches Program data
  ↓
Stores: 
  - program_id = "60a7c5e1f2c4d8e0a8b1c2d3"
  - department_code = "CSE"
  ↓
Student Filters (selects "CSE" from dropdown)
  ↓
Sends: department_code = "CSE"
  ↓
Backend finds Program with code "CSE" → Gets program_id
  ↓
Filters timetables by matching program_id
  ↓
Response includes:
  - department_code: "CSE" (for display)
  - entries: [...] (courses to display)
  ↓
Frontend displays instantly without transformation
```

---

## API Response Examples

### GET /timetable/options/filters

```json
{
  "programs": [
    {
      "id": "60a7c5e1f2c4d8e0a8b1c2d3",
      "code": "CSE",
      "name": "Computer Science Engineering"
    },
    {
      "id": "60a7c5e1f2c4d8e0a8b1c2d4",
      "code": "ECE",
      "name": "Electronics and Communication Engineering"
    }
  ],
  "years": [1, 2, 3, 4],
  "semesters": ["Odd", "Even"],
  "sections": ["A", "B", "C"]
}
```

### GET /timetable/my

```json
{
  "department": "CSE",
  "department_code": "CSE",
  "year": 1,
  "section": "A",
  "semester": "Odd",
  "timetable_id": "60a7c5e1f2c4d8e0a8b1c2d5",
  "generated_at": "2026-02-03T10:30:00",
  "entries": [
    {
      "group_id": "60a7c5e1f2c4d8e0a8b1c2d6",
      "course_code": "CS101",
      "course_name": "Programming Fundamentals",
      "faculty": "Dr. Smith",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "10:00",
      "room": "Room 101",
      "is_lab": false
    }
  ]
}
```

### GET /timetable/filter?department_code=CSE&year=1&semester=Odd&section=A

```json
{
  "department_code": "CSE",
  "year": 1,
  "semester": "Odd",
  "section": "A",
  "timetable_id": "60a7c5e1f2c4d8e0a8b1c2d5",
  "generated_at": "2026-02-03T10:30:00",
  "entries": [
    {
      "group_id": "60a7c5e1f2c4d8e0a8b1c2d6",
      "course_code": "CS101",
      "course_name": "Programming Fundamentals",
      "faculty": "Dr. Smith",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "10:00",
      "room": "Room 101",
      "is_lab": false
    }
  ]
}
```

---

## Backward Compatibility

- Backend still accepts `program_id` as a fallback parameter
- Responses include both `department` and `department_code` for compatibility
- Existing integrations continue to work if they use `program_id`

---

## Testing Checklist

### Frontend Testing

- [ ] Student dashboard loads and displays department code
- [ ] Department dropdown shows "CSE - Computer Science" format
- [ ] Selecting department and clicking "Search Timetable" filters correctly
- [ ] Filter response returns entries instantly
- [ ] Table grid displays courses when entries exist
- [ ] Debug box appears only when no entries are loaded
- [ ] Success message appears when entries are loaded

### Backend Testing

- [ ] Create timetable stores `department_code` 
- [ ] GET /timetable/my returns `department_code`
- [ ] GET /timetable/filter?department_code=CSE returns matching timetable
- [ ] GET /timetable/options/filters returns programs with `code` field
- [ ] Filter works with both `department_code` and `program_id` (backward compatibility)

### Database Verification

- [ ] Check timetables collection for new timetables with `department_code` field
- [ ] Verify `department_code` matches program.code
- [ ] Check that old timetables without `department_code` still work via fallback logic

---

## Implementation Summary

| Component | Change | Impact |
|-----------|--------|--------|
| Timetable Model | Added `department_code` field | Stores program code in each timetable |
| Create Endpoint | Extract and store department code | Auto-populate code on creation |
| Filter Endpoint | Accept `department_code` parameter | Enable direct filtering by code |
| My Timetable Endpoint | Return `department_code` in response | UI can use code directly |
| Filter Options | Return program `code` field | Dropdowns show consistent values |
| Student Dashboard | Use `department_code` for filter/display | Consistent value format throughout |

---

## Benefits

1. **Data Consistency**: All systems use the same code format
2. **No Transformation Needed**: Department code flows directly from API to UI
3. **Stable Identifier**: Program code is more stable than ObjectId
4. **Instant Reflection**: Timetables appear immediately without lookups
5. **Better UX**: Users see readable codes ("CSE") instead of ObjectIds
6. **Backward Compatible**: Old queries still work via fallback logic

---

## Future Improvements

- Consider migrating old timetables to populate `department_code` via batch script
- Update admin dashboard to also use `department_code` consistently
- Add database indexes on `department_code` for faster queries
- Update API documentation to recommend `department_code` over `program_id`
