# Department Code Consistency - Visual Reference Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEP Timetable System                          │
└─────────────────────────────────────────────────────────────────┘

┌───────────────────┐              ┌──────────────────┐
│  ADMIN DASHBOARD  │              │ STUDENT DASHBOARD │
│  Create Timetable │              │   View Timetable  │
└────────┬──────────┘              └────────┬─────────┘
         │                                  │
         ├─ Select Program (by ID)         ├─ Select Department (by CODE) ✨
         │  "CSE - CS Engineering"         │  "CSE - CS Engineering"
         │                                 │
         ├─ Store: program_id              ├─ Send: department_code ✨
         │         + department_code ✨   │
         │                                 │
         └─────────────┬────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │    BACKEND API              │
         │                             │
         │  POST /timetable/           │
         │  ├─ Extract dept code ✨   │
         │  └─ Store both fields ✨   │
         │                             │
         │  GET /timetable/filter      │
         │  ├─ Accept dept_code ✨    │
         │  ├─ Look up program_id      │
         │  └─ Return dept_code ✨    │
         │                             │
         │  GET /timetable/my          │
         │  └─ Return dept_code ✨    │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌──────────────────────────┐
         │   MONGODB DATABASE       │
         │                          │
         │  Timetables:             │
         │  ├─ program_id: ObjId    │
         │  ├─ dept_code: "CSE" ✨ │
         │  └─ entries: [...]       │
         │                          │
         │  Programs:               │
         │  ├─ code: "CSE"          │
         │  └─ name: "CS Eng"       │
         └──────────────────────────┘

✨ = New/Updated for consistency
```

---

## Data Flow Diagram

### Before Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│ STUDENT FILTERS BY DEPARTMENT                                   │
└─────────────────────────────────────────────────────────────────┘

User Interface:
  Department: [CSE - Computer Science Engineering ▼]  ← Shows code
                                                  │
                                                  ▼
              Frontend Gets: prog.id = ObjectId(...)
                                                  │
                                                  ▼
              Sends to Backend: 
              /filter?program_id=ObjectId(...) ✗ Problem!
                                                  │
                                                  ▼
              Backend matches timetable by ObjectId
                                                  │
                                                  ▼
              Response: department: "CSE"
                                                  │
                                                  ▼
              Frontend must map "CSE" back to:
              filterOptions.programs.find(p => p.code === "CSE")
              ↓
              To get the ObjectId again for next filter
              
⚠️ Issue: Circular mapping, potential mismatch, extra lookups
```

### After Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│ STUDENT FILTERS BY DEPARTMENT                                   │
└─────────────────────────────────────────────────────────────────┘

User Interface:
  Department: [CSE - Computer Science Engineering ▼]  ← Shows code
                                                  │
                                                  ▼
              Frontend Gets: "CSE" directly ✨ (department_code)
                                                  │
                                                  ▼
              Sends to Backend: 
              /filter?department_code=CSE ✅ Direct!
                                                  │
                                                  ▼
              Backend:
              1. Looks up Program where code = "CSE"
              2. Gets program_id = ObjectId(...)
              3. Queries timetables by program_id
                                                  │
                                                  ▼
              Response: department_code: "CSE" ✨
                                                  │
                                                  ▼
              Frontend displays "CSE" directly ✅
              No mapping needed!
              
✅ Benefits: Direct flow, no circular lookups, instant display
```

---

## Component Interaction Diagram

```
                    ┌──────────────────────────┐
                    │  StudentTimetable.tsx    │
                    │                          │
                    │  state: selectedProgram  │
                    │         = "CSE" ✨      │
                    └────────────┬─────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
         ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
         │ Dropdown    │  │ Filter      │  │ Table Grid   │
         │ Component   │  │ Handler     │  │ Component    │
         │             │  │             │  │              │
         │ Shows:      │  │ Sends:      │  │ Displays:    │
         │"CSE - CS Eng"│  │ dept_code   │  │ Courses      │
         │ Stores:     │  │ = "CSE"     │  │              │
         │ "CSE" ✨   │  │ to API      │  │ From:        │
         └─────────────┘  └──────┬──────┘  │ response.    │
                                 │         │ entries ✨  │
                                 ▼         └──────────────┘
                    ┌──────────────────────────┐
                    │  timetableService        │
                    │                          │
                    │  filterTimetables(       │
                    │    {                     │
                    │      department_code ✨ │
                    │    }                     │
                    │  )                       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  FastAPI Backend         │
                    │  GET /timetable/filter   │
                    │                          │
                    │  @router.get("/filter")  │
                    │  async def filter_      │
                    │  timetables(             │
                    │    department_code ✨,  │
                    │    year, semester, ...   │
                    │  )                       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  MongoDB Driver          │
                    │  (Motor)                 │
                    │                          │
                    │  1. Find Program by code │
                    │  2. Get program_id       │
                    │  3. Query timetables     │
                    │  4. Return entries ✨  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  MongoDB Collections     │
                    │                          │
                    │  programs:               │
                    │    {code: "CSE", ...}    │
                    │                          │
                    │  timetables:             │
                    │    {program_id: X,       │
                    │     department_code:     │
                    │     "CSE", ✨           │
                    │     entries: [...]}      │
                    └──────────────────────────┘
