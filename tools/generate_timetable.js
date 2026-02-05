#!/usr/bin/env node
/*
Generate a weekly timetable from user-provided JSON input.
Usage:
  node tools/generate_timetable.js input.json
Or pipe JSON via stdin.

Input format (JSON):
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
    },
    ...
  ]
}

Rules enforced:
- No hardcoded data; only use provided input.
- If inputs are missing or invalid, report validation messages and do not generate.
- No overlapping time slots for the same faculty or same course on the same day.
- Map courses exactly to the specified day/time ranges.
- If no valid entries, outputs empty timetable layout.
- The script can be re-run when input changes (real-time behavior can be implemented by the caller watching the file).
*/

const fs = require('fs');
const path = require('path');

const DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];

function parseInput(json) {
  if (!json || typeof json !== 'object') return { error: 'Input is not a JSON object' };
  const courses = Array.isArray(json.courses) ? json.courses : null;
  if (!courses) return { error: 'Missing "courses" array in input' };
  return { courses };
}

function timeToMinutes(t) {
  if (!t || typeof t !== 'string') return null;
  const m = t.match(/^(\d{1,2}):(\d{2})$/);
  if (!m) return null;
  let hh = parseInt(m[1],10);
  const mm = parseInt(m[2],10);
  if (hh < 0 || hh > 23 || mm < 0 || mm > 59) return null;
  return hh*60 + mm;
}

function rangesOverlap(aStart,aEnd,bStart,bEnd) {
  return aStart < bEnd && bStart < aEnd;
}

function validateAndBuild(coursesRaw) {
  const messages = [];
  const validEntries = [];

  coursesRaw.forEach((c, idx) => {
    const base = `courses[${idx}]`;
    if (!c || typeof c !== 'object') { messages.push(`${base} invalid`); return; }
    const course_name = (c.course_name || c.course || '').toString().trim();
    const course_code = (c.course_code || c.code || '').toString().trim();
    const faculty = (c.faculty || c.faculty_name || '').toString().trim();
    const days = Array.isArray(c.days) ? c.days.map(d=>d.toString().trim()) : (c.day? [c.day.toString().trim()]: null);
    const times = Array.isArray(c.times) ? c.times : (c.time? [c.time] : null);
    const room = (c.room || c.room_name || '').toString().trim();
    const periods = c.periods !== undefined ? Number(c.periods) : (c.period? Number(c.period): undefined);

    if (!course_name) messages.push(`${base}: missing course_name`);
    if (!course_code) messages.push(`${base}: missing course_code`);
    if (!faculty) messages.push(`${base}: missing faculty`);
    if (!days || days.length===0) messages.push(`${base}: missing days`);
    if (!times || times.length===0) messages.push(`${base}: missing times`);
    if (!room) messages.push(`${base}: missing room`);
    if (!periods || !Number.isFinite(periods) || periods<=0) messages.push(`${base}: invalid periods`);

    if (messages.length>0) return;

    // parse times for each entry
    const parsedTimes = [];
    for (let t of times) {
      if (typeof t === 'string') {
        // accept "HH:MM-HH:MM" or "HH:MM - HH:MM"
        const parts = t.split('-').map(s=>s.trim());
        if (parts.length!==2) { messages.push(`${base}: invalid time format '${t}'`); continue; }
        const smin = timeToMinutes(parts[0]);
        const emin = timeToMinutes(parts[1]);
        if (smin===null || emin===null) { messages.push(`${base}: invalid time value '${t}'`); continue; }
        if (emin <= smin) { messages.push(`${base}: end must be after start in '${t}'`); continue; }
        parsedTimes.push({start: parts[0], end: parts[1], smin, emin});
      } else if (t && typeof t === 'object' && t.start && t.end) {
        const smin = timeToMinutes(t.start);
        const emin = timeToMinutes(t.end);
        if (smin===null || emin===null) { messages.push(`${base}: invalid time value ${JSON.stringify(t)}`); continue; }
        if (emin <= smin) { messages.push(`${base}: end must be after start in ${JSON.stringify(t)}`); continue; }
        parsedTimes.push({start: t.start, end: t.end, smin, emin});
      } else {
        messages.push(`${base}: unsupported times entry ${JSON.stringify(t)}`);
      }
    }

    if (parsedTimes.length===0) return;

    // Validate day names and expand days to canonical forms
    const canonicalDays = [];
    for (let d of days) {
      if (!d) continue;
      const found = DAYS.find(dd => dd.toLowerCase() === d.toLowerCase());
      if (!found) { messages.push(`${base}: invalid day '${d}'`); continue; }
      canonicalDays.push(found);
    }
    if (canonicalDays.length===0) return;

    // Build entry(s) - one per day per time
    for (let day of canonicalDays) {
      for (let t of parsedTimes) {
        validEntries.push({
          course_name, course_code, faculty, day, start: t.start, end: t.end, smin: t.smin, emin: t.emin, room, periods
        });
      }
    }
  });

  // Now check overlaps: for same day, same faculty or same course should not overlap
  const errors = [];
  const byDay = {};
  validEntries.forEach((e, i) => {
    byDay[e.day] = byDay[e.day] || [];
    byDay[e.day].push({...e, _idx:i});
  });

  for (let day of Object.keys(byDay)) {
    const arr = byDay[day];
    // compare all pairs
    for (let i=0;i<arr.length;i++){
      for (let j=i+1;j<arr.length;j++){
        const a = arr[i], b = arr[j];
        if (rangesOverlap(a.smin,a.emin,b.smin,b.emin)) {
          if (a.faculty === b.faculty) {
            errors.push(`Overlap on ${day} for faculty '${a.faculty}': ${a.course_code} ${a.start}-${a.end} overlaps ${b.course_code} ${b.start}-${b.end}`);
          }
          if (a.course_code === b.course_code) {
            errors.push(`Overlap on ${day} for course '${a.course_code}': ${a.start}-${a.end} overlaps ${b.start}-${b.end}`);
          }
        }
      }
    }
  }

  return { messages, errors, validEntries };
}

