import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Avatar,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Chat as ChatIcon,
  Warning as EmergencyIcon,
  LocalPharmacy as MedicationIcon,
  Security as ScamIcon,
  Spa as WellnessIcon,
  People as FamilyIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  Logout as LogoutIcon,
  AutoAwesome as HeroIcon,
} from '@mui/icons-material';
import { useAuthStore } from '../../stores/authStore';
import { useWebSocket } from '../../contexts/WebSocketContext';

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
  { label: 'AI Chat', path: '/chat', icon: <ChatIcon /> },
  { label: 'Emergency', path: '/emergency', icon: <EmergencyIcon />, color: 'error' },
  { label: 'Medications', path: '/medication', icon: <MedicationIcon /> },
  { label: 'Scam Detection', path: '/scam-detection', icon: <ScamIcon /> },
  { label: 'Wellness', path: '/wellness', icon: <WellnessIcon /> },
  { label: 'Family Portal', path: '/family-portal', icon: <FamilyIcon /> },
  { label: 'Hero Tech', path: '/hero-showcase', icon: <HeroIcon />, highlight: true },
  { label: 'Settings', path: '/settings', icon: <SettingsIcon /> },
];

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { isConnected } = useWebSocket();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleNav = (path) => {
    navigate(path);
    setDrawerOpen(false);
  };

  const isActive = (path) => location.pathname === path;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(90deg, #1a237e 0%, #311b92 100%)' }}>
        <Toolbar>
          {/* Hamburger for mobile */}
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setDrawerOpen(true)}
            sx={{ mr: 1, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          {/* Logo */}
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 0, mr: 3, cursor: 'pointer', fontWeight: 'bold' }}
            onClick={() => navigate('/dashboard')}
          >
            🛡️ Elder AI Guardian
          </Typography>

          {/* Desktop Nav */}
          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' }, gap: 0.5 }}>
            {navItems.map((item) => (
              <Button
                key={item.path}
                color="inherit"
                onClick={() => handleNav(item.path)}
                startIcon={item.icon}
                size="small"
                sx={{
                  opacity: isActive(item.path) ? 1 : 0.75,
                  fontWeight: isActive(item.path) ? 'bold' : 'normal',
                  bgcolor: isActive(item.path) ? 'rgba(255,255,255,0.15)' : 'transparent',
                  ...(item.highlight && {
                    border: '1px solid rgba(255,255,255,0.5)',
                    borderRadius: 1,
                  }),
                  ...(item.color === 'error' && {
                    color: '#ff8a80',
                  }),
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' },
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>

          {/* Right side: WS status + user */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title={isConnected ? 'Real-time connected' : 'WebSocket disconnected'}>
              <Chip
                label={isConnected ? '🟢 Live' : '🔴 Offline'}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: 'white', fontSize: '0.7rem' }}
              />
            </Tooltip>
            <Typography variant="caption" sx={{ opacity: 0.8, display: { xs: 'none', sm: 'block' } }}>
              {user?.name || user?.email || 'User'}
            </Typography>
            <Tooltip title="Logout">
              <IconButton color="inherit" onClick={handleLogout} size="small">
                <LogoutIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Box sx={{ width: 260 }}>
          <Box sx={{ p: 2, bgcolor: '#1a237e', color: 'white' }}>
            <Typography variant="h6" fontWeight="bold">🛡️ Elder AI Guardian</Typography>
            <Typography variant="caption">{user?.email}</Typography>
          </Box>
          <Divider />
          <List>
            {navItems.map((item) => (
              <ListItem
                key={item.path}
                button
                onClick={() => handleNav(item.path)}
                selected={isActive(item.path)}
                sx={{
                  ...(item.highlight && { bgcolor: '#f3e5f5' }),
                  ...(item.color === 'error' && { color: 'error.main' }),
                }}
              >
                <ListItemIcon sx={{ color: item.color === 'error' ? 'error.main' : item.highlight ? 'secondary.main' : 'inherit' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
            <Divider />
            <ListItem button onClick={handleLogout}>
              <ListItemIcon><LogoutIcon /></ListItemIcon>
              <ListItemText primary="Logout" />
            </ListItem>
          </List>
        </Box>
      </Drawer>

      <Container component="main" sx={{ flexGrow: 1, py: 3 }}>
        <Outlet />
      </Container>

      {/* Footer */}
      <Box sx={{ py: 1, textAlign: 'center', bgcolor: 'grey.100' }}>
        <Typography variant="caption" color="text.secondary">
          Powered by Microsoft Foundry • Azure MCP • Agent Framework • Agentic DevOps
        </Typography>
      </Box>
    </Box>
  );
};

export default Layout;