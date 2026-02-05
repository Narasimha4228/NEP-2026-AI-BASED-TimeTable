import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Schedule,
  School,
  Psychology,
  Assignment,
  CheckCircle,
  Warning,
} from '@mui/icons-material';
import timetableService from '../../services/timetableService';
import { useAuthStore } from '../../store/authStore';

interface DashboardStat {
  title: string;
  value: number | string;
  icon: React.ReactElement;
  color: string;
  change: string;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuthStore();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        let statsData: DashboardStat[] = [];

        // Helper function to safely fetch data with fallback
        const safelyFetch = async <T,>(fn: () => Promise<T>, fallback: T): Promise<T> => {
          try {
            return await fn();
          } catch (err) {
            console.warn('Failed to fetch, using fallback:', err);
            return fallback;
          }
        };

        // Check user role
        if (user?.role === 'faculty') {
          // Fetch faculty-specific dashboard
          try {
            const facultyDash = await timetableService.getFacultyDashboard();
            
            statsData = [
              {
                title: 'Total Classes',
                value: facultyDash.total_classes || 0,
                icon: <Schedule />,
                color: '#1976d2',
                change: 'Teaching assignments',
              },
              {
                title: "Today's Classes",
                value: facultyDash.today_classes || 0,
                icon: <Psychology />,
                color: '#2e7d32',
                change: facultyDash.today || 'Not available',
              },
              {
                title: 'Weekly Hours',
                value: facultyDash.weekly_hours || 0,
                icon: <Assignment />,
                color: '#ed6c02',
                change: 'teaching hours',
              },
              {
                title: 'Faculty Name',
                value: facultyDash.faculty_name || 'N/A',
                icon: <CheckCircle />,
                color: '#9c27b0',
                change: 'Current user',
              },
            ];
          } catch (err) {
            console.error('Error fetching faculty dashboard:', err);
            // Fallback to general data with error handling
            const programs = await safelyFetch(() => timetableService.getPrograms(), []);
            const courses = await safelyFetch(() => timetableService.getCourses(), []);
            const faculty = await safelyFetch(() => timetableService.getFaculty(), []);
            const rooms = await safelyFetch(() => timetableService.getRooms(), []);
            const timetables = await safelyFetch(() => timetableService.getAllTimetables(), []);

            statsData = [
              {
                title: 'Active Timetables',
                value: timetables.length,
                icon: <Schedule />,
                color: '#1976d2',
                change: `${timetables.length > 0 ? 'Active' : 'No active timetables'}`,
              },
              {
                title: 'Programs',
                value: programs.length,
                icon: <School />,
                color: '#2e7d32',
                change: `${programs.length} total programs`,
              },
              {
                title: 'Courses',
                value: courses.length,
                icon: <Assignment />,
                color: '#ed6c02',
                change: `${courses.length} courses available`,
              },
              {
                title: 'Faculty',
                value: faculty.length,
                icon: <Psychology />,
                color: '#9c27b0',
                change: `${faculty.length} faculty members`,
              },
              {
                title: 'Rooms',
                value: rooms.length,
                icon: <CheckCircle />,
                color: '#0288d1',
                change: `${rooms.length} rooms available`,
              },
            ];
          }
        } else if (user?.role === 'student') {
          // Fetch student-specific data with error handling
          const timetables = await safelyFetch(() => timetableService.getAllTimetables(), []);
          const courses = await safelyFetch(() => timetableService.getCourses(), []);

          statsData = [
            {
              title: 'My Classes',
              value: timetables.length,
              icon: <Schedule />,
              color: '#1976d2',
              change: 'Enrolled courses',
            },
            {
              title: 'Total Courses',
              value: courses.length,
              icon: <School />,
              color: '#2e7d32',
              change: 'Available courses',
            },
            {
              title: 'Status',
              value: 'Active',
              icon: <CheckCircle />,
              color: '#0288d1',
              change: 'Current semester',
            },
          ];
        } else {
          // Admin/Default view with error handling
          const programs = await safelyFetch(() => timetableService.getPrograms(), []);
          const courses = await safelyFetch(() => timetableService.getCourses(), []);
          const faculty = await safelyFetch(() => timetableService.getFaculty(), []);
          const rooms = await safelyFetch(() => timetableService.getRooms(), []);
          const timetables = await safelyFetch(() => timetableService.getAllTimetables(), []);

          statsData = [
            {
              title: 'Active Timetables',
              value: timetables.length,
              icon: <Schedule />,
              color: '#1976d2',
              change: `${timetables.length > 0 ? 'Active' : 'No active timetables'}`,
            },
            {
              title: 'Programs',
              value: programs.length,
              icon: <School />,
              color: '#2e7d32',
              change: `${programs.length} total programs`,
            },
            {
              title: 'Courses',
              value: courses.length,
              icon: <Assignment />,
              color: '#ed6c02',
              change: `${courses.length} courses available`,
            },
            {
              title: 'Faculty',
              value: faculty.length,
              icon: <Psychology />,
              color: '#9c27b0',
              change: `${faculty.length} faculty members`,
            },
            {
              title: 'Rooms',
              value: rooms.length,
              icon: <CheckCircle />,
              color: '#0288d1',
              change: `${rooms.length} rooms available`,
            },
          ];
        }

