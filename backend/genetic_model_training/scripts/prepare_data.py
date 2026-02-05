"""
Data Preparation Script for Genetic Model Training
Prepares and preprocesses timetable data for model training
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class TrainingDataPreparator:
    """Prepares training data for the genetic model"""
    
    def __init__(self, output_dir: str = "../data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_sample_constraints(self) -> Dict[str, Any]:
        """Create sample constraints for training"""
        return {
            'num_entries': 150,           # Total class entries to schedule
            'num_slots': 60,              # Total time slots available
            'num_rooms': 15,              # Number of classrooms
            'num_instructors': 25,        # Number of instructors
            'num_courses': 30,            # Number of courses
            'num_students': 500,          # Number of students
            'conflicts': 8,               # Known conflicts/hard constraints
            'max_hours_per_day': 8,       # Maximum hours per day
            'min_break_between_classes': 15,  # Minimum break (minutes)
            'working_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'time_slots': {
                '8:00-9:00': 0,
                '9:00-10:00': 1,
                '10:00-11:00': 2,
                '11:00-12:00': 3,
                '12:00-1:00': 4,
                '1:00-2:00': 5,
                '2:00-3:00': 6,
                '3:00-4:00': 7,
                '4:00-5:00': 8
            }
        }
    
    def create_courses_data(self) -> List[Dict[str, Any]]:
        """Create sample courses data"""
        courses = []
        departments = ['CSE', 'ECE', 'Mechanical', 'Civil', 'Electrical']
        years = [1, 2, 3, 4]
        
        course_id = 1
        for dept in departments:
            for year in years:
                for i in range(2):  # 2 courses per dept-year combination
                    courses.append({
                        'id': course_id,
                        'code': f"{dept}{year}0{i+1}",
                        'name': f"{dept} Course Year {year} - {i+1}",
                        'department': dept,
                        'year': year,
                        'credits': 3 + i,
                        'instructor_id': (course_id % 25) + 1,
                        'students_count': 40 + (i * 10),
                        'required_slots': 3 + i  # Classes per week
                    })
                    course_id += 1
        
        return courses
    
    def create_instructors_data(self) -> List[Dict[str, Any]]:
        """Create sample instructors data"""
        instructors = []
        names = [
            'Dr. Smith', 'Prof. Johnson', 'Dr. Williams', 'Prof. Brown',
            'Dr. Jones', 'Prof. Garcia', 'Dr. Miller', 'Prof. Davis',
            'Dr. Rodriguez', 'Prof. Martinez', 'Dr. Hernandez', 'Prof. Lopez',
            'Dr. Gonzalez', 'Prof. Wilson', 'Dr. Anderson', 'Prof. Thomas',
            'Dr. Taylor', 'Prof. Moore', 'Dr. Jackson', 'Prof. Martin',
            'Dr. Lee', 'Prof. Perez', 'Dr. Thompson', 'Prof. White',
            'Dr. Harris'
        ]
        
        for idx, name in enumerate(names, 1):
            instructors.append({
                'id': idx,
                'name': name,
                'department': ['CSE', 'ECE', 'Mechanical', 'Civil', 'Electrical'][(idx-1) % 5],
                'max_classes_per_day': 4,
                'unavailable_slots': [(idx % 3), (idx % 5)],  # Some unavailable slots
                'specialization': f"Specialization {idx}",
                'office_room': f"Office {100 + idx}"
            })
        
        return instructors
    
    def create_rooms_data(self) -> List[Dict[str, Any]]:
        """Create sample rooms data"""
        rooms = []
        buildings = ['Building A', 'Building B', 'Building C']
        
        room_id = 1
        for building in buildings:
            for floor in range(1, 3):
                for room_num in range(1, 6):
                    rooms.append({
                        'id': room_id,
                        'number': f"{building}-{floor}{room_num:02d}",
                        'building': building,
                        'floor': floor,
                        'capacity': 40 + (room_id % 40),
                        'room_type': ['Lecture', 'Lab', 'Studio'][(room_id-1) % 3],
                        'has_projector': room_id % 2 == 0,
                        'has_computer': room_id % 3 == 0
                    })
                    room_id += 1
        
        return rooms
    
    def create_student_groups_data(self) -> List[Dict[str, Any]]:
        """Create sample student groups data"""
        groups = []
        departments = ['CSE', 'ECE', 'Mechanical', 'Civil', 'Electrical']
        
        group_id = 1
        for dept in departments:
            for year in range(1, 5):
                for section in ['A', 'B', 'C', 'D']:
                    groups.append({
                        'id': group_id,
                        'name': f"{dept} {year}-{section}",
                        'department': dept,
                        'year': year,
                        'section': section,
                        'student_count': 40 + (group_id % 30),
                        'courses': [group_id + i for i in range(1, 4)] if group_id <= 100 else []
                    })
                    group_id += 1
        
        return groups
    
    def prepare_training_data(self) -> Dict[str, Any]:
        """Prepare complete training dataset"""
        print("Preparing training data...")
        
        training_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'constraints': self.create_sample_constraints(),
            'courses': self.create_courses_data(),
            'instructors': self.create_instructors_data(),
            'rooms': self.create_rooms_data(),
            'student_groups': self.create_student_groups_data()
        }
        
        return training_data
    
    def save_training_data(self, data: Dict[str, Any], 
                          filename: str = "training_data.json") -> str:
        """Save training data to JSON file"""
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Training data saved to {output_path}")
        print(f"Total courses: {len(data['courses'])}")
        print(f"Total instructors: {len(data['instructors'])}")
        print(f"Total rooms: {len(data['rooms'])}")
        print(f"Total student groups: {len(data['student_groups'])}")
        
        return output_path
    
    def create_validation_data(self) -> Dict[str, Any]:
        """Create validation dataset (smaller)"""
        print("Creating validation data...")
        
        validation_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'constraints': {
                'num_entries': 50,
                'num_slots': 30,
                'num_rooms': 8,
                'num_instructors': 10,
                'conflicts': 3,
                'max_hours_per_day': 8
            },
            'courses': self.create_courses_data()[:10],
            'instructors': self.create_instructors_data()[:10],
            'rooms': self.create_rooms_data()[:8],
            'student_groups': self.create_student_groups_data()[:15]
        }
        
        return validation_data
    
    def save_validation_data(self, 
                            filename: str = "validation_data.json") -> str:
        """Save validation data to JSON file"""
        validation_data = self.create_validation_data()
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(validation_data, f, indent=2)
        
        print(f"Validation data saved to {output_path}")
        return output_path


def main():
    """Main function to prepare data"""
    print("=== Training Data Preparation ===\n")
    
    preparator = TrainingDataPreparator()
    
    # Prepare and save training data
    training_data = preparator.prepare_training_data()
    training_file = preparator.save_training_data(training_data)
    
    print()
    
    # Prepare and save validation data
    validation_file = preparator.save_validation_data()
    
    print(f"\n=== Data Preparation Complete ===")
    print(f"Training data: {training_file}")
    print(f"Validation data: {validation_file}")


if __name__ == "__main__":
    main()
