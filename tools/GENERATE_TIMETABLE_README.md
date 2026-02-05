Generate Timetable CLI

Usage

  node tools/generate_timetable.js path/to/input.json

Or pipe JSON:

  cat input.json | node tools/generate_timetable.js

Input format example (JSON):

{
  "courses": [
    {
      "course_name": "Probability and Statistics",
      "course_code": "PCCAILM501A",
      "faculty": "dr-jahangir-chowdhury",
      "days": ["Tuesday","Thursday"],
      "times": [{"start":"10:00","end":"10:50"}],
      "room": "theory-classroom-n009",
      "periods": 1
    }
  ]
}

Behavior and rules

- The script uses ONLY the provided input; no hardcoded timetable data is added.
- If required fields are missing, the script prints validation messages and will not generate a timetable.
- Overlapping time slots for the same faculty or same course on the same day are treated as validation errors.
- Each course is placed at the exact day/time(s) provided.
- If there are no valid entries, the script returns an empty timetable layout.
- To emulate real-time updates, re-run the script whenever the input JSON is modified (or integrate into a file watcher).

Exit codes

- 0: success (timetable generated or empty layout returned)
- 2: input/parse error
- 3: validation errors (overlaps/conflicts)
- 1: unexpected error