```

---

## Database Schema Update

```
BEFORE IMPLEMENTATION:
┌────────────────────────────────────────────┐
│ timetables collection                      │
├────────────────────────────────────────────┤
│ {                                          │
│   "_id": ObjectId("..."),                  │
│   "title": "CSE Year 1",                   │
│   "program_id": ObjectId("60a7c5e1..."),  │
│   "semester": 1,                           │
│   "is_draft": false,                       │
│   "entries": [...]                         │
│ }                                          │
└────────────────────────────────────────────┘
   ⚠️ No department_code field
      Must fetch from programs collection


AFTER IMPLEMENTATION:
┌────────────────────────────────────────────┐
│ timetables collection                      │
├────────────────────────────────────────────┤
│ {                                          │
│   "_id": ObjectId("..."),                  │
│   "title": "CSE Year 1",                   │
│   "program_id": ObjectId("60a7c5e1..."),  │
│   "department_code": "CSE", ✨            │
│   "semester": 1,                           │
│   "is_draft": false,                       │
│   "entries": [...]                         │
│ }                                          │
└────────────────────────────────────────────┘
   ✅ Has department_code field
      Direct access, no lookup needed
```

---

## Request/Response Flow

### Old Flow

```
FRONTEND REQUEST:
GET /api/v1/timetable/filter
?program_id=60a7c5e1f2c4d8e0a8b1c2d3
&year=1&semester=Odd&section=A

        │
        ▼

BACKEND PROCESSING:
1. Receive program_id (ObjectId)
2. Query: {program_id: ObjectId(...), is_draft: false}
3. Find timetable
4. Fetch program to get code for display
5. Build response

        │
        ▼

BACKEND RESPONSE:
{
  "department": "CSE",
  "year": 1,
  "semester": "Odd",
  "section": "A",
  "entries": [...]
}

        │
        ▼

FRONTEND PROCESSING:
1. Receive department: "CSE"
2. Find: filterOptions.programs.find(p => p.code === "CSE")
3. Get: prog.id (ObjectId)
4. Store: selectedProgram = ObjectId
5. Display: "CSE - CS Engineering"

⚠️ Extra lookups and mappings
```

### New Flow

```
FRONTEND REQUEST:
GET /api/v1/timetable/filter
?department_code=CSE ✨
&year=1&semester=Odd&section=A

        │
        ▼

BACKEND PROCESSING:
1. Receive department_code: "CSE"
2. Find Program where code = "CSE"
3. Get program_id from Program
4. Query: {program_id: ObjectId(...), is_draft: false}
5. Find timetable (already has department_code)
6. Build response with department_code

        │
        ▼

BACKEND RESPONSE:
{
  "department_code": "CSE", ✨
  "year": 1,
  "semester": "Odd",
  "section": "A",
  "entries": [...]
}

        │
        ▼

FRONTEND PROCESSING:
1. Receive department_code: "CSE"
2. Store: selectedProgram = "CSE" ✨
3. Display: "CSE - CS Engineering"

✅ Direct flow, no extra lookups
```

---

## State Management

### Student Dashboard State

```
BEFORE:
┌────────────────────────────────────────────┐
│ StudentTimetable Component State           │
├────────────────────────────────────────────┤
│ selectedProgram = "60a7c5e1f2c4d8e0..." │
│                   (ObjectId string)        │
│ selectedYear = "1"                         │
│ selectedSemester = "Odd"                   │
│ selectedSection = "A"                      │
│                                            │
│ entries = [...]                            │
│ department = "CSE"                         │
└────────────────────────────────────────────┘
   ⚠️ selectedProgram is ObjectId
      Different format than display


