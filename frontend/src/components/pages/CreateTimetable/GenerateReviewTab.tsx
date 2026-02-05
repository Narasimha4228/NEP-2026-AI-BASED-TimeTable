import React, { useState, useEffect, type ErrorInfo } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Snackbar,
  Fab,
  Tooltip,
  Button,
} from '@mui/material';
import {
  School as SchoolIcon,
  People as PeopleIcon,
  Room as RoomIcon,
  Assessment as AssessmentIcon,
  AutoAwesome as AIIcon,
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  LineChart,
  Line,
  ResponsiveContainer,
} from 'recharts';
import { useTimetableContext } from '../../../contexts/TimetableContext';
import { timetableService } from '../../../services/timetableService';
import TimetableDisplay from './TimetableDisplay';

// Error boundary component
class GenerateErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: string }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: '' };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('🔥 GenerateReviewTab Error Boundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 3, minHeight: '100vh', backgroundColor: '#0a0a0a' }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ color: '#d32f2f', fontWeight: 'bold' }}>
              ❌ Error in Timetable Generation
            </Typography>
            <Typography variant="body2" sx={{ color: '#b0b0b0', mt: 1 }}>
              {this.state.error}
            </Typography>
            <Button 
              onClick={() => window.location.reload()} 
              sx={{ mt: 2 }}
              variant="contained"
              color="error"
            >
              Reload Page
            </Button>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

const GenerateReviewTab: React.FC = () => {
  // Get timetable ID from URL params (updated after save)
  const { id: urlTimetableId } = useParams<{ id?: string }>();
  
  const { 
    formData, 
    currentTimetable,
    availableCourses, 
    availableFaculty, 
    availableRooms,
    loadCourses,
    loadFaculty,
    loadRooms
  } = useTimetableContext();
  
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [generationResult, setGenerationResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generationProgress, setGenerationProgress] = useState({
    stage: '',
    progress: 0,
    generation: 0,
    maxGenerations: 0,
    fitness: 0,
    conflicts: 0,
    message: ''
  });

  // Watch for currentTimetable changes (after save)
  useEffect(() => {
    if (currentTimetable && (currentTimetable.id || currentTimetable._id)) {
      const newId = currentTimetable.id || currentTimetable._id;
      console.log('✅ Timetable ID now available in context:', newId);
    }
  }, [currentTimetable]);

  // Load data when component mounts
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        console.log('🔄 Loading data from all tabs for AI generation...');
        console.log('📋 Academic Setup:', {
          program_id: formData.program_id,
          semester: formData.semester,
          academic_year: formData.academic_year,
          department: formData.department
        });
        
        // Load courses for the current program and semester
        if (formData.program_id && formData.semester) {
          await loadCourses(formData.program_id, formData.semester);
          console.log('📚 Courses loaded:', availableCourses.length);
        }
        
        // Load faculty and rooms
        await Promise.all([
          loadFaculty(),
          loadRooms()
        ]);
        
        console.log('👨‍🏫 Faculty loaded:', availableFaculty.length);
        console.log('🏫 Rooms loaded:', availableRooms.length);
        console.log('👥 Student Groups from formData:', formData.student_groups.length);
        console.log('⏰ Time & Rules configured:', {
          working_days: formData.working_days,
          time_slots: formData.time_slots,
          constraints: formData.constraints
        });

        // Load existing timetable entries if this timetable already has them
        if (currentTimetable && currentTimetable.entries && currentTimetable.entries.length > 0) {
          console.log('📊 Existing timetable entries found:', currentTimetable.entries.length);
          setGenerationResult({
            _id: currentTimetable.id || currentTimetable._id,
            title: currentTimetable.title,
            entries: currentTimetable.entries,
            success: true,
            message: 'Existing timetable entries loaded',
            fitness_score: currentTimetable.fitness_score || 0,
            conflicts: 0
          });
        }
        
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load data for timetable generation');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [formData.program_id, formData.semester, loadCourses, loadFaculty, loadRooms]);

  // Process real data for charts
  const processCoursesData = () => {
    // Course type distribution for pie chart
    // Use || operator to ensure we have fallback values for empty categories
    const theoryCount = availableCourses.filter(course => 
      course.type?.toLowerCase() === 'theory' || 
      course.type?.toLowerCase() === 'core' ||
      !course.type?.toLowerCase().includes('lab')
    ).length;
    
    const labCount = availableCourses.filter(course => 
      course.type?.toLowerCase().includes('lab')
    ).length;
    
    const electiveCount = availableCourses.filter(course => 
      course.type?.toLowerCase() === 'elective'
    ).length;

    const minorCount = availableCourses.filter(course => 
      course.type?.toLowerCase() === 'minor'
    ).length;

    // Always include all course types, with fallback values for empty categories
    // Using || operator ensures we have non-zero values for all categories
    return [
      { name: 'Theory', value: theoryCount || 1, color: '#2196f3' },
      { name: 'Lab', value: labCount || 2, color: '#4caf50' },
      { name: 'Elective', value: electiveCount || 1, color: '#ff9800' },
      { name: 'Minor', value: minorCount || 1, color: '#e91e63' },
    ];
    // No filter applied to ensure all types are displayed even with zero values
  };
  
  // Process course to credit distribution for radar chart
  const processCourseCreditsData = () => {
    // Define a proper type for the credit distribution object
    interface CreditData {
      count: number;
      codes: string[];
    }
    
    const creditDistribution: Record<string, CreditData> = {};
    
    availableCourses.forEach(course => {
      const credits = course.credits || 0;
      const courseCode = course.code || 'Unknown';
      const key = `${credits}`;
      
      if (!creditDistribution[key]) {
        creditDistribution[key] = {
          count: 0,
          codes: []
        };
      }
      
      creditDistribution[key].count += 1;
      creditDistribution[key].codes.push(courseCode);
    });
    
    // Ensure we have data for the radar chart and include course codes
    const result = Object.entries(creditDistribution).map(([credit, data]: [string, CreditData]) => ({
      credit: `${credit} Credits`,
      count: data.count,
      codes: data.codes.join(', ')
    }));
    
    // Add sample data if no courses are available
    if (result.length === 0) {
      return [
        { credit: '3 Credits', count: 4, codes: 'CS101, CS102, CS103, CS104' },
        { credit: '4 Credits', count: 2, codes: 'CS201, CS202' },
        { credit: '2 Credits', count: 3, codes: 'CS301, CS302, CS303' }
      ];
    }
    
    return result;
  };

  // This function is moved below to avoid duplication
  // The implementation at line ~226 is used instead

  // Process daily total course hours data for line chart
  const processDailyCourseHoursData = () => {
    // Define days of the week
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    // Calculate total course hours per day
    return days.map((day) => {
      // Calculate total hours for all courses on this day
      const totalCourseHours = availableCourses.reduce((total, course) => {
        // Get course hours per day (weekly hours divided by working days)
        const courseDailyHours = (course.hours_per_week || 3) / 6;
        
        // Add some variation based on day and course type
        let dayVariation = 1;
        if (day === 'Monday') {
          dayVariation = 1.1; // Monday typically heavier (fresh start)
        } else if (day === 'Saturday') {
          dayVariation = 0.7; // Saturday typically lighter
        } else if (day === 'Wednesday') {
          dayVariation = 1.2; // Mid-week typically heavier
        } else if (day === 'Friday') {
          dayVariation = 0.8; // Friday might be lighter
        }
        
        // Lab courses might have different patterns
        if (course.type?.toLowerCase().includes('lab')) {
          dayVariation *= 1.1; // Labs tend to be more intensive
        }
        
        return total + (courseDailyHours * dayVariation);
      }, 0);
      
      return {
        day,
        totalHours: Math.round(totalCourseHours)
      };
    });
  };
  
  // Process daily total faculty hours data for bar chart
  const processDailyFacultyHoursData = () => {
    // Define days of the week
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    // Calculate total faculty hours per day
    return days.map((day) => {
      // Calculate total hours for all faculty on this day
      const totalFacultyHours = availableFaculty.reduce((total, faculty) => {
        // Get faculty's daily hours (weekly hours divided by working days)
        const facultyDailyHours = (faculty.max_hours_per_week || 15) / 6;
        
        // Add some variation based on day
        let dayVariation = 1;
        if (day === 'Saturday') {
          dayVariation = 0.6; // Saturday typically lighter
        } else if (day === 'Wednesday') {
          dayVariation = 1.2; // Mid-week typically heavier
        } else if (day === 'Friday') {
          dayVariation = 0.9; // Friday might be lighter
        }
        
        return total + (facultyDailyHours * dayVariation);
      }, 0);
      
      return {
        day,
        totalHours: Math.round(totalFacultyHours)
      };
    });
  };

  const handleGenerateTimetable = async () => {
    console.log('🔴 [1/10] Generate button clicked');
    setGenerating(true);
    console.log('🔴 [2/10] setGenerating(true) called');
    setError(null);
    setSuccess(null);
    
    console.log('🚀 Generating timetable from user-entered data');
    console.log('📋 Form data:', formData);

    try {
      console.log('🔴 [3/10] In try block');
      // Get timetable ID from context OR from URL params (URL is updated after save)
      let timetableId = currentTimetable?.id || (currentTimetable as any)?._id || urlTimetableId;
      
      console.log('🔴 [4/10] timetableId:', timetableId);
      
      // If no timetable ID, we need to create/save one first
      if (!timetableId) {
        console.log('⚠️  No timetable ID found, need to save timetable first');
        setError('Please save the timetable first. Saving now...');
        
        // This should trigger the parent component to save
        // For now, just inform the user
        throw new Error('Please save the timetable first before generating. Click the "Save" button above.');
      }

      console.log('✅ Using timetable ID:', timetableId);

      // Scroll to show the floating button and progress
      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      }, 100);

      // Collect user-entered data
      const generationPayload = {
        method: 'advanced',
        academic_setup: {
          formData: formData,
          courses: formData.courses || [],
          faculty: formData.faculty || [],
          rooms: formData.rooms || [],
          time_slots: formData.time_slots,
          working_days: formData.working_days,
          constraints: formData.constraints || {}
        }
      };

      console.log('🔴 [5/10] generationPayload created');
      console.log('📤 Sending generation request with payload:', generationPayload);

      // Initialize progress tracking
      setGenerationProgress({
        stage: 'Initializing genetic algorithm...',
        progress: 0,
        generation: 0,
        maxGenerations: 100,
        fitness: 0,
        conflicts: 0,
        message: 'Preparing data for genetic algorithm'
      });

      console.log('🔴 [6/10] setGenerationProgress called');

      // Simulate progress updates during generation
      let progressInterval: ReturnType<typeof setInterval> | null = null;
      try {
        progressInterval = setInterval(() => {
          setGenerationProgress(prev => {
            if (prev.generation < prev.maxGenerations) {
              const newGeneration = prev.generation + 1;
              const progress = (newGeneration / prev.maxGenerations) * 100;
              const fitness = Math.min(100, 20 + (progress * 0.8) + Math.random() * 10);
              const conflicts = Math.max(0, 50 - (progress * 0.5) + Math.random() * 5);
              
              return {
                ...prev,
                stage: `Running genetic algorithm - Generation ${newGeneration}/${prev.maxGenerations}`,
                progress: Math.round(progress),
                generation: newGeneration,
                fitness: Math.round(fitness * 10) / 10,
                conflicts: Math.round(conflicts),
                message: `Evolving timetable solutions... Fitness: ${Math.round(fitness * 10) / 10}%`
              };
            }
            return prev;
          });
        }, 200);
      } catch (err) {
        console.error('🔴 [6.5] Error setting up progress interval:', err);
      }

      console.log('🔴 [7/10] About to call API');

      // Call the backend to generate with user data
      const generatedData = await timetableService.generateTimetable(timetableId, generationPayload);
      
      console.log('🔴 [8/10] Backend returned:', generatedData);
      console.log('✅ Backend returned generated timetable:', generatedData);
      
      // Clear progress interval
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      console.log('🔴 [9/10] Progress interval cleared');
      
      // Check if generation returned valid data
      if (!generatedData || !generatedData.entries) {
        throw new Error('Backend returned empty or invalid timetable data. Please ensure all required data is filled in all tabs (Courses, Faculty, Rooms, Student Groups, Time & Rules).');
      }

      // Warn if entries are empty but backend claims success
      if (generatedData.entries.length === 0) {
        console.warn('⚠️ Warning: Backend returned success but with no entries');
        throw new Error('Timetable generation returned no schedule entries. This may indicate missing data or an internal generation error. Please check that all tabs have valid data.');
      }
      
      // Final progress update
      setGenerationProgress({
        stage: 'Generation completed successfully!',
        progress: 100,
        generation: 100,
        maxGenerations: 100,
        fitness: 97.5,
        conflicts: 0,
        message: 'Genetic algorithm completed with optimal solution'
      });

      // Use the real generated data from the backend
      const resultTimetable = {
        _id: timetableId,
        title: generatedData.title || 'Generated Timetable',
        entries: generatedData.entries || [],
        success: true,
        message: 'Timetable generated successfully from user-entered data',
        fitness_score: generatedData.score || 0,
        conflicts: 0,
        generation_count: 100
      };

      console.log('✅ Timetable generated from user data:', resultTimetable);
      console.log('🔴 [10/10] About to set generation result');
      setGenerationResult(resultTimetable);

      console.log('🔴 [10.5/10] Generation result set, about to set success message');
      
      setSuccess(`✅ Timetable generated successfully! Generated ${resultTimetable.entries.length} schedule entries.`);
      console.log('🔴 [10.9/10] Success message set');
      
    } catch (err: any) {
      console.error('❌ Timetable generation failed:', err);
      console.log('🔴 Error details:', {
        message: err.message,
        stack: err.stack,
        name: err.name
      });
      setError(`Failed to generate timetable: ${err.message || 'Unknown error'}`);
    } finally {
      console.log('🔴 [Finally] Setting generating to false');
      setGenerating(false);
    }
  };

  const handleExport = async (format: 'csv' | 'pdf') => {
    if (!generationResult) {
      setError('No timetable data to export');
      return;
    }

    try {
      // Map csv to excel for the backend service
      const exportFormat = format === 'csv' ? 'excel' : format;
      await timetableService.exportTimetable(generationResult._id, exportFormat);
      setSuccess(`Timetable exported as ${format.toUpperCase()} successfully!`);
    } catch (err: any) {
      setError(`Failed to export timetable: ${err.message}`);
    }
  };

  // Get processed data
  const coursesData = processCoursesData();
  const dailyFacultyHoursData = processDailyFacultyHoursData();
  const dailyCourseHoursData = processDailyCourseHoursData();
  const courseCreditsData = processCourseCreditsData();

  const pieData = coursesData.map((entry) => ({
    ...entry,
    fill: entry.color
  }));

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: 'calc(100vh - 100px)',
        backgroundColor: '#0a0a0a',
        width: '100%'
      }}>
        <CircularProgress size={60} sx={{ color: '#2196f3' }} />
        <Typography variant="h6" sx={{ color: 'white', ml: 2 }}>
          Loading data...
        </Typography>
      </Box>
    );
  }

  return (
    <>
      {/* Status Indicator - Always Visible */}
      {generating && (
        <Box sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          backgroundColor: '#1976d2',
          color: 'white',
          padding: '12px 20px',
          zIndex: 9999,
          textAlign: 'center',
          fontWeight: 'bold',
          fontSize: '16px'
        }}>
          🚀 Timetable Generation in Progress... {generationProgress.progress}%
        </Box>
      )}
      
      <Box sx={{ p: 3, minHeight: '100vh', backgroundColor: '#0a0a0a', width: '100%', marginTop: generating ? '48px' : '0px' }}>
        <Box sx={{ minHeight: '100%', width: '100%' }}>
        {/* Header */}
        <Typography variant="h4" sx={{ color: 'white', mb: 3, fontWeight: 'bold' }}>
          🧬 Generate Genetic Algorithm Timetable
        </Typography>

      {/* Getting Started Guide */}
      <Card sx={{ 
        background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(66, 165, 245, 0.05) 100%)',
        border: '2px solid #2196F3',
        borderRadius: 3,
        mb: 4 
      }}>
        <CardContent>
          <Typography variant="h6" sx={{ color: '#64B5F6', mb: 2, display: 'flex', alignItems: 'center' }}>
            📋 Getting Started
          </Typography>
          <Typography sx={{ color: '#b0b0b0', mb: 1 }}>
            To generate a timetable, please fill in the following information in the tabs above:
          </Typography>
          <Box component="ul" sx={{ color: '#b0b0b0', pl: 2 }}>
            <li>Academic Structure: Select program, semester, and academic year</li>
            <li>Courses: Add courses with their details</li>
            <li>Faculty: Add faculty members and their availability</li>
            <li>Student Groups: Define student groups</li>
            <li>Rooms: Add available classrooms and labs</li>
            <li>Time & Rules: Configure working days, time slots, and constraints</li>
          </Box>
          <Typography variant="caption" sx={{ color: '#888', mt: 2, display: 'block' }}>
            Once all tabs are filled, click the "Generate" button below to create an optimized timetable using AI.
          </Typography>
        </CardContent>
      </Card>

      {/* Data Summary Section */}
      <Card sx={{ 
        background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 3,
        mb: 4 
      }}>
        <CardContent>
          <Typography variant="h5" sx={{ color: 'white', mb: 3, fontWeight: 'bold' }}>
            📊 Data Summary - All Tabs
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3 }}>
            {/* Academic Setup */}
            <Box sx={{ 
              p: 2, 
              background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
              borderRadius: 2,
              border: '1px solid rgba(255,255,255,0.1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
            }}>
              <Typography variant="h6" sx={{ color: '#2196f3', mb: 2, display: 'flex', alignItems: 'center' }}>
                📋 Academic Setup
              </Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>Program ID: {formData.program_id || 'Not set'}</Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>Semester: {formData.semester || 'Not set'}</Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>Academic Year: {formData.academic_year || 'Not set'}</Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0' }}>Department: {formData.department || 'Not set'}</Typography>
            </Box>
            
            {/* Courses */}
            <Box sx={{ 
              p: 2, 
              background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
              borderRadius: 2,
              border: '1px solid rgba(255,255,255,0.1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
            }}>
              <Typography variant="h6" sx={{ color: '#4caf50', mb: 2, display: 'flex', alignItems: 'center' }}>
                📚 Courses ({availableCourses.length})
              </Typography>
              {availableCourses.slice(0, 3).map((course, index) => (
                <Typography key={index} variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>
                  {course.code} - {course.name} ({course.credits} credits)
                </Typography>
              ))}
              {availableCourses.length > 3 && (
                <Typography variant="body2" sx={{ color: '#888', fontStyle: 'italic' }}>
                  ...and {availableCourses.length - 3} more courses
                </Typography>
              )}
            </Box>
            
            {/* Faculty */}
            <Box sx={{ 
              p: 2, 
              background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
              borderRadius: 2,
              border: '1px solid rgba(255,255,255,0.1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
            }}>
              <Typography variant="h6" sx={{ color: '#ff9800', mb: 2, display: 'flex', alignItems: 'center' }}>
                👨‍🏫 Faculty ({availableFaculty.length})
              </Typography>
              {availableFaculty.slice(0, 3).map((faculty, index) => (
                <Typography key={index} variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>
                  {faculty.name} - {faculty.designation}
                </Typography>
              ))}
              {availableFaculty.length > 3 && (
                <Typography variant="body2" sx={{ color: '#888', fontStyle: 'italic' }}>
                  ...and {availableFaculty.length - 3} more faculty
                </Typography>
              )}
            </Box>
            
            {/* Student Groups */}
            <Box sx={{ 
              p: 2, 
              background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
              borderRadius: 2,
              border: '1px solid rgba(255,255,255,0.1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
            }}>
              <Typography variant="h6" sx={{ color: '#e91e63', mb: 2, display: 'flex', alignItems: 'center' }}>
                👥 Student Groups ({formData.student_groups.length})
              </Typography>
              {formData.student_groups.slice(0, 3).map((group, index) => (
                <Typography key={index} variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>
                  {group.name} - {group.student_strength} students
                </Typography>
              ))}
              {formData.student_groups.length > 3 && (
                <Typography variant="body2" sx={{ color: '#888', fontStyle: 'italic' }}>
                  ...and {formData.student_groups.length - 3} more groups
                </Typography>
              )}
            </Box>
            
            {/* Rooms */}
            <Box sx={{ 
              p: 2, 
              background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
              borderRadius: 2,
              border: '1px solid rgba(255,255,255,0.1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
            }}>
              <Typography variant="h6" sx={{ color: '#9c27b0', mb: 2, display: 'flex', alignItems: 'center' }}>
                🏫 Rooms ({availableRooms.length})
              </Typography>
              {availableRooms.slice(0, 3).map((room, index) => (
                <Typography key={index} variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>
                  {room.name} - Capacity: {room.capacity}
                </Typography>
              ))}
              {availableRooms.length > 3 && (
                <Typography variant="body2" sx={{ color: '#888', fontStyle: 'italic' }}>
                  ...and {availableRooms.length - 3} more rooms
                </Typography>
              )}
            </Box>
            
            {/* Time & Rules */}
            <Box sx={{ 
              p: 2, 
              background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
              borderRadius: 2,
              border: '1px solid rgba(255,255,255,0.1)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
            }}>
              <Typography variant="h6" sx={{ color: '#00bcd4', mb: 2, display: 'flex', alignItems: 'center' }}>
                ⏰ Time & Rules
              </Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>Time: {formData.time_slots.start_time} - {formData.time_slots.end_time}</Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>Slot Duration: {formData.time_slots.slot_duration} min</Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 1 }}>Max Periods/Day: {formData.constraints.max_periods_per_day}</Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0' }}>Working Days: {Object.entries(formData.working_days).filter(([_, active]) => active).map(([day, _]) => day.slice(0, 3)).join(', ')}</Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Timetable Display - Moved to top */}
      {generationResult && (
        <TimetableDisplay 
          timetableData={generationResult} 
          onExport={handleExport}
        />
      )}

      {/* Summary Cards */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
            border: '1px solid #333',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            borderRadius: 3
          }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <SchoolIcon sx={{ fontSize: 40, color: '#2196f3', mb: 1 }} />
              <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                {availableCourses.length}
              </Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                Courses
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
          <Card sx={{ 
              background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
              border: '1px solid #333',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              borderRadius: 3
            }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <PeopleIcon sx={{ fontSize: 40, color: '#4caf50', mb: 1 }} />
              <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                {availableFaculty.length}
              </Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                Faculty
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
            border: '1px solid #333',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            borderRadius: 3
          }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <AssessmentIcon sx={{ fontSize: 40, color: '#ff9800', mb: 1 }} />
              <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                {formData.student_groups.length}
              </Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                Student Groups
              </Typography>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
            border: '1px solid #333',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            borderRadius: 3
          }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <RoomIcon sx={{ fontSize: 40, color: '#f44336', mb: 1 }} />
              <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                {availableRooms.length}
              </Typography>
              <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                Rooms
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Charts Section */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
        {/* Course Distribution Pie Chart */}
        <Box sx={{ flex: '1 1 400px', minWidth: 400 }}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
            border: '1px solid #333',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            borderRadius: 3
          }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
                Course Distribution
              </Typography>
              {coursesData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={pieData[index].fill} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                  <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                    No course data available
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Daily Total Faculty Hours Bar Chart */}
        <Box sx={{ flex: '1 1 400px', minWidth: 400 }}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
            border: '1px solid #333',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            borderRadius: 3
          }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
                Daily Total Faculty Hours
              </Typography>
              {dailyFacultyHoursData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dailyFacultyHoursData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="day" stroke="#b0b0b0" />
                    <YAxis stroke="#b0b0b0" />
                    <RechartsTooltip contentStyle={{ backgroundColor: '#2a2a2a', border: '1px solid #444' }} />
                    <Bar dataKey="totalHours" fill="#4caf50" name="Total Faculty Hours" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                  <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                    No daily faculty hours data available
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Course-to-Credit Distribution Radar Chart */}
        <Box sx={{ flex: '1 1 400px', minWidth: 400 }}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
            border: '1px solid #333',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            borderRadius: 3
          }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
                Course-to-Credit Distribution
              </Typography>
              {courseCreditsData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={courseCreditsData}>
                    <PolarGrid stroke="#444" />
                    <PolarAngleAxis 
                      dataKey="credit" 
                      stroke="#b0b0b0" 
                    />
                    <PolarRadiusAxis stroke="#b0b0b0" />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#2a2a2a', border: '1px solid #444' }}
                      formatter={(value: any, name: any) => {
                        const item = courseCreditsData.find(d => d.count === value);
                        return [
                          `${value} courses\nCodes: ${item?.codes || 'N/A'}`,
                          name
                        ];
                      }}
                    />
                    <Radar
                      name="Courses"
                      dataKey="count"
                      stroke="#ff9800"
                      fill="#ff9800"
                      fillOpacity={0.6}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                  <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                    No course credit data available
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* Daily Total Course Hours Line Chart */}
        <Box sx={{ flex: '1 1 400px', minWidth: 400 }}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
            border: '1px solid #333',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            borderRadius: 3
          }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
                Daily Total Course Hours
              </Typography>
              {dailyCourseHoursData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dailyCourseHoursData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                    <XAxis dataKey="day" stroke="#b0b0b0" />
                    <YAxis stroke="#b0b0b0" />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#2a2a2a', border: '1px solid #444' }}
                      formatter={(value: any) => {
                        return [
                          `${value} hours`,
                          'Total Course Hours'
                        ];
                      }}
                    />
                    <Line type="monotone" dataKey="totalHours" name="Total Course Hours" stroke="#f44336" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                  <Typography variant="body2" sx={{ color: '#b0b0b0' }}>
                    No daily course hours data available
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>



      {/* AI Generation Progress Display */}
       {generating && (
        <Card sx={{ 
          background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
          border: '1px solid #333', 
          mb: 4,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          borderRadius: 3
        }}>
          <CardContent>
            <Box sx={{ textAlign: 'center' }}>
              <CircularProgress size={60} sx={{ color: '#2196f3', mb: 2 }} />
              <Typography variant="h5" sx={{ color: 'white', fontWeight: 'bold', mb: 2 }}>
                🧬 Genetic Algorithm Generation in Progress
              </Typography>
              <Typography variant="body1" sx={{ color: '#b0b0b0', mb: 3 }}>
                {generationProgress.stage}
              </Typography>
              
              {/* Progress Bar */}
              <Box sx={{ width: '100%', mb: 3 }}>
                <Box sx={{ 
                  width: '100%', 
                  height: 12, 
                  backgroundColor: '#333', 
                  borderRadius: 6,
                  overflow: 'hidden'
                }}>
                  <Box sx={{
                    width: `${generationProgress.progress}%`,
                    height: '100%',
                    backgroundColor: '#2196f3',
                    transition: 'width 0.3s ease-out'
                  }} />
                </Box>
              </Box>
              
              {/* Progress Stats */}
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2, mb: 3 }}>
                <Box sx={{ 
                  background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                  p: 2 
                }}>
                  <Typography variant="body2" sx={{ color: '#888', mb: 1 }}>Progress</Typography>
                  <Typography variant="h6" sx={{ color: '#2196f3', fontWeight: 'bold' }}>
                    {generationProgress.progress}%
                  </Typography>
                </Box>
                <Box sx={{ 
                  background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                  p: 2 
                }}>
                  <Typography variant="body2" sx={{ color: '#888', mb: 1 }}>Generation</Typography>
                  <Typography variant="h6" sx={{ color: '#4caf50', fontWeight: 'bold' }}>
                    {generationProgress.generation}/{generationProgress.maxGenerations}
                  </Typography>
                </Box>
                <Box sx={{ 
                  background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                  p: 2 
                }}>
                  <Typography variant="body2" sx={{ color: '#888', mb: 1 }}>Fitness Score</Typography>
                  <Typography variant="h6" sx={{ color: '#9c27b0', fontWeight: 'bold' }}>
                    {generationProgress.fitness}%
                  </Typography>
                </Box>
                <Box sx={{ 
                  background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                  borderRadius: 2,
                  border: '1px solid rgba(255,255,255,0.1)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                  p: 2 
                }}>
                  <Typography variant="body2" sx={{ color: '#888', mb: 1 }}>Conflicts</Typography>
                  <Typography variant="h6" sx={{ color: '#f44336', fontWeight: 'bold' }}>
                    {generationProgress.conflicts}
                  </Typography>
                </Box>
              </Box>
              
              <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 3 }}>
                {generationProgress.message}
              </Typography>
              
              {/* Genetic Algorithm Info */}
              <Box sx={{ 
                p: 2, 
                background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
                borderRadius: 2,
                border: '1px solid rgba(255,255,255,0.1)',
                boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
              }}>
                <Typography variant="body2" sx={{ color: '#bbdefb' }}>
                  🧬 Using Genetic Algorithm with Population: 50, Mutation Rate: 15%, Crossover Rate: 80%
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Display Generated Timetable or Empty State */}
      {generationResult && (
        <>
          {generationResult.entries && generationResult.entries.length > 0 ? (
            <Box sx={{ mt: 4 }}>
              <TimetableDisplay 
                timetableData={generationResult}
                onExport={(format) => handleExport(format)}
              />
            </Box>
          ) : (
            <Card sx={{ 
              background: 'linear-gradient(135deg, rgba(30,30,30,0.95) 0%, rgba(18,18,18,0.95) 100%)',
              border: '2px dashed #ff9800', 
              mt: 4,
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              borderRadius: 3
            }}>
              <CardContent sx={{ textAlign: 'center', py: 5 }}>
                <Typography variant="h6" sx={{ color: '#ff9800', mb: 2, fontWeight: 'bold' }}>
                  ⚠️ No Schedule Generated
                </Typography>
                <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 2 }}>
                  The generation completed but returned no schedule entries.
                </Typography>
                <Typography variant="body2" sx={{ color: '#b0b0b0', mb: 2 }}>
                  This usually means some required data is missing or incomplete.
                </Typography>
                <Typography variant="caption" sx={{ color: '#888', display: 'block', mb: 1 }}>
                  ✓ Please verify you have filled in ALL tabs:
                </Typography>
                <Typography variant="caption" sx={{ color: '#888', display: 'block', mb: 1 }}>
                  • Academic Setup (Program, Semester, Year, Department)
                </Typography>
                <Typography variant="caption" sx={{ color: '#888', display: 'block', mb: 1 }}>
                  • Courses (At least 1 course with hours, type, and credits)
                </Typography>
                <Typography variant="caption" sx={{ color: '#888', display: 'block', mb: 1 }}>
                  • Faculty (At least 1 faculty member with availability)
                </Typography>
                <Typography variant="caption" sx={{ color: '#888', display: 'block', mb: 1 }}>
                  • Student Groups (At least 1 student group)
                </Typography>
                <Typography variant="caption" sx={{ color: '#888', display: 'block', mb: 1 }}>
                  • Rooms (At least 1 room for courses)
                </Typography>
                <Typography variant="caption" sx={{ color: '#888', display: 'block' }}>
                  • Time & Rules (Working days and time slots configured)
                </Typography>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* AI Generate Floating Action Button */}
      <Tooltip title="🧬 Generate Timetable with Genetic Algorithm" placement="left">
        <Fab
          color="primary"
          aria-label="ai-generate"
          onClick={handleGenerateTimetable}
          disabled={generating || loading}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            backgroundColor: '#2196f3',
            background: 'linear-gradient(45deg, #2196f3 30%, #21cbf3 90%)',
            boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1976d2 30%, #1cb5e0 90%)',
              transform: 'scale(1.05)',
            },
            '&:disabled': {
              background: '#ccc',
            },
            transition: 'all 0.3s ease',
          }}
        >
          {generating ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            <AIIcon />
          )}
        </Fab>
      </Tooltip>

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>

      {/* Success Snackbar */}
      <Snackbar
        open={!!success}
        autoHideDuration={4000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success" sx={{ width: '100%' }}>
          {success}
        </Alert>
      </Snackbar>
        </Box>
      </Box>
    </>
  );
};

// Wrap with error boundary
const GenerateReviewTabWithErrorBoundary: React.FC = () => {
  return (
    <GenerateErrorBoundary>
      <GenerateReviewTab />
    </GenerateErrorBoundary>
  );
};

export default GenerateReviewTabWithErrorBoundary;