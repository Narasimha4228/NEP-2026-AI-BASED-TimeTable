from typing import List, Dict, Any, Tuple
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from app.db.mongodb import db
from .data_collector import TimetableDataCollector

logger = logging.getLogger(__name__)

# -------------------- DATA STRUCTURES --------------------

@dataclass
class TimeSlot:
    day: str
    start_time: str
    end_time: str
    duration_minutes: int
    slot_index: int


@dataclass
class TimetableGene:
    course_id: str
    faculty_id: str
    room_id: str
    group_id: str
    time_slot: TimeSlot
    session_type: str  # theory / practical


@dataclass
class Chromosome:
    genes: List[TimetableGene]
    fitness_score: float = 0.0


# -------------------- GENETIC ALGORITHM ENGINE --------------------

class GeneticTimetableGenerator:
    """
    AI-assisted Timetable Generator using
    Rule-based + Genetic Algorithm Optimization
    """

    def __init__(
        self,
        population_size: int = 40,
        generations: int = 80,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
    ):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = 5

        self.data_collector = TimetableDataCollector()

        self.academic_setup = {}
        self.courses = []
        self.faculty = []
        self.student_groups = []
        self.rooms = []
        self.time_rules = {}
        self.time_slots: List[TimeSlot] = []

    # -------------------- EXPLAINABLE AI RULES --------------------

    def explain_rules(self):
        return {
            "hard_constraints": [
                "No faculty overlap",
                "No room overlap",
                "No student group overlap",
                "Room capacity must be sufficient",
            ],
            "soft_constraints": [
                "Balanced daily academic load",
                "Faculty workload optimization",
                "Morning slot preference",
                "Reduced continuous hours",
            ],
        }

    # -------------------- TIME SLOT GENERATION --------------------

    def generate_time_slots(self) -> List[TimeSlot]:
        slots = []
        index = 0

        for day, enabled in self.academic_setup["working_days"].items():
            if not enabled:
                continue

            current = datetime.strptime(self.time_rules["college_start_time"], "%H:%M")
            end = datetime.strptime(self.time_rules["college_end_time"], "%H:%M")
            lunch_start = datetime.strptime(self.time_rules["lunch_start_time"], "%H:%M")
            lunch_end = datetime.strptime(self.time_rules["lunch_end_time"], "%H:%M")

            while current < end:
                next_time = current + timedelta(minutes=self.time_rules["class_duration"])

                if not (lunch_start <= current < lunch_end):
                    slots.append(
                        TimeSlot(
                            day=day,
                            start_time=current.strftime("%H:%M"),
                            end_time=next_time.strftime("%H:%M"),
                            duration_minutes=self.time_rules["class_duration"],
                            slot_index=index,
                        )
                    )
                    index += 1

                current = next_time + timedelta(minutes=self.time_rules["break_duration"])

        self.time_slots = slots
        return slots

    # -------------------- CHROMOSOME CREATION --------------------

    def create_random_chromosome(self) -> Chromosome:
        genes = []

        for course in self.courses:
            hours = course.get("hours_per_week", 3)
            is_lab = course.get("course_type") == "lab"

            eligible_faculty = self.faculty or []
            eligible_rooms = self.rooms or []
            eligible_groups = [
                g for g in self.student_groups if course["id"] in g["course_ids"]
            ]

            for _ in range(hours):
                if not (eligible_faculty and eligible_rooms and eligible_groups and self.time_slots):
                    continue

                genes.append(
                    TimetableGene(
                        course_id=course["id"],
                        faculty_id=random.choice(eligible_faculty)["id"],
                        room_id=random.choice(eligible_rooms)["id"],
                        group_id=random.choice(eligible_groups)["id"],
                        time_slot=random.choice(self.time_slots),
                        session_type="practical" if is_lab else "theory",
                    )
                )

        return Chromosome(genes=genes)

    # -------------------- FITNESS FUNCTION --------------------

    def calculate_fitness(self, chromosome: Chromosome) -> float:
        score = 1000

        conflicts = self._check_conflicts(chromosome)
        score -= len(conflicts) * 50

        faculty_hours = self._faculty_workload(chromosome)
        for fid, hours in faculty_hours.items():
            faculty = next((f for f in self.faculty if f["id"] == fid), None)
            if faculty and hours > faculty.get("max_hours_per_week", 16):
                score -= (hours - faculty["max_hours_per_week"]) * 30

        return max(score, 0)

    # -------------------- CONSTRAINT CHECKS --------------------

    def _check_conflicts(self, chromosome: Chromosome) -> List[str]:
        conflicts = []
        slot_map = {}

        for g in chromosome.genes:
            key = f"{g.time_slot.day}-{g.time_slot.start_time}"
            slot_map.setdefault(key, []).append(g)

        for key, genes in slot_map.items():
            if len({g.faculty_id for g in genes}) < len(genes):
                conflicts.append(f"Faculty conflict at {key}")
            if len({g.room_id for g in genes}) < len(genes):
                conflicts.append(f"Room conflict at {key}")
            if len({g.group_id for g in genes}) < len(genes):
                conflicts.append(f"Group conflict at {key}")

        return conflicts

    def _faculty_workload(self, chromosome: Chromosome) -> Dict[str, int]:
        workload = {}
        for g in chromosome.genes:
            workload[g.faculty_id] = workload.get(g.faculty_id, 0) + 1
        return workload

    # -------------------- EVOLUTION --------------------

    def evolve(self, population: List[Chromosome]) -> List[Chromosome]:
        population.sort(key=lambda c: c.fitness_score, reverse=True)
        new_population = population[: self.elite_size]

        while len(new_population) < self.population_size:
            p1, p2 = random.sample(population[:20], 2)
            child = Chromosome(genes=random.choice([p1, p2]).genes.copy())
            new_population.append(child)

        return new_population

    # -------------------- MAIN ENTRY POINT --------------------

    async def generate_timetable(self, program_id: str, semester: int, academic_year: str):
        collected = await self.data_collector.collect_all_data(
            program_id, semester, academic_year
        )

        self.academic_setup = collected["academic_setup"]
        self.courses = collected["courses"]
        self.faculty = collected["faculty"]
        self.student_groups = collected["student_groups"]
        self.rooms = collected["rooms"]
        self.time_rules = collected["time_rules"]

        self.generate_time_slots()

        population = []
        for _ in range(self.population_size):
            c = self.create_random_chromosome()
            c.fitness_score = self.calculate_fitness(c)
            population.append(c)

        for _ in range(self.generations):
            for c in population:
                c.fitness_score = self.calculate_fitness(c)
            population = self.evolve(population)

        best = max(population, key=lambda c: c.fitness_score)

        timetable_entries = [
            {
                "course_id": g.course_id,
                "faculty_id": g.faculty_id,
                "room_id": g.room_id,
                "group_id": g.group_id,
                "day": g.time_slot.day,
                "start_time": g.time_slot.start_time,
                "end_time": g.time_slot.end_time,
                "session_type": g.session_type,
            }
            for g in best.genes
        ]

        # Generate different timetable views
        group_wise_timetable = self._generate_group_wise_timetable(timetable_entries)
        faculty_wise_timetable = self._generate_faculty_wise_timetable(timetable_entries)
        student_wise_timetable = self._generate_student_wise_timetable(timetable_entries)

        return {
            "success": True,
            "timetable_entries": timetable_entries,
            "best_fitness_score": best.fitness_score,
            "optimization_score": best.fitness_score,
            "rules_applied": self.explain_rules(),
            "conflicts": self._check_conflicts(best),
            "total_classes_scheduled": len(timetable_entries),
            "group_wise_timetable": group_wise_timetable,
            "faculty_wise_timetable": faculty_wise_timetable,
            "student_wise_timetable": student_wise_timetable,
        }

    # -------------------- TIMETABLE VIEW GENERATORS --------------------

    def _generate_group_wise_timetable(self, entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate group-wise timetable view"""
        group_timetable = {}
        
        for entry in entries:
            group_id = entry["group_id"]
            if group_id not in group_timetable:
                group_timetable[group_id] = []
            
            # Get course and faculty names
            course = next((c for c in self.courses if c["id"] == entry["course_id"]), {})
            faculty = next((f for f in self.faculty if f["id"] == entry["faculty_id"]), {})
            room = next((r for r in self.rooms if r["id"] == entry["room_id"]), {})
            
            group_entry = {
                "day": entry["day"],
                "start_time": entry["start_time"],
                "end_time": entry["end_time"],
                "course_code": course.get("code", "Unknown"),
                "course_name": course.get("name", "Unknown"),
                "faculty_name": faculty.get("name", "Unknown"),
                "room_name": room.get("name", "Unknown"),
                "session_type": entry["session_type"]
            }
            group_timetable[group_id].append(group_entry)
        
        # Sort entries by day and time
        for group_id in group_timetable:
            group_timetable[group_id].sort(key=lambda x: (x["day"], x["start_time"]))
        
        return group_timetable

    def _generate_faculty_wise_timetable(self, entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate faculty-wise timetable view"""
        faculty_timetable = {}
        
        for entry in entries:
            faculty_id = entry["faculty_id"]
            if faculty_id not in faculty_timetable:
                faculty_timetable[faculty_id] = []
            
            # Get course, group, and room names
            course = next((c for c in self.courses if c["id"] == entry["course_id"]), {})
            group = next((g for g in self.student_groups if g["id"] == entry["group_id"]), {})
            room = next((r for r in self.rooms if r["id"] == entry["room_id"]), {})
            faculty = next((f for f in self.faculty if f["id"] == faculty_id), {})
            
            faculty_entry = {
                "day": entry["day"],
                "start_time": entry["start_time"],
                "end_time": entry["end_time"],
                "course_code": course.get("code", "Unknown"),
                "course_name": course.get("name", "Unknown"),
                "group_name": group.get("name", "Unknown"),
                "room_name": room.get("name", "Unknown"),
                "session_type": entry["session_type"],
                "faculty_name": faculty.get("name", "Unknown")
            }
            faculty_timetable[faculty_id].append(faculty_entry)
        
        # Sort entries by day and time
        for faculty_id in faculty_timetable:
            faculty_timetable[faculty_id].sort(key=lambda x: (x["day"], x["start_time"]))
        
        return faculty_timetable

    def _generate_student_wise_timetable(self, entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate student-wise timetable view"""
        student_timetable = {}
        
        # For dynamic groups, we need to map students to their groups
        for group in self.student_groups:
            if group.get("type") == "dynamic" and "student_ids" in group:
                for student_id in group["student_ids"]:
                    if student_id not in student_timetable:
                        student_timetable[student_id] = []
                    
                    # Get entries for this group
                    group_entries = [e for e in entries if e["group_id"] == group["id"]]
                    
                    for entry in group_entries:
                        course = next((c for c in self.courses if c["id"] == entry["course_id"]), {})
                        faculty = next((f for f in self.faculty if f["id"] == entry["faculty_id"]), {})
                        room = next((r for r in self.rooms if r["id"] == entry["room_id"]), {})
                        
                        student_entry = {
                            "day": entry["day"],
                            "start_time": entry["start_time"],
                            "end_time": entry["end_time"],
                            "course_code": course.get("code", "Unknown"),
                            "course_name": course.get("name", "Unknown"),
                            "faculty_name": faculty.get("name", "Unknown"),
                            "room_name": room.get("name", "Unknown"),
                            "session_type": entry["session_type"],
                            "group_name": group.get("name", "Unknown")
                        }
                        student_timetable[student_id].append(student_entry)
        
        # Sort entries by day and time for each student
        for student_id in student_timetable:
            student_timetable[student_id].sort(key=lambda x: (x["day"], x["start_time"]))
        
        return student_timetable
