# Data → Model → Results Flow

## 1️⃣ DATA FILES (What gets trained on)

### Location: `data/training_data.json`
Contains:

```
{
  "timestamp": "2026-02-05T...",
  "constraints": {
    "num_entries": 150,           ← Total classes to schedule
    "num_slots": 60,              ← Available time slots
    "num_rooms": 15,              ← Classrooms available
    "num_instructors": 25,        ← Teachers
    "num_courses": 30,
    "max_hours_per_day": 8,
    "min_break_between_classes": 15
  },
  
  "courses": [                    ← List of all courses
    {
      "id": 1,
      "code": "CSE101",
      "name": "Introduction to Programming",
      "department": "CSE",
      "year": 1,
      "instructor_id": 5,
      "students_count": 50,
      "required_slots": 3          ← Classes per week
    },
    ...
  ],
  
  "instructors": [                ← List of all instructors
    {
      "id": 1,
      "name": "Dr. Smith",
      "department": "CSE",
      "max_classes_per_day": 4,
      "unavailable_slots": [2, 5],
      "office_room": "Office 101"
    },
    ...
  ],
  
  "rooms": [                       ← List of all classrooms
    {
      "id": 1,
      "number": "Building A-101",
      "building": "Building A",
      "capacity": 80,
      "room_type": "Lecture",
      "has_projector": true,
      "has_computer": false
    },
    ...
  ],
  
  "student_groups": [              ← List of all student groups
    {
      "id": 1,
      "name": "CSE 1-A",
      "department": "CSE",
      "year": 1,
      "section": "A",
      "student_count": 40,
      "courses": [1, 2, 3]
    },
    ...
  ]
}
```

---

## 2️⃣ GENETIC MODEL (How it trains)

### Location: `models/genetic_model_YYYYMMDD_HHMMSS.json`

The model trains using:

```
GENETIC ALGORITHM TRAINING:

1. INITIALIZATION
   ↓
   Create 50 random "chromosomes" (timetable assignments)
   Each chromosome = array of time slots for each class
   Example: [2, 5, 8, 3, 1, 9, ...]
            ↑ slot for class 1, slot for class 2, etc.

2. FITNESS EVALUATION (Per Generation)
   ↓
   For each chromosome, calculate "fitness score":
   - Conflicts detected = +10 penalty
   - Room overbooked = penalty
   - Instructor has 2 classes at same time = penalty
   - Imbalanced room usage = penalty
   
   Lower score = Better solution ✓

3. SELECTION (Tournament)
   ↓
   Pick best chromosomes from population

4. CROSSOVER (Genetic Mixing)
   ↓
   Take 2 good chromosomes:
   Parent 1: [2, 5, 8, 3, 1, 9, ...]
   Parent 2: [4, 1, 6, 7, 2, 3, ...]
                    ↓ Split point
   Child 1:  [2, 5, 8 | 7, 2, 3, ...]
   Child 2:  [4, 1, 6 | 3, 1, 9, ...]

5. MUTATION (Small Changes)
   ↓
   Randomly change a gene (10% chance):
   Before: [2, 5, 8, 3, 1, 9, ...]
   After:  [2, 5, 8, 6, 1, 9, ...]  ← Changed 3 to 6
                    ↑

6. REPEAT 100 generations
   ↓
   Track best fitness at each step
```

### Saved Model Contains:

```json
{
  "timestamp": "2026-02-05T...",
  "generations": 100,
  "population_size": 50,
  "mutation_rate": 0.1,
  "crossover_rate": 0.8,
  
  "best_fitness": 45.32,          ← Lowest score achieved
  
  "best_chromosome": [2, 5, 8, 3, 1, 9, ...],  ← Best solution
  
  "convergence_history": [
    {"generation": 0, "fitness": 234.5},
    {"generation": 1, "fitness": 198.3},
    {"generation": 2, "fitness": 187.1},
    ...
    {"generation": 99, "fitness": 45.32}   ← Improved ✓
  ],
  
  "constraints": { ... }
}
```

---

## 3️⃣ RESULTS (What you get)

### Location: `results/` folder

#### A. training_report_YYYYMMDD_HHMMSS.md
```
# Genetic Model Training Report
Generated: 2026-02-05 14:30:15

## Training Configuration
- Generations: 100
- Population Size: 50
- Mutation Rate: 0.1
- Crossover Rate: 0.8

## Training Results
- Best Fitness Score: 45.3200
- Convergence Steps: 100

## Convergence History
| Generation | Fitness Score |
|------------|---------------|
|          0 |     234.5000  |
|          5 |     178.3200  |
|         10 |     156.1400  |
|         50 |      67.8500  |
|         99 |      45.3200  |

## Improvement
- Started at: 234.5 (many conflicts)
- Ended at: 45.32 (optimized)
- Total improvement: 80.67%
```

#### B. training_summary_YYYYMMDD_HHMMSS.json
```json
{
  "timestamp": "2026-02-05T14:30:15",
  "generations": 100,
  "population_size": 50,
  "best_fitness": 45.32,
  "model_file": "models/genetic_model_20260205_143015.json",
  "report_file": "results/training_report_20260205_143015.md"
}
```

---

## 📊 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA PHASE                           │
│                                                              │
│  Generate: 30 courses × 25 instructors × 15 rooms          │
│            100+ student groups with 150+ class entries     │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    data/training_data.json
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      TRAINING PHASE                         │
│                                                              │
│  Genetic Algorithm: 100 generations × 50 population        │
│                                                              │
│  Generation 0:  Fitness = 234.5 ❌ (many conflicts)       │
│  Generation 25: Fitness = 89.2 ⚠️  (improving)            │
│  Generation 50: Fitness = 56.1 🟡 (better)                │
│  Generation 99: Fitness = 45.3 ✓  (optimized!)            │
└─────────────────────────────────────────────────────────────┘
                            ↓
    ┌───────────────────────┴───────────────────────┐
    ↓                                               ↓
models/genetic_model_...json            results/training_report_...md
(Complete trained model)                (Analysis & visualization)
└───────────────────────────────────────────────────────────────┘
```

---

## 🔄 Example Usage Flow

```bash
# 1. DATA INPUT
python prepare_data.py
→ Creates data/training_data.json (150 classes, 25 teachers, 15 rooms)

# 2. TRAINING
python train_genetic_model.py
→ Runs GA for 100 generations
→ Evaluates fitness each step
→ Saves best_fitness: 45.32

# 3. RESULTS
→ models/genetic_model_20260205_143015.json
→ results/training_report_20260205_143015.md
→ results/training_summary_20260205_143015.json

# VIEW RESULTS
cat results/training_report_20260205_143015.md
```

---

## 📈 Key Metrics in Results

| Metric | Meaning | Example |
|--------|---------|---------|
| **best_fitness** | Quality of best solution (lower=better) | 45.32 |
| **convergence** | How fast it improved | 89% improvement |
| **generations** | Training iterations | 100 |
| **population_size** | Solutions tested per generation | 50 |
| **best_chromosome** | The optimal timetable solution | [2,5,8,3,...] |

---

## ✅ What Each File Represents

| File | Contains | Purpose |
|------|----------|---------|
| `data/training_data.json` | Raw input (courses, rooms, instructors) | Training input |
| `models/genetic_model_*.json` | Trained model + history | Deploy model |
| `results/training_report_*.md` | Human-readable analysis | Review progress |
| `results/training_summary_*.json` | Key statistics | Integration |