        setStats(statsData);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [user?.role]);

  const recentActivity = [
    {
      action: 'Timetable Generated',
      subject: 'Computer Science - Semester 3',
      time: '2 hours ago',
      status: 'success',
    },
    {
      action: 'AI Optimization',
      subject: 'Mathematics Department',
      time: '4 hours ago',
      status: 'success',
    },
    {
      action: 'Constraint Violation',
      subject: 'Physics Lab Schedule',
      time: '6 hours ago',
      status: 'warning',
    },
    {
      action: 'Program Updated',
      subject: 'B.Tech Electronics',
      time: '1 day ago',
      status: 'info',
    },
  ];

  const upcomingTasks = [
    'Review Computer Science timetable',
    'Optimize Mathematics department schedule',
    'Resolve Physics lab conflicts',
    'Generate reports for administration',
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
        Dashboard
      </Typography>

      {loading && (
        <Box display="flex" justifyContent="center" alignItems="center" sx={{ my: 4 }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>
            Loading dashboard data...
          </Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && (
        <>
          {/* Stats Cards */}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 4 }}>
            {stats.map((stat, index) => (
              <Card key={index} elevation={2} sx={{ minWidth: 250, flex: 1 }}>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography color="textSecondary" gutterBottom variant="overline">
                        {stat.title}
                      </Typography>
                      <Typography variant="h4" fontWeight="bold">
                        {stat.value}
                      </Typography>
                      <Typography variant="caption" color="success.main">
                        {stat.change}
                      </Typography>
                    </Box>
                <Box
                  sx={{
                    backgroundColor: stat.color,
                    borderRadius: 2,
                    p: 1,
                    color: 'white',
                  }}
                >
                  {stat.icon}
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>

      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {/* Recent Activity */}
        <Paper elevation={2} sx={{ p: 3, flex: 2, minWidth: 400 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
            Recent Activity
          </Typography>
          <List>
            {recentActivity.map((activity, index) => (
              <ListItem key={index} divider={index < recentActivity.length - 1}>
                <Box display="flex" alignItems="center" width="100%">
                  <Box sx={{ mr: 2 }}>
                    {activity.status === 'success' && (
                      <CheckCircle color="success" />
                    )}
                    {activity.status === 'warning' && (
                      <Warning color="warning" />
                    )}
                    {activity.status === 'info' && (
                      <Assignment color="info" />
                    )}
                  </Box>
                  <Box flexGrow={1}>
                    <ListItemText
                      primary={activity.action}
                      secondary={activity.subject}
                    />
                  </Box>
                  <Typography variant="caption" color="textSecondary">
                    {activity.time}
                  </Typography>
                </Box>
              </ListItem>
            ))}
          </List>
        </Paper>

        {/* Quick Actions & Tasks */}
        <Box sx={{ flex: 1, minWidth: 300 }}>
          <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
              System Status
            </Typography>
            <Box sx={{ mb: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">Database</Typography>
                <Chip label="Online" color="success" size="small" />
              </Box>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="body2">AI Service</Typography>
                <Chip label="Active" color="success" size="small" />
              </Box>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                Performance
              </Typography>
              <LinearProgress variant="determinate" value={87} />
              <Typography variant="caption" color="textSecondary">
                87% Efficiency
              </Typography>
            </Box>
          </Paper>

          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
              Upcoming Tasks
            </Typography>
            <List dense>
              {upcomingTasks.map((task, index) => (
                <ListItem key={index}>
                  <ListItemText primary={task} />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      </Box>
        </>
      )}
    </Box>
  );
};

export default Dashboard;