function buildTimetable(entries) {
  const tt = {};
  DAYS.forEach(d=> tt[d] = []);
  entries.forEach(e => {
    tt[e.day].push({ course_name: e.course_name, course_code: e.course_code, faculty: e.faculty, room: e.room, start: e.start, end: e.end, periods: e.periods });
  });
  // sort each day by start time
  for (let d of Object.keys(tt)) {
    tt[d].sort((a,b)=> timeToMinutes(a.start) - timeToMinutes(b.start));
  }
  return tt;
}

function prettyPrintTimetable(tt) {
  console.log('\n--- Generated Timetable ---\n');
  for (let day of DAYS) {
    const entries = tt[day] || [];
    console.log(day + ':');
    if (entries.length===0) { console.log('  [empty]\n'); continue; }
    for (let e of entries) {
      console.log(`  ${e.start}-${e.end} | ${e.course_code} | ${e.course_name} | ${e.faculty} | ${e.room}`);
    }
    console.log('');
  }
}

// Runner
(async function main(){
  try {
    let raw = null;
    const arg = process.argv[2];
    if (arg && fs.existsSync(arg)) {
      raw = fs.readFileSync(arg,'utf8');
    } else {
      // try stdin
      const stat = fs.fstatSync(0);
      if (!stat.isTTY) {
        raw = fs.readFileSync(0,'utf8');
      }
    }

    if (!raw) {
      console.error('No input provided. Provide a path to a JSON file or pipe JSON via stdin.');
      process.exit(2);
    }

    let json = null;
    try { json = JSON.parse(raw); } catch (err) { console.error('Failed to parse JSON:', err.message); process.exit(2); }

    const parsed = parseInput(json);
    if (parsed.error) { console.error('Input error:', parsed.error); process.exit(2); }

    const result = validateAndBuild(parsed.courses);
    if (result.messages && result.messages.length>0) {
      console.error('Validation messages:');
      result.messages.forEach(m=> console.error(' -', m));
    }
    if (result.errors && result.errors.length>0) {
      console.error('Validation errors (overlaps / conflicts):');
      result.errors.forEach(m=> console.error(' -', m));
      process.exit(3);
    }

    const tt = buildTimetable(result.validEntries || []);

    // If no valid entries, return empty layout
    const hasAny = Object.values(tt).some(arr=>arr.length>0);
    if (!hasAny) {
      console.log(JSON.stringify({ timetable: tt, message: 'No valid entries to generate timetable' }, null, 2));
      process.exit(0);
    }

    // Output JSON and pretty print
    console.log(JSON.stringify({ timetable: tt, message: 'OK' }, null, 2));
    prettyPrintTimetable(tt);
    process.exit(0);
  } catch (err) {
    console.error('Unexpected error:', err && err.stack ? err.stack : String(err));
    process.exit(1);
  }
})();
