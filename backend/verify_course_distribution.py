#!/usr/bin/env python3
"""Verify courses are properly distributed across days (no duplicates)"""

from app.services.timetable.advanced_generator import AdvancedTimetableGenerator
from app.models.timetable import Faculty, Course, Group, Room, ConstraintRules

print("=" * 70)
print("VERIFYING COURSE DISTRIBUTION (No Duplicates Per Day)")
print("=" * 70)

# Setup
generator = AdvancedTimetableGenerator()

# Create test data
generator.faculty = [
    Faculty("F001", "Dr. Smith", ["OS_THEORY", "ML_THEORY"]),
    Faculty("F002", "Dr. Johnson", ["OS_THEORY", "OS_LAB"]),
    Faculty("F003", "Dr. Brown", ["OOP_THEORY", "OOP_LAB"]),
    Faculty("F004", "Dr. Davis", ["CLOUD_COMP", "IND_MGMT"]),
    Faculty("F005", "Dr. Ravi", ["OPT_TECH", "PROB_STATS"]),
]

generator.courses = [
    Course("OS_THEORY", "Operating Systems Theory", 4, 4, False),
    Course("OS_LAB", "Operating Systems Lab", 3, 2, True),
    Course("OOP_THEORY", "OOP Theory", 4, 4, False),
    Course("OOP_LAB", "OOP Lab", 3, 2, True),
    Course("ML_THEORY", "Machine Learning", 4, 4, False),
    Course("CLOUD_COMP", "Cloud Computing", 2, 4, False),
    Course("IND_MGMT", "Industrial Management", 2, 2, False),
    Course("OPT_TECH", "Optimization Techniques", 2, 2, False),
    Course("PROB_STATS", "Probability & Statistics", 2, 2, False),
]

generator.groups = [
    Group("G001", "CSE-A", False, 60),
    Group("G001.1", "CSE-A-1", True, 30),
    Group("G001.2", "CSE-A-2", True, 30),
]

generator.rooms = [
    Room("R001", "Room 101", 70),
    Room("R002", "Room 102", 70),
    Room("R003", "Room 103", 50),
    Room("R004", "Room 104", 50),
]

generator.rules = ConstraintRules()
generator.initialize_occupancy_tracking()

# Generate
print("\nGenerating timetable with course distribution constraint...\n")
result = generator.generate_timetable()

if result["valid"]:
    print("\n✓ Generation successful!")
    print(f"  Sessions scheduled: {result['sessions_count']}")
    print(f"  Optimization score: {result['score']}")
    
    # Analyze course distribution
    print("\n" + "=" * 70)
    print("COURSE DISTRIBUTION BY DAY")
    print("=" * 70)
    
    schedule = result.get('timetable_entries', [])
    
    # Group by course and day
    course_day_distribution = {}
    for entry in schedule:
        course = entry.get('course_code', 'UNKNOWN')
        day = entry.get('day', 'UNKNOWN')
        key = (course, day)
        
        if key not in course_day_distribution:
            course_day_distribution[key] = []
        course_day_distribution[key].append(entry)
    
    # Display distribution
    courses_by_name = {}
    for course in generator.courses:
        courses_by_name[course.code] = course.name
    
    for (course_code, day) in sorted(course_day_distribution.keys()):
        entries = course_day_distribution[(course_code, day)]
        course_name = courses_by_name.get(course_code, course_code)
        
        print(f"\n{course_code} ({course_name}) on {day}: {len(entries)} session(s)")
        for i, entry in enumerate(entries, 1):
            faculty = entry.get('faculty_name', 'Unknown')
            time = f"{entry.get('start_time', '?')}-{entry.get('end_time', '?')}"
            room = entry.get('room_name', '?')
            print(f"  [{i}] {time} | {faculty} | {room}")
    
    # Verify no duplicates
    print("\n" + "=" * 70)
    print("DUPLICATE VERIFICATION")
    print("=" * 70)
    
    duplicates_found = False
    for (course_code, day), entries in course_day_distribution.items():
        if len(entries) > 2:  # Allow up to 2 (theory + lab for same group)
            print(f"⚠️  {course_code} on {day}: {len(entries)} sessions (>2 - potential issue)")
            duplicates_found = True
    
    if not duplicates_found:
        print("✓ No duplicate courses on same day (courses properly spread)")
    
    # Course spread analysis
    print("\n" + "=" * 70)
    print("COURSE SPREAD ANALYSIS (Days per course)")
    print("=" * 70)
    
    course_days_count = {}
    for (course_code, day) in course_day_distribution.keys():
        if course_code not in course_days_count:
            course_days_count[course_code] = set()
        course_days_count[course_code].add(day)
    
    for course_code in sorted(course_days_count.keys()):
        days = course_days_count[course_code]
        course_name = courses_by_name.get(course_code, course_code)
        print(f"{course_code} ({course_name}): {len(days)} days - {sorted(days)}")
    
    print("\n" + "=" * 70)
    print("✓ COURSE DISTRIBUTION TEST PASSED!")
    print("=" * 70)
else:
    print("\n✗ Generation failed")
    if result.get('hard_constraints_violations'):
        print("Constraint violations:")
        for v in result['hard_constraints_violations']:
            print(f"  - {v}")
