import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

interface AuthGuardProps {
  children: React.ReactNode;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, checkTokenExpiration, refreshTokenIfNeeded, logout } = useAuthStore();

  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      // If not authenticated, ensure user is redirected to login
      navigate('/login');
      return;
    }

    // Check token expiration every hour (since tokens now last 30 days)
    const checkInterval = setInterval(async () => {
      // Silent token check - don't log to console to avoid UI warnings
      const isExpiringSoon = checkTokenExpiration();
      
      if (isExpiringSoon) {
        const refreshSuccessful = await refreshTokenIfNeeded();
        
        if (!refreshSuccessful) {
          logout();
        }
      }
    }, 60 * 60 * 1000); // Check every hour instead of every 5 minutes

    // Also check immediately on mount
    const checkImmediately = async () => {
      const isExpiringSoon = checkTokenExpiration();
      if (isExpiringSoon) {
        await refreshTokenIfNeeded();
      }
    };
    
    checkImmediately();

    return () => clearInterval(checkInterval);
  }, [isAuthenticated, checkTokenExpiration, refreshTokenIfNeeded, logout]);

  return <>{children}</>;
};