AFTER:
┌────────────────────────────────────────────┐
│ StudentTimetable Component State           │
├────────────────────────────────────────────┤
│ selectedProgram = "CSE" ✨                │
│                   (department_code)        │
│ selectedYear = "1"                         │
│ selectedSemester = "Odd"                   │
│ selectedSection = "A"                      │
│                                            │
│ entries = [...]                            │
│ department = "CSE"                         │
└────────────────────────────────────────────┘
   ✅ selectedProgram is code
      Same format as display
      Matches API parameter name
```

---

## Test Coverage Map

```
┌─────────────────────────────────────────────────────────────┐
│ COMPONENT TESTING                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend:                                                  │
│  ✓ Dropdown renders program codes                          │
│  ✓ Filter sends department_code parameter                  │
│  ✓ Response includes department_code field                 │
│  ✓ Table displays entries without transformation           │
│  ✓ Pre-fill uses department_code directly                  │
│                                                             │
│  Backend:                                                   │
│  ✓ Create timetable extracts department_code               │
│  ✓ Filter endpoint accepts department_code                 │
│  ✓ Filter endpoint accepts program_id (backward compat)    │
│  ✓ Filter response includes department_code                │
│  ✓ /my endpoint returns department_code                    │
│  ✓ /options/filters returns code field                     │
│                                                             │
│  Database:                                                  │
│  ✓ New timetables have department_code field               │
│  ✓ Old timetables work without department_code             │
│  ✓ Queries work with both program_id and department_code   │
│                                                             │
│  Integration:                                               │
│  ✓ Full flow: Filter → Search → Display                    │
│  ✓ Error handling for unknown department codes             │
│  ✓ Backward compatibility with existing timetables         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Timeline

```
TIME    │ ACTIVITY
────────┼──────────────────────────────────────────────────────
T+0     │ Deploy backend changes
        │ ├─ Update timetable.py model
        │ └─ Update endpoint handlers
        │
T+5min  │ Backend API available with new fields
        │ ├─ department_code extracted on create
        │ ├─ Filter accepts department_code
        │ └─ Responses include department_code
        │
T+10min │ Deploy frontend changes
        │ ├─ Update StudentTimetable.tsx
        │ └─ Change to use department_code
        │
T+15min │ Clear caches
        │ ├─ Browser cache cleared
        │ └─ CDN cache updated (if applicable)
        │
T+20min │ End-to-end testing
        │ ├─ Create new timetable
        │ ├─ Filter by department code
        │ ├─ View entries immediately
        │ └─ Verify database stores department_code
        │
T+30min │ Monitor for issues
        │ ├─ Check server logs
        │ ├─ Monitor API response times
        │ └─ Verify no errors
        │
T+1hr   │ Full deployment complete
        │ ✅ All systems using department_code consistently
```

---

## Dependency Graph

```
┌──────────────────────┐
│  Program Model       │
│  code: "CSE"         │
└──────────────────────┘
          ▲
          │ depends on
          │
┌──────────────────────┐
│  Create Timetable    │
│  Endpoint            │
│  ├─ Fetches Program  │
│  └─ Stores code ✨  │
└──────────────────────┘
          ▲
          │ depends on
          │
┌──────────────────────┐
│  Filter Endpoint     │
│  ├─ Accepts code ✨ │
│  └─ Looks up Program│
└──────────────────────┘
          ▲
          │ used by
          │
┌──────────────────────┐
│  Student Dashboard   │
│  ├─ Sends code ✨   │
│  └─ Gets entries    │
└──────────────────────┘

✨ = New/Updated component
```

---

## Migration Path (For Existing Data)

```
EXISTING TIMETABLES WITHOUT department_code:

Step 1: API Request
        └─ department_code = "CSE"

Step 2: Backend Filter
        ├─ Find Program where code = "CSE"
        ├─ Get program_id = ObjectId(...)
        └─ Query: {program_id: ObjectId(...)}

Step 3: Timetable Found
        ├─ Check: has department_code field?
        ├─ NO → Fetch from Program
        └─ Return in response

Step 4: Response
        └─ department_code: "CSE" ✨

✅ Old timetables work without modification
✅ No migration needed
✅ Gradual adoption as new timetables created
```

---

## Version Compatibility

```
FRONTEND          BACKEND          DATABASE
v1.0              v1.0             Old
(uses program_id) (accepts both)   (no dept_code)
        ✅ Works ✅

FRONTEND          BACKEND          DATABASE
v2.0 (new)        v1.0 (updated)   Old
(uses dept_code)  (accepts both)   (no dept_code)
        ✅ Works ✅

FRONTEND          BACKEND          DATABASE
v1.0 (old)        v1.0 (updated)   New
(uses program_id) (accepts both)   (has dept_code)
        ✅ Works ✅
```

No breaking changes - full backward compatibility!
