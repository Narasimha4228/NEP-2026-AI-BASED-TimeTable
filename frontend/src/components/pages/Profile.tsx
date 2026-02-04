import React from 'react';
import { Box, Paper, Typography, Avatar, Stack, Switch, FormControlLabel } from '@mui/material';
import { useAuthStore } from '../../store/authStore';
import { useThemeStore } from '../../store/themeStore';

const Profile: React.FC = () => {
  const { user } = useAuthStore();
  const mode = useThemeStore((s) => s.mode);
  const toggle = useThemeStore((s) => s.toggle);

  if (!user) return null;

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ p: 3, maxWidth: 800 }}>
        <Stack direction="row" spacing={2} alignItems="flex-start">
          <Avatar sx={{ width: 72, height: 72, bgcolor: 'secondary.main', flexShrink: 0 }}>
            {user.name?.charAt(0) ?? 'U'}
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6">{user.name}</Typography>
            <Typography variant="body2" color="text.secondary">{user.email}</Typography>
            <Typography variant="caption" color="text.secondary">Role: {user.role}</Typography>
          </Box>
        </Stack>

        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle1">Account Details</Typography>
          <Typography variant="body2">Full name: {user.full_name ?? user.name}</Typography>
          <Typography variant="body2">Active: {user.is_active ? 'Yes' : 'No'}</Typography>
          <Typography variant="body2">Admin: {user.is_admin ? 'Yes' : 'No'}</Typography>
        </Box>

        <Box sx={{ mt: 3 }}>
          <FormControlLabel
            control={<Switch checked={mode === 'dark'} onChange={toggle} />}
            label={mode === 'dark' ? 'Dark Theme' : 'Light Theme'}
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default Profile;
