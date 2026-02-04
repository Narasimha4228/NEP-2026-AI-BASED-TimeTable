import asyncio
import json
import os
import sys

# ensure the backend package root is importable when running this script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.genetic_algorithm.genetic_timetable_generator import GeneticTimetableGenerator

BASE = os.path.join(os.path.dirname(__file__), '..', 'sample_data')
BASE = os.path.abspath(BASE)


def load(fname):
    with open(os.path.join(BASE, fname), 'r', encoding='utf-8') as f:
        return json.load(f)


async def main():
    faculties = load('faculty.json')
    courses = load('courses.json')
    rooms = load('rooms.json')
    student_groups = load('student_groups.json')

    gen = GeneticTimetableGenerator(
        test_mode=True,
        faculties=faculties,
        courses=courses,
        rooms=rooms,
        student_groups=student_groups,
    )

    result = await gen.generate_timetable()

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
