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

const FacultyTimetable: React.FC = () => {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const data: Timetable[] = await timetableService.getAllTimetables();

        // flatten entries
        const allEntries = data.flatMap(tt => tt.entries || []);
        setEntries(allEntries);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const getCell = (day: string, slot: string) => {
    const e = entries.find(
      x => x.day === day && x.slot === slot
    );
    return e
      ? `${e.subject}\n${e.room}\n${e.group_id}`
      : '';
  };

  if (loading) return <Typography sx={{ p: 3 }}>Loading...</Typography>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Faculty – My Timetable
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
    </Box>
  );
};

export default FacultyTimetable;
