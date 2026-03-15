import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuthStore } from './stores/authStore';
import PanicMode from './components/PanicMode';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Emergency from './pages/Emergency';
import Medication from './pages/Medication';
import ScamDetection from './pages/ScamDetection';
import Wellness from './pages/Wellness';
import FamilyPortal from './pages/FamilyPortal';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';
import NotFound from './pages/NotFound';
import ConfirmEmergency from './pages/ConfirmEmergency';
import ProtectedRoute from './components/ProtectedRoute';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { AzureProvider } from './contexts/AzureContext';

// ===== ADD THIS IMPORT =====
import HeroShowcase from './pages/HeroShowcase';
// ===========================

function App() {
  const { isLoading, initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <AzureProvider>
      <WebSocketProvider>
        <PanicMode>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/confirm-emergency" element={<ConfirmEmergency />} />
            
            {/* Protected Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="chat" element={<Chat />} />
              <Route path="emergency" element={<Emergency />} />
              <Route path="medication" element={<Medication />} />
              <Route path="scam-detection" element={<ScamDetection />} />
              <Route path="wellness" element={<Wellness />} />
              <Route path="family-portal" element={<FamilyPortal />} />
              <Route path="settings" element={<Settings />} />
              {/* ===== ADD THIS ROUTE ===== */}
              <Route path="hero-showcase" element={<HeroShowcase />} />
              {/* ========================== */}
            </Route>
            
            {/* 404 Route */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </PanicMode>
      </WebSocketProvider>
    </AzureProvider>
  );
}

export default App;
