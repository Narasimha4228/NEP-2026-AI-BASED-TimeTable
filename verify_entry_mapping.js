#!/usr/bin/env node
/**
 * Verify that timetable entries map correctly to table cells
 * This simulates the React getCell() logic
 */

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const SLOTS = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '01:00-02:00'];

// Sample entries from backend (matching test data format)
const sampleEntries = [
  {
    "group_id": "6971b4b3d91cfa375761779f",
    "course_code": "CS101",
    "course_name": "Programming Fundamentals",
    "faculty": "Dr. Smith",
    "day": "Monday",
    "start_time": "09:00",
    "end_time": "10:00",
    "room": "Room 101",
    "is_lab": false
  },
  {
    "group_id": "6971b4b3d91cfa375761779f",
    "course_code": "CS102",
    "course_name": "Data Structures",
    "faculty": "Dr. Johnson",
    "day": "Monday",
    "start_time": "10:00",
    "end_time": "11:00",
    "room": "Room 102",
    "is_lab": false
  },
  {
    "group_id": "6971b4b3d91cfa375761779f",
    "course_code": "CS103",
    "course_name": "Database Design",
    "faculty": "Dr. Williams",
    "day": "Wednesday",
    "start_time": "09:00",
    "end_time": "10:00",
    "room": "Room 103",
    "is_lab": true
  },
];

// Simulate getCell() logic
function getCell(day, slot) {
  const slotStart = slot.split('-')[0].trim();

  const matchingEntries = sampleEntries.filter((entry) => {
    if (!entry) return false;

    const entryDay = (entry.day || '').toString().toLowerCase().trim();
    const targetDay = day.toLowerCase().trim();

    if (entryDay !== targetDay) return false;

    const entStart = (entry.start_time || entry.start || '').toString().trim();

    if (entStart === slotStart) return true;

    return false;
  });

  if (matchingEntries.length > 0) {
    const entry = matchingEntries[0];
    const courseName = entry.course_name || entry.course || '';
    const facultyName = entry.faculty || entry.faculty_name || '';
    const roomName = entry.room || entry.room_name || '';

    return {
      course: courseName,
      faculty: facultyName,
      room: roomName,
      type: 'entry'
    };
  }

  return null;
}

// Print timetable
console.log('\n' + '='.repeat(80));
console.log('TIMETABLE GRID VERIFICATION');
console.log('='.repeat(80) + '\n');

console.log('Sample Entries:');
sampleEntries.forEach((entry, idx) => {
  console.log(`  [${idx}] ${entry.day} ${entry.start_time}-${entry.end_time}: ${entry.course_name} @ ${entry.room}`);
});

console.log('\n' + '-'.repeat(80));
console.log('RENDERED GRID:');
console.log('-'.repeat(80) + '\n');

// Print header
process.stdout.write('DAY/TIME'.padEnd(15));
SLOTS.forEach(slot => {
  process.stdout.write(slot.padEnd(20));
});
console.log('\n' + '-'.repeat(80));

// Print rows
DAYS.forEach(day => {
  process.stdout.write(day.padEnd(15));
  SLOTS.forEach(slot => {
    const cell = getCell(day, slot);
    if (cell) {
      const text = `${cell.course} (${cell.faculty})`;
      process.stdout.write(text.substring(0, 18).padEnd(20));
    } else {
      process.stdout.write('[empty]'.padEnd(20));
    }
  });
  console.log();
});

console.log('\n' + '='.repeat(80));
console.log('✅ Mapping verification complete');
console.log('='.repeat(80) + '\n');
