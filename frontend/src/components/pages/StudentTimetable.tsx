import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Paper,
} from '@mui/material';
import { timetableService } from '../../services/timetableService';
import type { Timetable } from '../../services/timetableService';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const SLOTS = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '01:00-02:00'];

const StudentTimetable: React.FC = () => {
  const [entries, setEntries] = useState<any[]>([]);
  const [timetableTitle, setTimetableTitle] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [courseMap, setCourseMap] = useState<Record<string,string>>({});
  const [facultyMap, setFacultyMap] = useState<Record<string,string>>({});
  const [roomMap, setRoomMap] = useState<Record<string,string>>({});
  const [lunchRange, setLunchRange] = useState<{start: string; end: string}>({ start: '12:00', end: '13:30' });
  const [rawTimetable, setRawTimetable] = useState<any | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data: Timetable[] = await timetableService.getAllTimetables();
        if (!data || data.length === 0) {
          setEntries([]);
          setTimetableTitle('No timetable available');
          return;
        }

        // Use the first timetable for "My Timetable" view. In the future
        // this could be selected by the user or derived from their program.
        const first: any = data[0];
        setTimetableTitle(first.title || `${first.program_id || ''} ${first.academic_year || ''}`);

        // Extract lunch times if provided in metadata
        const meta = first.metadata || first.time_slots || {};
        if (meta?.lunch_start && meta?.lunch_end) {
          setLunchRange({ start: meta.lunch_start, end: meta.lunch_end });
        }

        const ttEntries = first.entries || [];

        // Fetch supporting data to resolve IDs -> names
        const [rooms, faculty] = await Promise.all([
          timetableService.getRooms().catch(() => []),
          timetableService.getFaculty().catch(() => []),
        ]);

        // Courses: attempt to use program-specific fetch, fall back to empty
        let courses: any[] = [];
        try {
          courses = await timetableService.getCourses(first.program_id, first.semester);
        } catch (e) {
          courses = [];
        }

        const cMap: Record<string,string> = {};
        const fMap: Record<string,string> = {};
        const rMap: Record<string,string> = {};

        (courses || []).forEach((c: any) => { cMap[c.id || c._id] = c.name || c.courseName || c.name; });
        (faculty || []).forEach((f: any) => { fMap[f.id || f._id] = f.name || f.full_name || f.name; });
        (rooms || []).forEach((r: any) => { rMap[r.id || r._id] = r.name || r.room_number || r.name; });

        setCourseMap(cMap);
        setFacultyMap(fMap);
        setRoomMap(rMap);

        console.debug('📥 Loaded timetable (raw):', first);
        console.debug('📋 Entries count:', (ttEntries || []).length);
        console.debug('🗂 courseMap keys:', Object.keys(cMap).length, 'facultyMap keys:', Object.keys(fMap).length, 'roomMap keys:', Object.keys(rMap).length);

        setRawTimetable(first);
        setEntries(ttEntries);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const timeInRange = (time: string, start: string, end: string) => {
    // time strings in HH:MM
    return time >= start && time < end;
  };

  const getCell = (day: string, slot: string) => {
    const slotStart = slot.split('-')[0];

    // Match entries that use either 'slot' or 'start_time'
    const e = entries.find((x: any) => {
      if (!x) return false;
      const entryDay = (x.day || x.DAY || '').toString().toLowerCase();
      const targetDay = day.toLowerCase();
      if (x.slot && x.slot === slot && entryDay === targetDay) return true;
      if (x.start_time && x.start_time === slotStart && entryDay === targetDay) return true;
      // Some entries may use 'day_name' or numeric day; try loose match
      if (x.day && x.day.toString().toLowerCase().includes(targetDay.substring(0,3))) return true;
      return false;
    });

    if (e) {
      const courseName = e.course_name || (e.course_id && courseMap[e.course_id]) || e.subject || e.course || '';
      const facultyName = e.faculty_name || (e.faculty_id && facultyMap[e.faculty_id]) || e.faculty || e.faculty_id || '';
      const roomName = e.room_name || (e.room_id && roomMap[e.room_id]) || e.room || e.room_number || '';
      return `${courseName}\n${facultyName}\n${roomName}`;
    }

    // If no entry, check if this slot falls in lunch range
    const lunchStart = lunchRange.start || '12:00';
    const lunchEnd = lunchRange.end || '13:30';
    if (timeInRange(slotStart, lunchStart, lunchEnd)) {
      return 'Lunch Break';
    }

    return '';
  };

  if (loading) return <Typography sx={{ p: 3 }}>Loading...</Typography>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Student – My Timetable
      </Typography>

      <Typography variant="h6" color="text.secondary" gutterBottom>
        {timetableTitle}
      </Typography>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><b>Day / Time</b></TableCell>
              {SLOTS.map(s => (
                <TableCell key={s}><b>{s}</b></TableCell>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {DAYS.map(day => (
              <TableRow key={day}>
                <TableCell><b>{day}</b></TableCell>
                {SLOTS.map(slot => (
                  <TableCell key={slot} sx={{ whiteSpace: 'pre-line' }}>
                    {getCell(day, slot)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* Debug panel to inspect raw timetable when cells are empty */}
      {(!entries || entries.length === 0) && rawTimetable && (
        <Box sx={{ mt: 3, p: 2, bgcolor: 'background.paper' }}>
          <Typography variant="subtitle1">Debug: Raw Timetable (first)</Typography>
          <pre style={{ maxHeight: 300, overflow: 'auto', color: '#ddd' }}>{JSON.stringify(rawTimetable, null, 2)}</pre>
        </Box>
      )}
    </Box>
  );
};

export default StudentTimetable;
