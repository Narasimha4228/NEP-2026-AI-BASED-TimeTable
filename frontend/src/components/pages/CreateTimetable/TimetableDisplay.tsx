import React, { useState, useEffect, type ErrorInfo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Stack,
  Card,
  CardContent,
} from '@mui/material';
import {
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
} from '@mui/icons-material';
import { timetableService } from '../../../services/timetableService';
import { useTimetableContext } from '../../../contexts/TimetableContext';

interface TimetableEntry {
  day: string;
  time: string;
  course_name: string;
  course_code: string;
  group: string;
  room: string;
  faculty: string;
  is_lab: boolean;
  duration: number;
}

interface Course {
  id?: string;
  _id?: string;
  name?: string;
  code?: string;
  type?: string;
  course_type?: string;
}

interface Faculty {
  id?: string;
  _id?: string;
  name?: string;
}

interface TimeSlot {
  start_time: string;
  end_time: string;
  day: string;
  duration_minutes?: number;
}

interface TimetableEntryData {
  course_id: string;
  faculty_id: string;
  group_id?: string;
  room_id: string;
  time_slot: TimeSlot;
  course_name?: string;
  course_code?: string;
}

interface CourseInfo {
  name: string;
  code: string;
  periods: number;
  faculty: string;
  type: string;
}

interface TimetableDisplayProps {
  timetableData: {
    entries?: TimetableEntryData[];
    timetable?: {
      entries?: TimetableEntryData[];
      metadata?: {
        schedule_details?: unknown[];
      };
      academic_year?: string;
    };
    generation_details?: {
      score?: string | number;
      statistics?: {
        total_sessions?: number;
        lab_sessions?: number;
        theory_sessions?: number;
      };
    };
    [key: string]: unknown;
  };
  onExport: (format: 'csv' | 'pdf') => void;
}

