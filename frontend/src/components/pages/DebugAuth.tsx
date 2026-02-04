import React from 'react';
import { Box, Paper, Typography, Button, Stack, Alert, Divider } from '@mui/material';
import { useAuthStore } from '../../store/authStore';
import { useNavigate } from 'react-router-dom';

const DebugAuth: React.FC = () => {
  const { user, token, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  
  const authStorage = localStorage.getItem('auth-storage');
  const parsed = authStorage ? JSON.parse(authStorage) : null;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>🔐 Debug: Auth Status</Typography>
      
      {!isAuthenticated && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          ⚠️ You are NOT authenticated. Please log in first.
        </Alert>
      )}

      {isAuthenticated && (
        <Alert severity="success" sx={{ mb: 2 }}>
          ✅ You ARE authenticated
        </Alert>
      )}
      
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2"><b>Auth State (from Zustand store):</b></Typography>
        <Stack spacing={1} sx={{ mt: 1, fontFamily: 'monospace', fontSize: '0.85rem' }}>
          <Typography><b>isAuthenticated:</b> {String(isAuthenticated)}</Typography>
          <Typography><b>Token present:</b> {token ? 'YES' : 'NO'}</Typography>
          {token && <Typography><b>Token preview:</b> {token.substring(0, 50)}...</Typography>}
          <Typography><b>User:</b></Typography>
          <pre style={{ background: '#f5f5f5', padding: '8px', borderRadius: '4px', overflow: 'auto', maxHeight: 200 }}>
            {user ? JSON.stringify(user, null, 2) : 'null'}
          </pre>
        </Stack>
      </Paper>

      <Divider sx={{ my: 2 }} />

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2"><b>localStorage (auth-storage):</b></Typography>
        <pre style={{ background: '#f5f5f5', padding: '8px', borderRadius: '4px', overflow: 'auto', maxHeight: 200, marginTop: '8px' }}>
          {authStorage ? JSON.stringify(parsed, null, 2) : 'empty'}
        </pre>
      </Paper>

      <Stack direction="row" spacing={2}>
        <Button variant="contained" onClick={() => navigate('/login')}>Go to Login</Button>
        <Button variant="contained" onClick={() => navigate('/my-timetable')}>Go to Timetable</Button>
        <Button variant="outlined" onClick={() => location.reload()}>Reload Page</Button>
      </Stack>
    </Box>
  );
};

export default DebugAuth;
