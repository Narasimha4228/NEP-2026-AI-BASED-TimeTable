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
  Alert,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
} from '@mui/material';
import { timetableService } from '../../services/timetableService';
import { useAuthStore } from '../../store/authStore';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const SLOTS = [
  { label: '09:00-10:00', start: '09:00' },
  { label: '10:00-11:00', start: '10:00' },
  { label: '11:00-12:00', start: '11:00' },
  { label: '01:00-02:00', start: '01:00' },
];

const StudentTimetable: React.FC = () => {
  const [entries, setEntries] = useState<any[]>([]);
  const [timetableTitle, setTimetableTitle] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [filterLoading, setFilterLoading] = useState(false);
  const [rawTimetable, setRawTimetable] = useState<any | null>(null);
  const [department, setDepartment] = useState<string | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [section, setSection] = useState<string | null>(null);
  const [semester, setSemester] = useState<string | number | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [availableTimetables, setAvailableTimetables] = useState<any[]>([]);
  const [selectedTimetableId, setSelectedTimetableId] = useState<string | null>(null);

  // Filter options and selections
  const [filterOptions, setFilterOptions] = useState<any>({
    programs: [],
    years: [],
    semesters: [],
    sections: [],
  });
  const [selectedProgram, setSelectedProgram] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<number | string>('');
  const [selectedSemester, setSelectedSemester] = useState<string>('');
  const [selectedSection, setSelectedSection] = useState<string>('');

  useEffect(() => {
    const load = async () => {
      try {
        console.log('📥 StudentTimetable: Starting load...');
        const currentUser = useAuthStore.getState().user;
        const token = useAuthStore.getState().token;
        console.log('📥 StudentTimetable: Current user:', currentUser);
        console.log('📥 StudentTimetable: Token present:', !!token);

        // Fetch filter options in parallel
        const optionsPromise = timetableService.getFilterOptions()
          .then(opts => {
            console.log('✅ Filter options loaded:', opts);
            setFilterOptions(opts);
          })
          .catch(err => {
            console.warn('⚠️ Failed to load filter options:', err);
          });

        // Load all available timetables for browsing
        const timetablesData = await timetableService.listAllTimetables();
        console.log('✅ Available timetables loaded:', timetablesData);
        const timetables = timetablesData?.timetables || [];
        setAvailableTimetables(timetables);
        
        // Auto-select and load the first available timetable
        if (timetables.length > 0) {
          const firstTimetable = timetables[0];
          console.log('🔄 Auto-loading first timetable:', firstTimetable);
          
          try {
            const fullTimetable = await timetableService.getTimetableById(firstTimetable.id);
            const entriesArray = fullTimetable?.entries ? 
              (Array.isArray(fullTimetable.entries) ? fullTimetable.entries : [fullTimetable.entries]) : [];
            
            setSelectedTimetableId(firstTimetable.id);
            setEntries(entriesArray);
            setRawTimetable(fullTimetable);
            setTimetableTitle(`Timetable - ${fullTimetable.title || firstTimetable.department_code}`);
            if (fullTimetable.department_code) setDepartment(fullTimetable.department_code);
            if (fullTimetable.semester) setSemester(fullTimetable.semester);
            
            console.log('✅ First timetable loaded with', entriesArray.length, 'entries');
            await optionsPromise;
            setLoading(false);
            return;
          } catch (err: any) {
            console.warn('⚠️ Failed to load first timetable:', err);
          }
        }

        // Fallback: Use the student-specific endpoint if available timetables fail
        const response = await timetableService.getMyTimetable();
        const data = response;
        console.log('📥 StudentTimetable: /timetable/my API returned:', data);
        console.log('📥 Entries count:', data?.entries?.length || 0);
        if (data?.entries && data.entries.length > 0) {
          console.log('📥 First entry sample:', data.entries[0]);
        }

        // New endpoint returns: { department, year, section, semester, timetable_id, entries }
        // Check if we have valid entries
        const entriesArray = data?.entries ? (Array.isArray(data.entries) ? data.entries : [data.entries]) : [];
        if (!entriesArray || entriesArray.length === 0) {
          console.warn('⚠️ No valid entries in initial load:', { hasData: !!data, hasEntries: !!data?.entries, isArray: Array.isArray(data?.entries), length: entriesArray?.length });
          setEntries([]);
          setTimetableTitle('No timetable available');
          setDepartment(null);
          setYear(null);
          setSection(null);
          setSemester(null);
          await optionsPromise;
          setLoading(false);
          return;
        }

        // Extract and set metadata
        setDepartment(data.department);
        setYear(data.year);
        setSection(data.section);
        setSemester(data.semester);
        setRawTimetable(data);
        setTimetableTitle('My Timetable');
        setEntries(entriesArray);

        // Pre-fill filter selections with student's current assignment
        // Use department_code directly from response instead of mapping through programs
        if (data.department_code || data.department) {
          const deptCode = data.department_code || data.department;
          setSelectedProgram(deptCode);  // department_code is the value
        }
        if (data.year) setSelectedYear(data.year);
        if (data.semester) setSelectedSemester(String(data.semester));
        if (data.section) setSelectedSection(data.section);

        // Wait for filter options to be set
        await optionsPromise;
      } catch (err: any) {
        console.error('❌ StudentTimetable load error:', err);
        let errorMsg = 'Unknown error';
        if (err.response?.status === 400) {
          errorMsg = `Bad Request (400): ${err.response?.data?.detail || err.message}`;
        } else if (err.response?.status === 401) {
          errorMsg = `Unauthorized (401): Token may be invalid or expired`;
        } else if (err.response?.status === 404) {
          errorMsg = `Not Found (404): Endpoint not available`;
        } else if (err.message) {
          errorMsg = err.message;
        }
        setApiError(errorMsg);
        setTimetableTitle('Error loading timetable');
        setEntries([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Fetch timetable by ID (when clicking an available timetable button)
  const handleSelectTimetable = async (timetableId: string) => {
    setFilterLoading(true);
    setApiError(null);
    try {
      console.log('📥 Fetching timetable by ID:', timetableId);
      const timetable = await timetableService.getTimetableById(timetableId);
      
      console.log('📦 Fetched timetable:', timetable);
      
      if (!timetable) {
        throw new Error('Timetable not found');
      }

      // Extract entries from timetable
      const entriesArray = timetable?.entries ? 
        (Array.isArray(timetable.entries) ? timetable.entries : [timetable.entries]) : [];
      
      console.log('✅ Timetable entries:', entriesArray.length);

      // Set state with fetched timetable data
      setSelectedTimetableId(timetableId);
      setEntries(entriesArray);
      setRawTimetable(timetable);
      setTimetableTitle(`Timetable - ${timetable.title || 'Selected'}`);
      
      // Update metadata if available
      if (timetable.department_code) setDepartment(timetable.department_code);
      if (timetable.semester) setSemester(timetable.semester);
      
      console.log('✅ Timetable loaded successfully with', entriesArray.length, 'entries');
    } catch (err: any) {
      console.error('❌ Error fetching timetable:', err);
      let errorMsg = 'Failed to load timetable';
      if (err.response?.status === 404) {
        errorMsg = 'Timetable not found';
      } else if (err.message) {
        errorMsg = err.message;
      }
      setApiError(errorMsg);
      setEntries([]);
    } finally {
      setFilterLoading(false);
    }
  };

  // Handle filter change - fetch filtered timetable
  const handleFilterChange = async () => {
    setFilterLoading(true);
    try {
      const filters: any = {};
      if (selectedProgram) filters.department_code = selectedProgram;  // Use department_code instead of program_id
      if (selectedYear) filters.year = Number(selectedYear);
      if (selectedSemester) filters.semester = selectedSemester;
      if (selectedSection) filters.section = selectedSection;

      console.log('🔍 Filtering timetable with:', filters);
      const response = await timetableService.filterTimetables(filters);
      const data = response;

      console.log('📥 Filter response:', data);
      console.log('📥 Filter response type:', typeof data);
      console.log('📥 Filter response is Array?:', Array.isArray(data));
      console.log('📥 Filter response constructor:', data?.constructor?.name);
      console.log('📥 Filtered entries count:', data?.entries?.length || 0);
      if (data?.entries && data.entries.length > 0) {
        console.log('📥 First filtered entry sample:', data.entries[0]);
      }

      // Check if we have valid entries
      console.log('🔍 DEBUG: data?.entries exists?', !!data?.entries);
      console.log('🔍 DEBUG: Array.isArray(data?.entries)?', Array.isArray(data?.entries));
      console.log('🔍 DEBUG: data?.entries value:', data?.entries);
      
      const entriesArray = data?.entries ? (Array.isArray(data.entries) ? data.entries : [data.entries]) : [];
      console.log('🔍 DEBUG: entriesArray after processing:', entriesArray);
      console.log('🔍 DEBUG: entriesArray.length:', entriesArray.length);
      
      if (!entriesArray || entriesArray.length === 0) {
        console.warn('⚠️ No valid entries in filter response:', { hasData: !!data, hasEntries: !!data?.entries, isArray: Array.isArray(data?.entries), length: entriesArray?.length });
        console.log('⚠️ Storing rawTimetable for debugging:', data);
        setEntries([]);
        setRawTimetable(data); // Set rawTimetable even if no entries
        setTimetableTitle('No timetable available for selected filters');
        setDepartment(null);
        setYear(null);
        setSection(null);
        setSemester(null);
        setApiError(null);
        return;
      }

      // Update display with filtered timetable
      console.log('✅ Setting entries from filter response');
      console.log('✅ Setting entries count:', entriesArray.length);
      setDepartment(data.department_code || data.department || null);
      setYear(data.year);
      setSection(data.section);
      setSemester(data.semester);
      setRawTimetable(data);
      setTimetableTitle('Filtered Timetable');
      setEntries(entriesArray);
      setApiError(null);
    } catch (err: any) {
      console.error('❌ Filter error:', err);
      let errorMsg = 'Failed to filter timetable';
      if (err.response?.status === 404) {
        errorMsg = 'No timetable found for selected filters';
      } else if (err.message) {
        errorMsg = err.message;
      }
      setApiError(errorMsg);
      setEntries([]);
    } finally {
      setFilterLoading(false);
    }
  };

  const timeInRange = (time: string, start: string, end: string) => {
    return time >= start && time < end;
  };

  const getCell = (day: string, slot: { label: string; start: string }) => {
    // Find all entries matching this day and time slot
    const matchingEntries = entries.filter((entry: any) => {
      if (!entry) return false;

      // Normalize and compare day - handle both full names and abbreviations
      const entryDay = (entry.day || '').toString().toLowerCase().trim();
      const targetDay = day.toLowerCase().trim();
      
      // Direct match or abbreviation match
      const dayMatches = entryDay === targetDay || 
        (entryDay.length <= 3 && targetDay.startsWith(entryDay)) ||
        (entryDay.length > 3 && entryDay.startsWith(targetDay));
      
      if (!dayMatches) return false;

      // Get entry start time (handle multiple possible field names)
      const entStart = (entry.start_time || entry.start || '').toString().trim();
      
      console.log(`Checking entry: day="${entry.day}" (${entryDay}) vs "${day}" (${targetDay}), time="${entStart}" vs "${slot.start}"`);
      
      // Check if entry start time matches the slot start time
      if (entStart === slot.start) return true;

      return false;
    });

    // Render matched entry
    if (matchingEntries.length > 0) {
      const entry = matchingEntries[0];
      const courseName = entry.course_name || entry.course || '';
      const facultyName = entry.faculty || entry.faculty_name || '';
      const roomName = entry.room || entry.room_name || '';

      console.log('✅ Rendering entry:', courseName);

      return (
        <Box sx={{ fontSize: '0.75rem', lineHeight: 1.3 }}>
          <Typography variant="caption" sx={{ fontWeight: 600, display: 'block' }}>
            {courseName}
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', color: '#666' }}>
            {facultyName}
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', color: '#999' }}>
            {roomName}
          </Typography>
        </Box>
      );
    }

    // Check for lunch break
    const lunchStart = '12:00';
    const lunchEnd = '13:30';
    if (timeInRange(slot.start, lunchStart, lunchEnd)) {
      return (
        <Typography variant="caption" sx={{ color: '#ff9800', fontStyle: 'italic' }}>
          LUNCH BREAK
        </Typography>
      );
    }

    // Empty cell
    return null;
  };

  if (loading) return <Typography sx={{ p: 3 }}>Loading...</Typography>;

  return (
    <Box sx={{ p: 3 }}>
      {apiError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="subtitle2">❌ API Error:</Typography>
          <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace', fontSize: '0.85rem' }}>
            {apiError}
          </Typography>
        </Alert>
      )}

      {/* Timetable conflict warning hidden as requested */}
      <Typography variant="h4" gutterBottom>
        Student – My Timetable
      </Typography>

      <Typography variant="h6" color="text.secondary" gutterBottom>
        {timetableTitle}
      </Typography>

      {/* Display timetable metadata clearly */}
      {(department || year || section || semester) && (
        <Box sx={{ 
          mb: 3, 
          p: 2, 
          bgcolor: '#f5f5f5', 
          borderRadius: 1,
          border: '1px solid #ddd'
        }}>
          <Stack direction="row" spacing={3} flexWrap="wrap">
            {department && (
              <Box>
                <Typography variant="subtitle2" color="textSecondary">Department</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>{department}</Typography>
              </Box>
            )}
            {year && (
              <Box>
                <Typography variant="subtitle2" color="textSecondary">Year</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>{year}</Typography>
              </Box>
            )}
            {section && (
              <Box>
                <Typography variant="subtitle2" color="textSecondary">Section</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>{section}</Typography>
              </Box>
            )}
            {semester && (
              <Box>
                <Typography variant="subtitle2" color="textSecondary">Semester</Typography>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>{semester}</Typography>
              </Box>
            )}
          </Stack>
        </Box>
      )}

      {/* Filter Controls */}
      <Box sx={{ mb: 3, p: 2, bgcolor: '#fff3cd', borderRadius: 1, border: '1px solid #ffc107' }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          📋 Select a Different Timetable
        </Typography>
        <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Department</InputLabel>
            <Select
              value={selectedProgram}
              onChange={(e) => setSelectedProgram(e.target.value)}
              label="Department"
              disabled={filterLoading}
            >
              <MenuItem value="">-- Select Department --</MenuItem>
              {(filterOptions.programs || []).map((prog: any) => (
                <MenuItem key={prog.code} value={prog.code}>
                  {prog.code} - {prog.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Year</InputLabel>
            <Select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              label="Year"
              disabled={filterLoading}
            >
              <MenuItem value="">-- Select Year --</MenuItem>
              {(filterOptions.years || []).map((yr: number) => (
                <MenuItem key={yr} value={yr}>
                  Year {yr}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Semester</InputLabel>
            <Select
              value={selectedSemester}
              onChange={(e) => setSelectedSemester(e.target.value)}
              label="Semester"
              disabled={filterLoading}
            >
              <MenuItem value="">-- Select Semester --</MenuItem>
              {(filterOptions.semesters || []).map((sem: string) => (
                <MenuItem key={sem} value={sem}>
                  {sem}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Section</InputLabel>
            <Select
              value={selectedSection}
              onChange={(e) => setSelectedSection(e.target.value)}
              label="Section"
              disabled={filterLoading}
            >
              <MenuItem value="">-- Select Section --</MenuItem>
              {(filterOptions.sections || []).map((sec: string) => (
                <MenuItem key={sec} value={sec}>
                  {sec}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {filterLoading ? (
              <CircularProgress size={40} />
            ) : (
              <Typography
                variant="body2"
                sx={{
                  color: '#666',
                  p: 1,
                  bgcolor: 'white',
                  borderRadius: 1,
                  border: '1px solid #ddd',
                  cursor: 'pointer',
                  '&:hover': { bgcolor: '#f0f0f0' },
                }}
                onClick={handleFilterChange}
              >
                🔍 Search Timetable
              </Typography>
            )}
          </Box>
        </Stack>
      </Box>

      {/* Browse All Available Timetables */}
      {availableTimetables.length > 0 && (
        <Box sx={{ mb: 3, p: 2, bgcolor: '#e3f2fd', borderRadius: 1, border: '1px solid #2196f3' }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            📚 Available Timetables
          </Typography>
          <Typography variant="body2" sx={{ mb: 2, color: '#666' }}>
            Click on any timetable to view its schedule
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
            {availableTimetables.map((tt: any) => (
              <Typography
                key={tt.id}
                variant="body2"
                sx={{
                  p: 1,
                  bgcolor: selectedTimetableId === tt.id ? '#2196f3' : 'white',
                  color: selectedTimetableId === tt.id ? 'white' : 'inherit',
                  borderRadius: 1,
                  border: `2px solid ${selectedTimetableId === tt.id ? '#2196f3' : '#2196f3'}`,
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                  fontWeight: selectedTimetableId === tt.id ? 600 : 400,
                  '&:hover': { 
                    bgcolor: '#2196f3', 
                    color: 'white',
                    boxShadow: '0 2px 8px rgba(33,150,243,0.3)'
                  },
                }}
                onClick={() => handleSelectTimetable(tt.id)}
              >
                {tt.department_code} - Semester {tt.semester} ({tt.entries_count} courses)
              </Typography>
            ))}
          </Stack>
        </Box>
      )}

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><b>Day / Time</b></TableCell>
              {SLOTS.map(slot => (
                <TableCell key={slot.start}><b>{slot.label}</b></TableCell>
              ))}
            </TableRow>
          </TableHead>

          <TableBody>
            {DAYS.map(day => (
              <TableRow key={day}>
                <TableCell><b>{day}</b></TableCell>
                {SLOTS.map(slot => (
                  <TableCell 
                    key={slot.start} 
                    sx={{ 
                      whiteSpace: 'normal',
                      verticalAlign: 'top',
                      minHeight: '80px',
                      borderLeft: '1px solid #ddd',
                      padding: '8px',
                      backgroundColor: getCell(day, slot) ? '#f9f9f9' : 'white',
                    }}
                  >
                    {getCell(day, slot)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* Show debug info ONLY if entries are truly empty */}
      {(!entries || entries.length === 0) && (
        <Box sx={{ mt: 3, p: 2, bgcolor: '#fff3e0', borderRadius: 1, border: '1px solid #ffb74d' }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>ℹ️ Debug Info: No Entries Loaded</Typography>
          <Typography variant="body2" sx={{ mb: 1, color: '#666' }}>
            No timetable entries available. 
          </Typography>
          {rawTimetable && (
            <Box>
              <Typography variant="body2" sx={{ mt: 1, fontWeight: 500 }}>
                Reason: {rawTimetable?.message || 'NONE'}
              </Typography>
              <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#999' }}>
                Timetable: {rawTimetable?.timetable ? 'Found' : 'NONE'}
              </Typography>
              <Typography variant="caption" sx={{ display: 'block', color: '#999' }}>
                Entries: {rawTimetable?.entries?.length || 'NONE'}
              </Typography>
            </Box>
          )}
        </Box>
      )}

      {/* Show success message ONLY when entries are loaded and being rendered */}
      {entries && entries.length > 0 && (
        <Box sx={{ mt: 2, p: 1, bgcolor: '#e8f5e9', borderRadius: 1, border: '1px solid #4caf50' }}>
          <Typography variant="caption" sx={{ color: '#2e7d32' }}>
            ✅ Timetable loaded with {entries.length} entries
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default StudentTimetable;