const TimetableDisplay: React.FC<TimetableDisplayProps> = ({ timetableData, onExport }) => {
  console.log('🔍 TimetableDisplay component rendered with data:', timetableData);
  if (timetableData?.entries) {
    console.log('  ✓ Has entries directly:', timetableData.entries.length);
    if (timetableData.entries.length > 0) {
      console.log('  First entry:', timetableData.entries[0]);
    }
  }
  if (timetableData?.timetable?.entries) {
    console.log('  ✓ Has timetable.entries:', timetableData.timetable.entries.length);
  }
  console.log('🔍 TimetableData keys:', Object.keys(timetableData || {}));
  console.log('🔍 TimetableData.entries:', timetableData?.entries);
  console.log('🔍 TimetableData.timetable?.entries:', timetableData?.timetable?.entries);
  console.log('🔍 TimetableData structure check:', {
    hasEntries: !!timetableData?.entries,
    hasTimetableEntries: !!timetableData?.timetable?.entries,
    entriesLength: timetableData?.entries?.length || 0,
    timetableEntriesLength: timetableData?.timetable?.entries?.length || 0
  });
  const { formData } = useTimetableContext();
  const [courses, setCourses] = useState<{ [key: string]: Course }>({});
  const [faculty, setFaculty] = useState<{ [key: string]: Faculty }>({});
  const [loading, setLoading] = useState(false); // Start with false since we don't need it to load before rendering

  // Catch any errors during rendering
  if (!timetableData) {
    return (
      <Box sx={{ p: 3, textAlign: 'center', backgroundColor: '#f5f5f5', borderRadius: 2 }}>
        <Typography variant="h6" color="error">
          ⚠️ No timetable data provided
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, color: '#666' }}>
          Please generate a timetable first.
        </Typography>
      </Box>
    );
  }

  // Generate time slots dynamically from context data
  const generateTimeSlots = () => {
    try {
      const { time_slots } = formData;
      const slots: string[] = [];
      
      // Defensive checks - provide fallback values
      if (!time_slots) {
        console.warn('⚠️ time_slots not configured, using defaults');
        return ['09:00 - 10:00', '10:00 - 11:00', '11:00 - 12:00', '12:00 - 13:00', '14:00 - 15:00', '15:00 - 16:00'];
      }

      // Parse start and end times with fallbacks
      const startTime = time_slots.start_time || '09:00';
      const endTime = time_slots.end_time || '17:00';
      const slotDuration = time_slots.slot_duration || 50;
      const breakDuration = time_slots.break_duration || 10;
      
      // Convert time string to minutes
      const timeToMinutes = (timeStr: string | undefined): number => {
        if (!timeStr) return 9 * 60; // Default to 09:00
        const parts = timeStr.split(':');
        const hours = parseInt(parts[0]) || 9;
        const minutes = parseInt(parts[1]) || 0;
        return hours * 60 + minutes;
      };
      
      // Convert minutes to time string
      const minutesToTime = (minutes: number) => {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
      };
      
      let currentTime = timeToMinutes(startTime);
      const endTimeMinutes = timeToMinutes(endTime);
      const lunchStartMinutes = time_slots.lunch_break && time_slots.lunch_start ? timeToMinutes(time_slots.lunch_start) : null;
      const lunchEndMinutes = time_slots.lunch_break && time_slots.lunch_end ? timeToMinutes(time_slots.lunch_end) : null;
      
      while (currentTime + slotDuration <= endTimeMinutes) {
        const slotStart = minutesToTime(currentTime);
        const slotEnd = minutesToTime(currentTime + slotDuration);
        
        // Skip lunch break time
        if (lunchStartMinutes && lunchEndMinutes && 
            currentTime < lunchEndMinutes && currentTime + slotDuration > lunchStartMinutes) {
          currentTime = lunchEndMinutes;
          continue;
        }
        
        slots.push(`${slotStart} - ${slotEnd}`);
        currentTime += slotDuration + breakDuration;
      }
      
      return slots.length > 0 ? slots : ['09:00 - 10:00', '10:00 - 11:00', '11:00 - 12:00'];
    } catch (error) {
      console.error('❌ Error generating time slots:', error);
      return ['09:00 - 10:00', '10:00 - 11:00', '11:00 - 12:00', '12:00 - 13:00', '14:00 - 15:00', '15:00 - 16:00'];
    }
  };

  // Generate working days dynamically from context data
  const generateWorkingDays = () => {
    try {
      const { working_days } = formData;
      
      // Defensive check
      if (!working_days) {
        console.warn('⚠️ working_days not configured, using defaults');
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
      }

      const dayMapping = {
        monday: 'Monday',
        tuesday: 'Tuesday',
        wednesday: 'Wednesday',
        thursday: 'Thursday',
        friday: 'Friday',
        saturday: 'Saturday',
        sunday: 'Sunday'
      };
      
      const result = Object.entries(working_days)
        .filter(([, enabled]) => enabled)
        .map(([day]) => dayMapping[day as keyof typeof dayMapping])
        .filter(Boolean);
      
      return result.length > 0 ? result : ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    } catch (error) {
      console.error('❌ Error generating working days:', error);
      return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    }
  };

  // Generate fallback time slots and days
  const fallbackTimeSlots = generateTimeSlots();
  const days = generateWorkingDays();
  
  // Debug logging
  console.log('📅 Generated working days:', days);
  console.log('📊 Form data time_slots:', formData.time_slots);
  console.log('📊 Timetable data:', timetableData);

  // Map backend day names to frontend day names (comprehensive mapping)
  const dayNameMapping: { [key: string]: string } = {
    'Mon': 'Monday',
    'Tue': 'Tuesday', 
    'Wed': 'Wednesday',
    'Thu': 'Thursday',
    'Fri': 'Friday',
    'Sat': 'Saturday',
    'Sun': 'Sunday',
    'Monday': 'Monday',
    'Tuesday': 'Tuesday',
    'Wednesday': 'Wednesday', 
    'Thursday': 'Thursday',
    'Friday': 'Friday',
    'Saturday': 'Saturday',
    'Sunday': 'Sunday'
  };

  // Fetch courses and faculty data
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch courses and faculty to populate lookup tables
        // This is optional - if not available, we'll just show course codes
        const coursesData = await timetableService.getCourses();
        const coursesMap: { [key: string]: Course } = {};
        coursesData.forEach((course: Course) => {
          const courseId = course.id || course._id;
          if (courseId) {
            coursesMap[courseId] = course;
            if (course._id && course._id !== courseId) {
              coursesMap[course._id] = course;
            }
          }
        });
        setCourses(coursesMap);
        
        const facultyData = await timetableService.getFaculty();
        const facultyMap: { [key: string]: Faculty } = {};
        facultyData.forEach((member: Faculty) => {
          const facultyId = member.id || member._id;
          if (facultyId) {
            facultyMap[facultyId] = member;
            if (member._id && member._id !== facultyId) {
              facultyMap[member._id] = member;
            }
          }
        });
        setFaculty(facultyMap);
        
        console.log('📚 Loaded courses:', coursesMap);
        console.log('👨‍🏫 Loaded faculty:', facultyMap);
        
      } catch (error) {
        console.error('❌ Error fetching data:', error);
      } finally {
        // Always set loading to false after attempt, regardless of success/failure
        // The timetable grid can render without this data
        setLoading(false);
      }
    };
    
    // Only fetch if we don't have data yet and timetableData exists
    if (timetableData && Object.keys(courses).length === 0) {
      fetchData();
    } else if (!timetableData) {
      setLoading(false);
    }
  }, [timetableData]);

  // Helper functions to get names from IDs
  const getCourseName = (courseId: string) => {
    const course = courses[courseId];
    if (course) {
      return course.name || course.code || courseId;
    }
    // If not found, try to find by matching _id or id field
    const foundCourse = Object.values(courses).find((c: Course) => c._id === courseId || c.id === courseId);
    return foundCourse?.name || foundCourse?.code || courseId;
  };

  const getCourseCode = (courseId: string) => {
    const course = courses[courseId];
    if (course) {
      return course.code || courseId;
    }
    // If not found, try to find by matching _id or id field
    const foundCourse = Object.values(courses).find((c: Course) => c._id === courseId || c.id === courseId);
    return foundCourse?.code || courseId;
  };

  const getFacultyName = (facultyId: string) => {
    const facultyMember = faculty[facultyId];
    if (facultyMember) {
      return facultyMember.name || facultyId;
    }
    // If not found, try to find by matching _id or id field
    const foundFaculty = Object.values(faculty).find((f: Faculty) => f._id === facultyId || f.id === facultyId);
    return foundFaculty?.name || facultyId;
  };

  const getCourseType = (courseId: string) => {
    const course = courses[courseId];
    if (course) {
      return course.type || course.course_type || 'Theory';
    }
    // If not found, try to find by matching _id or id field
    const foundCourse = Object.values(courses).find((c: Course) => c._id === courseId || c.id === courseId);
    return foundCourse?.type || foundCourse?.course_type || 'Theory';
  };

  // Process the timetable data into a grid format
  const processScheduleData = (): { scheduleGrid: { [key: string]: { [key: string]: TimetableEntry | null } }, actualTimeSlots: string[] } => {
    try {
      const scheduleGrid: { [key: string]: { [key: string]: TimetableEntry | null } } = {};
      const actualTimeSlots = new Set<string>();
      
      // First pass: collect all actual time slots from the data
      let entries = null;
      if (timetableData?.entries) {
        entries = timetableData.entries;
        console.log('🔍 Found entries in timetableData.entries:', entries.length);
      } else if (timetableData?.timetable?.entries) {
        entries = timetableData.timetable.entries;
        console.log('🔍 Found entries in timetableData.timetable.entries:', entries.length);
      } else {
        console.log('❌ No entries found in either location');
        console.log('🔍 Available timetableData keys:', Object.keys(timetableData || {}));
      }
      
      if (entries && entries.length > 0) {
        console.log('🔍 Sample entry structure:', entries[0]);
        entries.forEach((entry: TimetableEntryData) => {
          // Defensive check for time_slot
          if (entry?.time_slot?.start_time && entry?.time_slot?.end_time) {
            const timeSlot = `${entry.time_slot.start_time} - ${entry.time_slot.end_time}`;
            actualTimeSlots.add(timeSlot);
          }
        });
      }
      
      // Use actual time slots if available, otherwise fall back to generated ones
      const slotsToUse: string[] = actualTimeSlots.size > 0 ? Array.from(actualTimeSlots).sort() : fallbackTimeSlots;
      console.log('🕐 Using time slots:', slotsToUse);

      // Initialize empty grid with actual time slots
      days.forEach(day => {
        scheduleGrid[day] = {};
        slotsToUse.forEach((slot: string) => {
          scheduleGrid[day][slot] = null;
        });
      });

      // Fill the grid with actual data from entries array (new backend structure)
      // Check for genetic algorithm response structure first (entries directly in response)
      if (entries && entries.length > 0) {
        console.log('🔍 Processing timetable entries:', entries.length);
        console.log('🔍 First entry sample:', entries[0]);
        
        let successfullyPlaced = 0;
        let failedToPlace = 0;
        
        entries.forEach((entry: TimetableEntryData, index: number) => {
          // Defensive checks
          if (!entry) {
            console.warn('⚠️ Entry is null:', entry);
            failedToPlace++;
            return;
          }

          // Handle both new (time_slot) and old (day, start_time, end_time) formats
          let timeSlot: {day: string; start_time: string; end_time: string; duration_minutes?: number} | undefined;
          
          if (entry.time_slot) {
            timeSlot = entry.time_slot;
          } else if ((entry as any).day && (entry as any).start_time && (entry as any).end_time) {
            // Old format - create time_slot from flat structure
            timeSlot = {
              day: (entry as any).day,
              start_time: (entry as any).start_time,
              end_time: (entry as any).end_time,
              duration_minutes: (entry as any).duration_minutes || 50
            };
            console.log(`📌 Entry ${index}: Converted old format to time_slot`);
          }

          if (!timeSlot) {
            console.warn(`⚠️ Entry ${index} missing time_slot or day/start_time/end_time:`, entry);
            failedToPlace++;
            return;
          }

          if (!timeSlot.start_time || !timeSlot.end_time) {
            console.warn(`⚠️ Time slot missing start_time or end_time:`, timeSlot);
            failedToPlace++;
            return;
          }

          const slotString = `${timeSlot.start_time} - ${timeSlot.end_time}`;
          const backendDay = timeSlot.day || 'Monday';
          const day = dayNameMapping[backendDay] || backendDay;
          
          console.log(`📅 Entry ${index}: ${entry.course_name} - Day: "${backendDay}" → "${day}", Time: ${slotString}`);
          
          // Initialize day if it doesn't exist
          if (!scheduleGrid[day]) {
            console.log(`  ℹ️  Created day "${day}" in grid`);
            scheduleGrid[day] = {};
            slotsToUse.forEach((slot: string) => {
              scheduleGrid[day][slot] = null;
            });
          }

          // Check if time slot exists in grid
          if (!(slotString in scheduleGrid[day])) {
            console.log(`  ℹ️  Creating time slot "${slotString}" in grid for day "${day}"`);
            scheduleGrid[day][slotString] = null;
          }

          // Place the entry - use all available data from entry
          console.log(`✅ Placing entry at ${day}/${slotString}`);
          scheduleGrid[day][slotString] = {
            day: day,
            time: slotString,
            course_name: entry.course_name || (entry as any).course_name || getCourseName(entry.course_id),
            course_code: entry.course_code || (entry as any).course_code || getCourseCode(entry.course_id),
            group: entry.group || (entry as any).group || entry.group_id || 'Default',
            room: entry.room || (entry as any).room || entry.room_id || 'TBD',
            faculty: entry.faculty || (entry as any).faculty || getFacultyName(entry.faculty_id) || 'TBD',
            is_lab: ((entry as any).is_lab === true),
            duration: timeSlot.duration_minutes || 50
          };
          successfullyPlaced++;
        });
        console.log(`📊 Placement summary: ${successfullyPlaced} placed, ${failedToPlace} failed out of ${entries.length} total`);
      }

      console.log('📊 Final schedule grid:', scheduleGrid);
      return { scheduleGrid, actualTimeSlots: slotsToUse };
    } catch (error) {
      console.error('❌ Error processing schedule data:', error);
      // Return empty grid with fallback time slots
      const emptyGrid: { [key: string]: { [key: string]: TimetableEntry | null } } = {};
      days.forEach(day => {
        emptyGrid[day] = {};
        fallbackTimeSlots.forEach((slot: string) => {
          emptyGrid[day][slot] = null;
        });
      });
      return { scheduleGrid: emptyGrid, actualTimeSlots: fallbackTimeSlots };
    }
  };

  // Process the schedule data to get actual time slots and grid
  const { scheduleGrid, actualTimeSlots: displayTimeSlots }: { scheduleGrid: { [key: string]: { [key: string]: TimetableEntry | null } }, actualTimeSlots: string[] } = processScheduleData();
  
  // Use actual time slots if available, otherwise fallback to generated ones
  const timeSlots: string[] = displayTimeSlots.length > 0 ? displayTimeSlots : fallbackTimeSlots;
  
  // Log the final schedule grid for debugging
  console.log('📊 Final schedule grid:', scheduleGrid);
  console.log('🕐 Actual time slots from data:', displayTimeSlots);
  console.log('⏰ Final time slots used:', timeSlots);
  
  // Count non-null entries in grid
  let entriesInGrid = 0;
  Object.values(scheduleGrid).forEach((daySlots) => {
    Object.values(daySlots).forEach((entry) => {
      if (entry !== null) entriesInGrid++;
    });
  });
  console.log(`📍 Total entries placed in grid: ${entriesInGrid}`);

  // Log the timetable data structure for debugging
  console.log('🔍 TimetableData structure:', timetableData);

  // Extract course information for the summary table
  const extractCourseInfo = (): CourseInfo[] => {
    const courses: { [key: string]: { name: string; code: string; faculty: string; periods: number; type: string; facultySet: Set<string> } } = {};
    
    // Extract from entries structure (handle both genetic algorithm and simple timetable responses)
    let entries = null;
    if (timetableData?.entries) {
      entries = timetableData.entries;
    } else if (timetableData?.timetable?.entries) {
      entries = timetableData.timetable.entries;
    }
    
    console.log('📚 Extracting course info from entries:', entries ? entries.length : 0, 'entries');
    
    if (entries && entries.length > 0) {
      console.log('  First entry sample:', entries[0]);
      console.log('  Entry keys:', Object.keys(entries[0]));
      
      entries.forEach((entry: any, index: number) => {
        // Use course_code as primary grouping key (more stable than course_id which might be numeric)
        const courseKey = entry.course_code || entry.course_id || `course_${index}`;
        const courseName = entry.course_name || entry.course || entry.subject || courseKey;
        const courseCodeDisplay = entry.course_code || entry.code || courseKey;
        
        // Try to get faculty name - first from faculty_id lookup, then faculty string, then TBD
        let facultyName = 'TBD';
        if (entry.faculty_id && faculty[entry.faculty_id]) {
          facultyName = faculty[entry.faculty_id].name || entry.faculty_id;
        } else if (entry.faculty) {
          // Use faculty string if it's not "mohan" (hardcoded default), otherwise try to get from formData
          if (entry.faculty !== 'mohan' && entry.faculty !== 'TBD') {
            facultyName = entry.faculty;
          } else {
            // Try to find faculty from formData
            const formFaculty = formData.faculty && formData.faculty.length > 0
              ? formData.faculty[(index % formData.faculty.length)]
              : null;
            facultyName = formFaculty?.name || entry.faculty || 'TBD';
          }
        } else if (formData.faculty && formData.faculty.length > 0) {
          // Use round-robin from form data faculty list
          facultyName = formData.faculty[(index % formData.faculty.length)].name || 'TBD';
        }
        
        console.log(`  Entry ${index}: courseKey="${courseKey}", name="${courseName}", faculty="${facultyName}"`);
        
        if (!courses[courseKey]) {
          courses[courseKey] = {
            name: courseName,
            code: courseCodeDisplay,
            periods: 0,
            faculty: facultyName,
            type: entry.is_lab ? 'Lab' : 'Theory',
            facultySet: new Set([facultyName])
          };
          console.log(`    ✓ Created new course entry for "${courseKey}", faculty: "${facultyName}"`);
        } else {
          // If course already exists, add faculty to the set
          courses[courseKey].facultySet.add(facultyName);
          // Update faculty display with all faculty names for this course
          const allFacultyNames = Array.from(courses[courseKey].facultySet as Set<string>)
            .filter(name => name && name !== 'TBD')
            .join(', ');
          courses[courseKey].faculty = allFacultyNames || 'TBD';
          console.log(`    + Updated existing course "${courseKey}", faculty count: ${courses[courseKey].facultySet.size}`);
        }
        courses[courseKey].periods += 1;
      });
    }

    // Clean up facultySet before returning
    const result = Object.values(courses).map(course => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { facultySet, ...cleanCourse } = course;
      return cleanCourse;
    });
    
    console.log(`📊 Final course info extracted: ${result.length} unique courses`);
    result.forEach((course, idx) => {
      console.log(`  ${idx + 1}. ${course.code} - ${course.name} (${course.periods} periods, ${course.faculty})`);
    });
    return result;
  };

  const courseInfo = extractCourseInfo();

  console.log('🔍 TimetableDisplay debug:', {
    timetableData: !!timetableData,
    loading,
    hasEntries: !!timetableData?.entries,
    entriesLength: timetableData?.entries?.length || 0
  });

  // Show loading state while fetching data
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Typography variant="h6" color="text.secondary">
          Loading course and faculty data...
        </Typography>
      </Box>
    );
  }

  // If no entries exist after loading, show empty state
  let entries = null;
  if (timetableData?.entries) {
    entries = timetableData.entries;
  } else if (timetableData?.timetable?.entries) {
    entries = timetableData.timetable.entries;
  }
  
  console.log('TimetableDisplay render - timetableData:', timetableData, 'entries:', entries, 'loading:', loading);
  
  // Show empty state ONLY if we have timetableData but no entries
  if (timetableData && !loading && (!entries || entries.length === 0)) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <Typography variant="h6" color="text.secondary">
          No timetable entries generated. Please check your courses and constraints.
        </Typography>
      </Box>
    );
  }

  // If no data at all, show loading or message
  if (!timetableData || !entries) {
    console.warn('No timetable data or entries', { timetableData, entries });
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px', flexDirection: 'column', gap: 2, background: '#f5f5f5', borderRadius: 2 }}>
        <Typography variant="h6" color="text.secondary">
          {loading ? '⏳ Loading timetable...' : '⏱️ Waiting for timetable data...'}
        </Typography>
        <Box sx={{ fontSize: '12px', color: '#666', background: '#fff', p: 2, borderRadius: 1, border: '1px solid #ddd', maxWidth: '400px' }}>
          <Typography variant="caption" display="block" sx={{ mb: 1, fontWeight: 'bold' }}>
            Debug Info:
          </Typography>
          <Typography variant="caption" display="block" sx={{ fontFamily: 'monospace', lineHeight: 1.8 }}>
            timetableData: {timetableData ? '✓ exists' : '✗ null'} {'\n'}
            entries: {entries ? `✓ ${entries.length} items` : '✗ null'} {'\n'}
            loading: {loading ? '⏳ true' : '✓ false'}
          </Typography>
        </Box>
      </Box>
    );
  }

  // Get cell content with proper styling
  const getCellContent = (entry: TimetableEntry | null, isBreak: boolean = false) => {
    if (isBreak) {
      return (
        <Box sx={{ 
          textAlign: 'center', 
          py: 1, 
          background: 'linear-gradient(45deg, rgba(255,193,7,0.2), rgba(255,152,0,0.2))',
          color: '#ffb74d',
          fontWeight: 'bold',
          border: '1px solid rgba(255,193,7,0.3)',
          borderRadius: 1
        }}>
          BREAK
        </Box>
      );
    }

    if (!entry) {
      return <Box sx={{ height: 40 }}></Box>;
    }

    const isLab = entry.is_lab;
    const backgroundColor = isLab ? '#fff3cd' : '#ffffff';
    const borderColor = isLab ? '#ffc107' : '#dee2e6';

    return (
      <Box sx={{ 
        p: 1, 
        backgroundColor,
        border: `1px solid ${borderColor}`,
        borderRadius: 1,
        minHeight: 60,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center'
      }}>
        <Typography variant="body2" sx={{ fontWeight: 'bold', fontSize: '0.75rem', lineHeight: 1.2 }}>
          {entry.course_name}
        </Typography>
        <Typography variant="caption" sx={{ color: '#666', fontSize: '0.65rem', lineHeight: 1.1 }}>
          {entry.course_code}
        </Typography>
        {entry.faculty && (
          <Typography variant="caption" sx={{ color: '#444', fontSize: '0.65rem', fontWeight: 'medium', lineHeight: 1.1 }}>
            {entry.faculty}
          </Typography>
        )}
        {entry.group && (
          <Typography variant="caption" sx={{ color: '#666', fontSize: '0.65rem', lineHeight: 1.1 }}>
            {entry.group} [{entry.room}]
          </Typography>
        )}
      </Box>
    );
  };

  const handleExport = (format: 'csv' | 'pdf') => {
    onExport(format);
  };

  return (
    <Box sx={{ width: '100%', mb: 4 }}>
      {/* Header */}
      <Card sx={{ 
        mb: 3, 
        background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        borderRadius: 3
      }}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'white', mb: 1 }}>
                B. Tech. CSE - AI-ML (Odd) Fifth Semester Class Routine
              </Typography>
              <Typography variant="subtitle1" sx={{ color: '#b0b0b0' }}>
                Theory Class Room - N-009 | Academic Year: {timetableData?.timetable?.academic_year || '2025-2026'}
              </Typography>
            </Box>
            
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                startIcon={<CsvIcon />}
                onClick={() => handleExport('csv')}
                sx={{ 
                  background: 'linear-gradient(45deg, #4CAF50, #66BB6A)',
                  boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #66BB6A, #4CAF50)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 6px 16px rgba(76, 175, 80, 0.4)'
                  }
                }}
              >
                Export CSV
              </Button>
              <Button
                variant="contained"
                startIcon={<PdfIcon />}
                onClick={() => handleExport('pdf')}
                sx={{ 
                  background: 'linear-gradient(45deg, #f44336, #ef5350)',
                  boxShadow: '0 4px 12px rgba(244, 67, 54, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #ef5350, #f44336)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 6px 16px rgba(244, 67, 54, 0.4)'
                  }
                }}
              >
                Export PDF
              </Button>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {/* Main Timetable */}
      <TableContainer component={Paper} sx={{ mb: 3, backgroundColor: '#1a1a1a' }}>
        <Table size="small" sx={{ minWidth: 1000 }}>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#2a2a2a' }}>
              <TableCell sx={{ color: 'white', fontWeight: 'bold', width: 100, border: '1px solid #444' }}>
                Day
              </TableCell>
              {timeSlots.map((slot: string) => (
                  <TableCell 
                    key={slot} 
                    sx={{ 
                      color: 'white', 
                      fontWeight: 'bold', 
                      textAlign: 'center',
                      border: '1px solid #444',
                      minWidth: 120,
                      fontSize: '0.75rem'
                    }}
                  >
                    {slot}
                  </TableCell>
                ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {days.map((day) => (
              <TableRow key={day} sx={{ backgroundColor: '#1a1a1a' }}>
                <TableCell sx={{ 
                  color: 'white', 
                  fontWeight: 'bold',
                  border: '1px solid #444',
                  backgroundColor: '#2a2a2a'
                }}>
                  {day}
                </TableCell>
                {timeSlots.map((slot: string) => (
                  <TableCell 
                    key={`${day}-${slot}`} 
                    sx={{ 
                      border: '1px solid #444',
                      p: 0.5,
                      verticalAlign: 'middle'
                    }}
                  >
                    {slot === '12:30 - 1:00' ? 
                      getCellContent(null, true) : 
                      getCellContent(scheduleGrid[day]?.[slot] || null)
                    }
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Course Information Table */}
      <Card sx={{ 
        background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        borderRadius: 3
      }}>
        <CardContent>
          <Typography variant="h6" sx={{ color: 'white', mb: 2, fontWeight: 'bold' }}>
            Course Information ({courseInfo.length} courses)
          </Typography>
          
          <TableContainer component={Paper} sx={{ backgroundColor: '#2a2a2a' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold', border: '1px solid #444' }}>
                    Paper Name
                  </TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold', border: '1px solid #444' }}>
                    Paper Code
                  </TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold', border: '1px solid #444' }}>
                    Periods
                  </TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 'bold', border: '1px solid #444' }}>
                    Faculty Name
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {courseInfo && courseInfo.length > 0 ? (
                  courseInfo.map((course: CourseInfo, index: number) => (
                    <TableRow key={index}>
                      <TableCell sx={{ color: 'white', border: '1px solid #444' }}>
                        {course.name}
                      </TableCell>
                      <TableCell sx={{ color: 'white', border: '1px solid #444' }}>
                        {course.code}
                      </TableCell>
                      <TableCell sx={{ color: 'white', border: '1px solid #444' }}>
                        {course.periods}
                      </TableCell>
                      <TableCell sx={{ color: 'white', border: '1px solid #444' }}>
                        {course.faculty}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={4} sx={{ color: '#999', border: '1px solid #444', textAlign: 'center', py: 2 }}>
                      No course information available
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Generation Statistics */}
      {timetableData?.generation_details && (
        <Card sx={{ 
          mt: 3, 
          background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          borderRadius: 3
        }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: 'white', mb: 2, fontWeight: 'bold' }}>
              Generation Statistics
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 2, 
                  background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
                }}>
                  <Typography variant="h4" sx={{ color: '#4CAF50', fontWeight: 'bold' }}>
                    {timetableData.generation_details.score || 'N/A'}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                    Optimization Score
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 2, 
                  background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
                }}>
                  <Typography variant="h4" sx={{ color: '#2196F3', fontWeight: 'bold' }}>
                    {timetableData.generation_details.statistics?.total_sessions || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                    Total Sessions
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 2, 
                  background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
                }}>
                  <Typography variant="h4" sx={{ color: '#FF9800', fontWeight: 'bold' }}>
                    {timetableData.generation_details.statistics?.lab_sessions || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                    Lab Sessions
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ flex: '1 1 200px', minWidth: '200px' }}>
                <Box sx={{ 
                  textAlign: 'center', 
                  p: 2, 
                  background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
                }}>
                  <Typography variant="h4" sx={{ color: '#9C27B0', fontWeight: 'bold' }}>
                    {timetableData.generation_details.statistics?.theory_sessions || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                    Theory Sessions
                  </Typography>
                </Box>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

// Error boundary wrapper
class TimetableDisplayErrorBoundary extends React.Component<
  { timetableData: any; onExport: (format: 'csv' | 'pdf') => void },
  { hasError: boolean; error: string }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: '' };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('🔥 TimetableDisplay Error Boundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 3, backgroundColor: '#0a0a0a', borderRadius: 2 }}>
          <Box
            sx={{
              backgroundColor: '#ffebee',
              border: '2px solid #f44336',
              borderRadius: 2,
              p: 2,
              mb: 2
            }}
          >
            <Typography variant="h6" sx={{ color: '#d32f2f', fontWeight: 'bold', mb: 1 }}>
              ❌ Error Rendering Timetable
            </Typography>
            <Typography variant="body2" sx={{ color: '#b0b0b0', fontFamily: 'monospace' }}>
              {this.state.error}
            </Typography>
            <Typography variant="caption" sx={{ color: '#888', display: 'block', mt: 1 }}>
              This usually means the timetable data is incomplete or improperly formatted.
            </Typography>
            <Button 
              onClick={() => window.location.reload()} 
              sx={{ mt: 2 }}
              variant="contained"
              color="error"
            >
              Reload Page
            </Button>
          </Box>
        </Box>
      );
    }

    return (
      <TimetableDisplay {...this.props} />
    );
  }
}

export default TimetableDisplayErrorBoundary;
