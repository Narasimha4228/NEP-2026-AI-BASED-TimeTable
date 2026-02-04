# Department Code Implementation - Deployment & Rollout Checklist

## Pre-Deployment

### Code Review
- [ ] Backend changes reviewed and approved
- [ ] Frontend changes reviewed and approved
- [ ] No syntax errors in Python or TypeScript
- [ ] All imports correct and dependencies available
- [ ] No console.error or console.warn left in code

### Testing (Local)
- [ ] Run backend tests locally
- [ ] Run frontend tests locally
- [ ] Create new timetable and verify `department_code` stored
- [ ] Filter by department_code and verify results
- [ ] Check browser console for errors

### Documentation
- [ ] All 5 documentation files created
- [ ] README updated with links to new docs
- [ ] Team notified of changes

---

## Deployment Phase 1: Backend

### Preparation
- [ ] Backup MongoDB (recommended)
- [ ] Note current API version
- [ ] Prepare rollback plan
- [ ] Set monitoring alerts

### Deployment
- [ ] Update `backend/app/models/timetable.py`
- [ ] Update `backend/app/api/v1/endpoints/timetable.py`
- [ ] Restart API server
- [ ] Verify API is running: `curl http://localhost:8000/health`
- [ ] Check logs for startup errors

### Verification (Backend Only)
- [ ] Test `/timetable/options/filters` endpoint
  ```bash
  curl -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/timetable/options/filters
  ```
  Expected: Programs array includes `code` field

- [ ] Test `/timetable/filter` with department_code
  ```bash
  curl -H "Authorization: Bearer <token>" \
    "http://localhost:8000/api/v1/timetable/filter?department_code=CSE&year=1&semester=Odd&section=A"
  ```
  Expected: Response includes `department_code` and `entries`

- [ ] Test `/timetable/my` endpoint
  ```bash
  curl -H "Authorization: Bearer <token>" \
    http://localhost:8000/api/v1/timetable/my
  ```
  Expected: Response includes both `department` and `department_code`

- [ ] Check logs
  ```bash
  tail -f server.log | grep -i "program\|code\|timetable"
  ```
  Expected: No errors, normal operations

---

## Deployment Phase 2: Frontend

### Preparation
- [ ] Clear browser cache
- [ ] Prepare CDN cache invalidation (if applicable)
- [ ] Have rollback script ready

### Deployment
- [ ] Update `frontend/src/components/pages/StudentTimetable.tsx`
- [ ] Run build
  ```bash
  cd frontend && npm run build
  ```
- [ ] Verify build succeeds without errors
- [ ] Deploy to production
- [ ] Clear CDN cache

### Verification (Frontend)
- [ ] Open Student Dashboard
- [ ] Check browser console (F12)
  - [ ] No red errors
  - [ ] Look for `✅ Filter options loaded`
  
- [ ] Department dropdown shows codes
  - [ ] Should see "CSE - Computer Science Engineering"
  - [ ] Should see "ECE - Electronics and..."
  - [ ] NOT see ObjectIds

- [ ] Test filter
  - [ ] Select different department
  - [ ] Click "Search Timetable"
  - [ ] Check console: `🔍 Filtering timetable with: {department_code: "CSE"...}`
  - [ ] Verify table updates with entries

- [ ] Check DevTools Network tab
  - [ ] Filter request shows `department_code=CSE` in URL
  - [ ] Response includes `department_code` field
  - [ ] Response includes `entries` array

---

## Deployment Phase 3: Integration Testing

### End-to-End Testing
- [ ] Create new timetable in Admin panel
- [ ] Verify database: `db.timetables.findOne({is_draft: false}, {department_code: 1})`
  - [ ] Should show: `"department_code": "CSE"`

- [ ] Test complete filter flow
  1. Open Student Dashboard
  2. Select department from dropdown
  3. Click "Search Timetable"
  4. Verify table shows courses
  5. Check console logs are correct

- [ ] Test old timetables (backward compatibility)
  1. Ensure old timetables still appear in filter
  2. Can filter by old timetables
  3. Entries display correctly

- [ ] Test error cases
  1. Select non-existent combination
  2. Should show "No timetable available"
  3. Debug info should appear

### Cross-Browser Testing
- [ ] Chrome/Edge (Latest)
- [ ] Firefox (Latest)
- [ ] Safari (Latest)
- [ ] Mobile (iOS/Android)

---

## Post-Deployment

### Monitoring (First 24 Hours)
- [ ] Watch server logs for errors
  ```bash
  grep -i "error\|exception\|traceback" server.log
  ```
  Expected: Only pre-existing errors, none related to department_code

- [ ] Monitor API response times
  Expected: < 500ms for filter requests

- [ ] Monitor error rates
  Expected: No increase in 4xx/5xx responses

