# Frontend Not Showing Data - Problem & Solution

## ❌ THE PROBLEM

Your screenshot shows an **empty timetable grid** because:

```
Backend ✓ (Running on localhost:8000)
   ↓
Genetic Model Training ✓ (Generates data)
   └─→ Saves to: models/genetic_model_*.json ✓
   └─→ Saves to: data/training_data.json ✓
   ↓
❌ BUT NOT SAVED TO DATABASE ❌
   ↓
Frontend (Calls API to fetch timetable)
   ↓
API Query: SELECT FROM timetables WHERE is_draft = false
   ↓
❌ Database is EMPTY - No timetable found
   ↓
❌ Frontend shows BLANK GRID
```

---

## 🔍 WHY IT HAPPENS

### Current Flow:
1. Genetic model trains ✓
2. Saves to JSON files ✓
3. Frontend calls: `GET /api/v1/timetable/public/{timetable_id}`
4. Backend queries MongoDB for published timetables
5. ❌ **MongoDB is empty - nothing to return**
6. ❌ Frontend displays blank

### The Missing Link:
```
Genetic Model (JSON files)  ─────────────┐
                                         ↓
                                   ❌ NO CONNECTION ❌
                                         ↓
      Database (MongoDB)           ←────┘
      
Should be:

Genetic Model (JSON) → Import Script → Database → API → Frontend
```

---

## ✅ THE SOLUTION

### Step 1: Run Training Pipeline (Already Done ✓)
```bash
python genetic_model_training/scripts/training_pipeline.py
```
Creates:
- `data/training_data.json`
- `models/genetic_model_20260205_122140.json`

### Step 2: Import to Database (NEW!)
```bash
cd backend
python genetic_model_training/scripts/import_to_database.py
```

This script will:
1. Load the genetic model from JSON
2. Convert chromosome to timetable entries
3. Create a published timetable in MongoDB
4. **Return the Timetable ID**

Example output:
```
📦 Loading genetic model from: genetic_model_20260205_122140.json
Best fitness: 98.26
Generations: 100
✓ Created 150 timetable entries from genetic model
✓ Timetable saved to database!
✓ Timetable ID: 65a1b2c3d4e5f6g7h8i9j0k1
✓ Published: True

📝 Use this timetable ID in frontend: 65a1b2c3d4e5f6g7h8i9j0k1
```

### Step 3: View in Frontend
1. Copy the **Timetable ID**
2. Go to frontend URL: `http://localhost:5173/timetable/65a1b2c3d4e5f6g7h8i9j0k1`
3. ✓ Timetable now displays!

---

## 📊 Complete Flow (Fixed)

```
1. PREPARE DATA
   └─→ python prepare_data.py
       └─→ data/training_data.json ✓

2. TRAIN GENETIC MODEL
   └─→ python training_pipeline.py
       ├─→ models/genetic_model_*.json ✓
       └─→ results/training_report_*.md ✓

3. IMPORT TO DATABASE ← NEW STEP
   └─→ python import_to_database.py
       ├─→ MongoDB: timetables collection ✓
       └─→ Returns: Timetable ID ✓

4. VIEW IN FRONTEND
   └─→ http://localhost:5173/timetable/{ID}
       └─→ ✓ Timetable displays with all entries!
```

---

## 🚀 Quick Fix (Do This Now)

### Run in terminal:
```bash
cd D:\NEP-Timetable-AI-master\backend

# If you haven't already trained:
cd genetic_model_training
python scripts/training_pipeline.py
cd ..

# Import to database:
python genetic_model_training/scripts/import_to_database.py
```

### Expected output:
```
✓ Timetable saved to database!
✓ Timetable ID: YOUR_ID_HERE
```

### Then view in frontend:
1. Replace `{TIMETABLE_ID}` with the ID from above
2. Open: `http://localhost:5173/timetable/{TIMETABLE_ID}`
3. ✓ See the timetable!

---

## 🔧 Why This Disconnect?

| Component | Purpose | Output | Input |
|-----------|---------|--------|-------|
| **Genetic Training** | Optimize scheduling | JSON files | - |
| **Database** | Store timetables | - | Formatted timetable data |
| **API** | Serve timetables | Timetable JSON | Query database |
| **Frontend** | Display timetable | HTML grid | API response |

**Missing**: The bridge between JSON output and database input!

---

## 📋 Checklist

- [ ] Backend is running (`localhost:8000`)
- [ ] Genetic model trained (generates `models/*.json`)
- [ ] Import script ran successfully (`import_to_database.py`)
- [ ] Timetable ID printed in terminal
- [ ] Database has timetable entry (`is_draft: false`)
- [ ] Frontend loads with `?timetable_id={ID}`
- [ ] ✓ Timetable displays!

---

## 🆘 Still Not Working?

Check these:

1. **Is backend running?**
   ```bash
   curl http://localhost:8000/api/v1/programs
   # Should return JSON, not connection error
   ```

2. **Does database have the timetable?**
   ```bash
   # In MongoDB:
   db.timetables.find({is_draft: false}).count()
   # Should show: 1 (or more)
   ```

3. **Is frontend using correct ID?**
   - Check URL: `http://localhost:5173/timetable/{ID}`
   - Check browser console for errors (F12)
   - Check Network tab to see API response

4. **Check logs:**
   - Backend logs: Any 404 errors?
   - Browser console (F12): CORS errors?
   - Frontend network requests: What's the response?
