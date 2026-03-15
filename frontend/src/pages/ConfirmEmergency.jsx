import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Container
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import api from '../services/api';

const ConfirmEmergency = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [responseTime, setResponseTime] = useState(null);
  
  const token = searchParams.get('token');
  const contact = searchParams.get('contact');
  const emergency = searchParams.get('emergency');

  useEffect(() => {
    const confirmEmergency = async () => {
      try {
        const response = await api.get('/emergency/confirm', {
          params: { token, contact, emergency }
        });
        
        if (response.data.success) {
          setStatus('success');
          setResponseTime(response.data.response_time);
        } else {
          setStatus('error');
        }
      } catch (error) {
        console.error('Confirmation failed:', error);
        setStatus('error');
      }
    };

    if (token && contact && emergency) {
      confirmEmergency();
    } else {
      setStatus('error');
    }
  }, [token, contact, emergency]);

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            {status === 'loading' && (
              <>
                <CircularProgress size={60} sx={{ mb: 3 }} />
                <Typography variant="h5" gutterBottom>
                  Confirming Emergency...
                </Typography>
                <Typography color="text.secondary">
                  Please wait while we process your confirmation
                </Typography>
              </>
            )}

            {status === 'success' && (
              <>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
                >
                  <CheckCircleIcon
                    sx={{ fontSize: 80, color: 'success.main', mb: 2 }}
                  />
                </motion.div>
                
                <Typography variant="h4" gutterBottom color="success.main">
                  Thank You!
                </Typography>
                
                <Typography variant="h6" gutterBottom>
                  Emergency Confirmed
                </Typography>
                
                {responseTime && (
                  <Alert severity="info" sx={{ my: 2 }}>
                    Response time: {responseTime} seconds
                  </Alert>
                )}
                
                <Typography paragraph>
                  Your confirmation has been recorded. The emergency services
                  have been notified that help is on the way.
                </Typography>
                
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  onClick={() => navigate('/family-dashboard')}
                  sx={{ mt: 2 }}
                >
                  Go to Family Dashboard
                </Button>
              </>
            )}

            {status === 'error' && (
              <>
                <ErrorIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
                
                <Typography variant="h4" gutterBottom color="error.main">
                  Confirmation Failed
                </Typography>
                
                <Alert severity="error" sx={{ my: 2 }}>
                  The confirmation link is invalid or has expired.
                </Alert>
                
                <Typography paragraph>
                  Please contact emergency services directly if this is an emergency.
                </Typography>
                
                <Button
                  variant="contained"
                  color="primary"
                  size="large"
                  onClick={() => navigate('/')}
                  sx={{ mt: 2 }}
                >
                  Go to Home
                </Button>
              </>
            )}
          </Paper>
        </motion.div>
      </Box>
    </Container>
  );
};

export default ConfirmEmergency;