- [ ] Check database for new timetables
  ```bash
  db.timetables.countDocuments({is_draft: false, department_code: {$exists: true}})
  ```
  Expected: > 0 (increases as new timetables created)

### User Feedback Collection
- [ ] Email to users: "Department code consistency update deployed"
- [ ] Post in team chat: "New feature available"
- [ ] Gather feedback on timetable filtering experience
- [ ] Note any issues reported

### Documentation Updates
- [ ] Update system documentation
- [ ] Create release notes
- [ ] Update API documentation
- [ ] Update user guides

---

## Verification Checklist (7 Days Post-Deployment)

### Functionality
- [ ] At least 5 new timetables created with department_code
- [ ] All users can filter by department without issues
- [ ] No user complaints about timetable filtering
- [ ] Student dashboard shows correct department codes

### Performance
- [ ] API response time still < 500ms
- [ ] Database queries performant
- [ ] No slowdowns reported

### Data Integrity
- [ ] All new timetables have department_code
- [ ] Old timetables still accessible
- [ ] No data corruption or missing entries

### Error Handling
- [ ] No errors in logs related to department_code
- [ ] Error messages are helpful and clear
- [ ] No stack traces in console

---

## Rollback Procedures

### If Critical Issue Found (Immediate)

#### Backend Rollback
1. Revert `backend/app/models/timetable.py`
2. Revert `backend/app/api/v1/endpoints/timetable.py`
3. Restart API server
4. Verify API is operational

#### Frontend Rollback
1. Revert `frontend/src/components/pages/StudentTimetable.tsx` (line 140)
2. Rebuild frontend
3. Clear cache and redeploy

#### Verification
```bash
# Test old endpoint works
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/timetable/filter?program_id=60a7c5e1f2c4d8e0a8b1c2d3&year=1&semester=Odd&section=A"
```

### If Partial Issue (During Business Hours)

1. **Document the issue** with:
   - User action that triggered it
   - Error message/behavior
   - Step to reproduce
   - Expected vs actual result

2. **Assess impact**:
   - How many users affected?
   - Is filter still usable?
   - Can users view their timetables?

3. **Decide**: Fix or rollback?
   - **Fix**: Apply hotfix if simple
   - **Rollback**: If issue significant

4. **Communicate**: Notify users of status and ETA

---

## Success Criteria

### Day 1
- ✅ Zero critical errors
- ✅ API responding normally
- ✅ Frontend loads without console errors
- ✅ Filter works with both old and new formats

### Day 7
- ✅ Multiple new timetables created with department_code
- ✅ All filter operations successful
- ✅ User feedback positive
- ✅ No regressions in other features

### Day 30
- ✅ All new timetables use department_code consistently
- ✅ No issues reported by users
- ✅ System performing as expected
- ✅ Ready to declare deployment complete

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | __________ | ______ | __________ |
| QA Lead | __________ | ______ | __________ |
| DevOps | __________ | ______ | __________ |
| Product Manager | __________ | ______ | __________ |

---

## Emergency Contacts

**During Deployment Issues:**
- Backend Lead: _______________
- Frontend Lead: _______________
- DevOps: _______________
- Database Admin: _______________

**Escalation:**
1. First: Team Lead
2. Second: Engineering Manager
3. Third: Department Head

---

## Post-Deployment Report

### Date Deployed: _______________
### Deployed By: _______________
### Issues Encountered: 

_________________________________
_________________________________
_________________________________

### Lessons Learned:

_________________________________
_________________________________
_________________________________

### Follow-up Actions:

- [ ] ________________________________________
- [ ] ________________________________________
- [ ] ________________________________________

---

## Final Sign-Off

**Deployment Status:** ☐ Successful ☐ With Issues ☐ Rolled Back

**Comments:**
_________________________________
_________________________________
_________________________________

**Deployed By:** __________________ **Date:** __________

**Verified By:** __________________ **Date:** __________

---

## Quick Reference Commands

### Check Backend Status
```bash
# API health
curl http://localhost:8000/health

# Get filter options
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/timetable/options/filters

# View server logs
tail -f backend/server.log
```

### Check Frontend Status
```bash
# Open browser console
F12 or Cmd+Option+I

# Search for errors
grep -i "error" in console

# Check network requests
Open DevTools → Network tab → Filter by "filter" or "timetable"
```

### Check Database Status
```bash
# Connect to MongoDB
mongosh

# Check new timetables
db.timetables.find(
  {is_draft: false},
  {program_id: 1, department_code: 1, title: 1}
).pretty()

# Count timetables with department_code
db.timetables.countDocuments({department_code: {$exists: true}})
```

---

**This deployment checklist ensures a safe, verified, and professional deployment of the department code consistency implementation.**
