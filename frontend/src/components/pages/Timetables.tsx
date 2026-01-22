import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Stack,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckCircleIcon,
  Drafts as DraftIcon,
  CalendarMonth as CalendarIcon,
} from '@mui/icons-material';
import { timetableService } from '../../services/timetableService';
import { useAuthStore } from '../../store/authStore';
import type { Timetable } from '../../services/timetableService';

const Timetables: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuthStore();

  const role = user?.role;
  const isAdmin = role === 'admin';

  const [timetables, setTimetables] = useState<Timetable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    timetable: Timetable | null;
  }>({ open: false, timetable: null });
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const fetchTimetables = async () => {
      if (!isAuthenticated) {
        navigate('/login');
        return;
      }

      try {
        setLoading(true);
        const data = await timetableService.getAllTimetables();
        setTimetables(data);
      } catch (err) {
        const error = err as { response?: { data?: { detail?: string } } };
        setError(error.response?.data?.detail || 'Failed to load timetables');
      } finally {
        setLoading(false);
      }
    };

    fetchTimetables();
  }, [isAuthenticated, navigate]);

  const handleEdit = (timetable: Timetable) => {
    const id = timetable.id || timetable._id;
    navigate(`/timetables/edit/${id}`);
  };

  const handleView = (timetable: Timetable) => {
    const id = timetable.id || timetable._id;
    navigate(`/timetables/${id}`);
  };

  const handleDeleteClick = (timetable: Timetable) => {
    setDeleteDialog({ open: true, timetable });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteDialog.timetable) return;

    const id = deleteDialog.timetable.id || deleteDialog.timetable._id;

    setDeleting(true);
    try {
      await timetableService.deleteTimetable(id);
      const updated = await timetableService.getAllTimetables();
      setTimetables(updated);
      setDeleteDialog({ open: false, timetable: null });
    } catch {
      setError('Failed to delete timetable');
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (date: string) => {
    try {
      return new Date(date).toLocaleDateString();
    } catch {
      return 'N/A';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading timetables...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            <CalendarIcon sx={{ mr: 1 }} />
            Timetables
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View generated academic timetables
          </Typography>
        </Box>

        {/* ADMIN ONLY */}
        {isAdmin && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/timetables/create')}
          >
            Create Timetable
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Empty State */}
      {timetables.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6">No timetables found</Typography>

          {isAdmin ? (
            <Button
              sx={{ mt: 2 }}
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate('/timetables/create')}
            >
              Create Timetable
            </Button>
          ) : (
            <Typography sx={{ mt: 2 }} color="text.secondary">
              Timetables will appear once admin generates them
            </Typography>
          )}
        </Paper>
      ) : (
        <Stack spacing={2}>
          {timetables.map((timetable) => (
            <Card key={timetable.id} sx={{ p: 2 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between">
                  <Box>
                    <Typography variant="h6" fontWeight="bold">
                      {timetable.title}
                    </Typography>
                    <Typography variant="body2">
                      {timetable.academic_year} — Semester {timetable.semester}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Created on {formatDate(timetable.created_at)}
                    </Typography>
                  </Box>

                  <Chip
                    size="small"
                    label={timetable.is_draft ? 'Draft' : 'Complete'}
                    color={timetable.is_draft ? 'warning' : 'success'}
                    icon={timetable.is_draft ? <DraftIcon /> : <CheckCircleIcon />}
                  />
                </Box>

                <Box display="flex" justifyContent="flex-end" mt={2} gap={1}>
                  <Tooltip title="View">
                    <IconButton onClick={() => handleView(timetable)}>
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>

                  {/* ADMIN ONLY */}
                  {isAdmin && (
                    <>
                      <Tooltip title="Edit">
                        <IconButton onClick={() => handleEdit(timetable)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>

                      <Tooltip title="Delete">
                        <IconButton onClick={() => handleDeleteClick(timetable)}>
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </>
                  )}
                </Box>
              </CardContent>
            </Card>
          ))}
        </Stack>
      )}

      {/* Delete Dialog */}
      <Dialog open={deleteDialog.open} onClose={() => setDeleteDialog({ open: false, timetable: null })}>
        <DialogTitle>Delete Timetable</DialogTitle>
        <DialogContent>
          Are you sure you want to delete this timetable?
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, timetable: null })}>
            Cancel
          </Button>
          <Button
            color="error"
            variant="contained"
            onClick={handleDeleteConfirm}
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Timetables;
