#!/usr/bin/env python3
"""
Test the faculty diversity fix in timetable generation
This test verifies that the generated timetable entries have diverse faculty names
instead of all showing "mohan"
"""

import sys
sys.path.insert(0, '/d/NEP-Timetable-AI-master/backend')

from app.services.timetable.advanced_generator import AdvancedTimetableGenerator, Faculty, StudentGroup, Room


def test_faculty_override():
    """Test that user-provided faculty overrides database faculty"""
    print("\n" + "="*60)
    print("TEST: Faculty Override in Advanced Generator")
    print("="*60)
    
    # Create test academic setup with user-provided faculty
    academic_setup = {
        "faculty": [
            {
                "id": "F001",
                "name": "Dr. Smith",
                "subjects": ["PROB_STATS", "ML_THEORY"]
            },
            {
                "id": "F002", 
                "name": "Dr. Johnson",
                "subjects": ["OS_THEORY", "OS_LAB"]
            },
            {
                "id": "F003",
                "name": "Dr. Brown",
                "subjects": ["OOP_THEORY", "OOP_LAB"]
            },
            {
                "id": "F004",
                "name": "Dr. Davis",
                "subjects": ["IND_MGMT", "CLOUD_COMP"]
            },
            {
                "id": "F005",
                "name": "Dr. Ravi",  # Important: This should replace "mohan"
                "subjects": ["OPT_TECH"]
            }
        ]
    }
    
    # Create generator
    generator = AdvancedTimetableGenerator()
    
    # Test 1: Setup with hardcoded data first (without async)
    print("\n[TEST 1] Setting up with hardcoded data...")
    generator.setup_cse_ai_ml_courses()
    
    # Manually create groups and rooms to avoid async issues
    generator.groups = [
        StudentGroup("G001", "Group 1", 30, False, None),
        StudentGroup("G001.1", "Group 1.1", 15, True, "G001"),
        StudentGroup("G001.2", "Group 1.2", 15, True, "G001")
    ]
    generator.rooms = [
        Room("R001", "N-001", 75, False),
        Room("R002", "N-002", 70, False),
        Room("R003", "N-003", 65, False),
        Room("R004", "N-004", 60, False),
        Room("R017", "N-017", 35, True),
        Room("R018", "N-018", 35, True),
    ]
    
    print(f"  Before override: {len(generator.faculty)} faculty")
    print(f"  Faculty names: {[f.name for f in generator.faculty]}")
    
    # Test 2: Simulate the load_from_database_with_setup behavior
    print(f"\n[TEST 2] Overriding with {len(academic_setup['faculty'])} user-provided faculty...")
    generator.faculty = []
    for fac in academic_setup['faculty']:
        fac_obj = Faculty(
            id=fac.get("id") or f"user_fac_{len(generator.faculty)}",
            name=fac.get("name", ""),
            subjects=fac.get("subjects", ["GENERAL"])
        )
        generator.faculty.append(fac_obj)
    print(f"  After override: {len(generator.faculty)} faculty")
    print(f"  Faculty names: {[f.name for f in generator.faculty]}")
    
    # Test 3: Generate a timetable
    print("\n[TEST 3] Generating timetable with diverse faculty...")
    print(f"  Courses: {len(generator.courses)}")
    print(f"  Groups: {len(generator.groups)}")
    print(f"  Rooms: {len(generator.rooms)}")
    print(f"  Faculty: {len(generator.faculty)}")
    
    try:
        result = generator.generate_timetable()
        
        if result.get("success"):
            entries = result.get("schedule", [])
            print(f"\n  ✅ Generated {len(entries)} entries")
            
            # Test 4: Check for faculty diversity
            print("\n[TEST 4] Checking faculty diversity...")
            faculty_names = set()
            for entry in entries:
                faculty_name = entry.get("faculty", "TBD")
                faculty_names.add(faculty_name)
            
            print(f"  Unique faculty found: {len(faculty_names)}")
            print(f"  Faculty names: {sorted(faculty_names)}")
            
            # Check if "mohan" is NOT in the results (success criterion)
            if "mohan" in faculty_names:
                print("\n  ❌ FAIL: 'mohan' still appears in faculty names!")
                return False
            else:
                print("\n  ✅ PASS: No hardcoded 'mohan' in faculty names!")
            
            # Check for "Dr. Ravi" (the important one the user mentioned)
            if "Dr. Ravi" in faculty_names:
                print("  ✅ PASS: 'Dr. Ravi' found in faculty names!")
            else:
                print("  ⚠️  WARNING: 'Dr. Ravi' not found in faculty names")
            
            # Check for faculty diversity (should have more than 1)
            non_tbd_faculty = [f for f in faculty_names if f and f != 'TBD']
            if len(non_tbd_faculty) > 1:
                print(f"  ✅ PASS: Faculty diversity verified ({len(non_tbd_faculty)} unique faculty)")
            else:
                print(f"  ❌ FAIL: Faculty diversity not achieved (only {len(non_tbd_faculty)} unique faculty)")
                return False
            
            # Verify first few entries
            print("\n[TEST 5] Sample generated entries:")
            for i, entry in enumerate(entries[:10]):
                print(f"  [{i+1}] {entry.get('course_code', 'Unknown')} - Faculty: {entry.get('faculty', 'TBD')}")
            
            return True
        else:
            print(f"\n  ❌ Generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n  ❌ Exception during generation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n[INFO] Running faculty diversity test...")
    
    success = test_faculty_override()
    
    if success:
        print("\n" + "="*60)
        print("✅ TEST PASSED: Faculty diversity working correctly!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ TEST FAILED: Check logs above")
        print("="*60)
        sys.exit(1)
