import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Avatar,
  Alert,
  AlertTitle,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  IconButton,
  CircularProgress,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  People as PeopleIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  MedicalServices as MedicalIcon,
  LocalHospital as HospitalIcon,
  FireTruck as FireTruckIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useMutation, useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../services/api';

const steps = ['Emergency Detected', 'Notifying Contacts', 'Dispatching Help', 'Resolved'];

const Emergency = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { sendMessage, lastMessage, isConnected } = useWebSocket();
  const [activeStep, setActiveStep] = useState(0);
  const [emergencyId, setEmergencyId] = useState(null);
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [countdown, setCountdown] = useState(30);
  const [openConfirmDialog, setOpenConfirmDialog] = useState(false);
  const [emergencyType, setEmergencyType] = useState('medical');
  const [customMessage, setCustomMessage] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  // Get user location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: position.coords.accuracy,
          });
          setLocationError(null);
        },
        (error) => {
          setLocationError(error.message);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    } else {
      setLocationError('Geolocation not supported');
    }
  }, []);

  // Countdown timer
  useEffect(() => {
    if (activeStep === 1 && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else if (countdown === 0 && activeStep === 1) {
      setActiveStep(2);
    }
  }, [activeStep, countdown]);

  // Handle WebSocket messages â€” fixed: lastMessage is already parsed object
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = typeof lastMessage === 'string' ? JSON.parse(lastMessage) : lastMessage;
        if (data.type === 'emergency_update') {
          handleEmergencyUpdate(data.data);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  const handleEmergencyUpdate = (data) => {
    if (data.emergency_id === emergencyId) {
      if (data.status === 'resolved') {
        setActiveStep(3);
      } else if (data.status === 'dispatched') {
        setActiveStep(2);
      }
    }
  };

  // Trigger SOS mutation
  const sosMutation = useMutation(
    async (data) => {
      const response = await api.post('/emergency/sos', data);
      return response.data;
    },
    {
      onSuccess: (data) => {
        setEmergencyId(data.emergency_id);
        setActiveStep(1);
        setSuggestions(data.suggestions || []);

        if (isConnected) {
          sendMessage('emergency', {
            emergency_id: data.emergency_id,
            status: 'triggered',
            message: customMessage || 'SOS triggered',
          });
        }
      },
      onError: (error) => {
        console.error('Failed to trigger SOS:', error);
      },
    }
  );

  // Resolve emergency mutation
  const resolveMutation = useMutation(
    async () => {
      const response = await api.post(`/emergency/${emergencyId}/resolve`, {
        resolved_by: user?.id,
        resolution: 'user_confirmed_safe',
      });
      return response.data;
    },
    {
      onSuccess: (data) => {
        setActiveStep(3);
        setSuggestions(data.suggestions || []);
      },
    }
  );

  const handleSOSTrigger = () => {
    setOpenConfirmDialog(false);

    const sosData = {
      userId: user?.id,
      message: customMessage || `Emergency: ${emergencyType}`,
      location: location ? {
        latitude: location.lat,
        longitude: location.lng,
        accuracy: location.accuracy,
      } : null,
      emergencyType: emergencyType,
    };

    sosMutation.mutate(sosData);
  };

  const handleCancel = () => {
    setOpenConfirmDialog(false);
    setActiveStep(0);
    setEmergencyId(null);
    setCountdown(30);
    setSuggestions([]);
  };

  const handleResolve = () => {
    resolveMutation.mutate();
  };

  const getEmergencyIcon = (type) => {
    switch (type) {
      case 'medical':
        return <MedicalIcon sx={{ fontSize: 40 }} />;
      case 'fire':
        return <FireTruckIcon sx={{ fontSize: 40 }} />;
      case 'security':
        return <SecurityIcon sx={{ fontSize: 40 }} />;
      default:
        return <WarningIcon sx={{ fontSize: 40 }} />;
    }
  };

  const getEmergencyColor = (type) => {
    switch (type) {
      case 'medical':
        return 'error';
      case 'fire':
        return 'warning';
      case 'security':
        return 'info';
      default:
        return 'error';
    }
  };

  if (sosMutation.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <LinearProgress sx={{ width: '100%' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          bgcolor: 'error.main',
          color: 'white',
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <WarningIcon sx={{ fontSize: 48 }} />
          </Grid>
          <Grid item xs>
            <Typography variant="h4" gutterBottom>
              Emergency Response System
            </Typography>
            <Typography variant="body1">
              One-touch access to emergency services and family notifications
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Active Emergency */}
      {activeStep > 0 && (
        <Paper sx={{ p: 3, mb: 3, bgcolor: 'warning.light' }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item>
              <CircularProgress color="error" size={60} />
            </Grid>
            <Grid item xs>
              <Typography variant="h5" gutterBottom color="error">
                Active Emergency in Progress
              </Typography>
              <Typography variant="body1">
                Emergency ID: {emergencyId}
              </Typography>
            </Grid>
            <Grid item>
              <Button
                variant="contained"
                color="success"
                size="large"
                onClick={handleResolve}
                disabled={resolveMutation.isLoading}
              >
                {resolveMutation.isLoading ? 'Resolving...' : 'Mark as Resolved'}
              </Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Suggestions Section */}
      {suggestions.length > 0 && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'info.light', color: 'white' }}>
          <Typography variant="h6" gutterBottom>
            ðŸš¨ Important Instructions
          </Typography>
          <List>
            {suggestions.map((suggestion, index) => (
              <ListItem key={index}>
                <ListItemText primary={suggestion} />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Stepper */}
      {activeStep > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Paper>
      )}

      <Grid container spacing={3}>
        {/* SOS Button */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                variant="contained"
                color="error"
                size="large"
                onClick={() => setOpenConfirmDialog(true)}
                disabled={activeStep > 0}
                sx={{
                  width: 200,
                  height: 200,
                  borderRadius: '50%',
                  fontSize: '2rem',
                  boxShadow: 3,
                  '&:hover': {
                    boxShadow: 6,
                  },
                }}
              >
                SOS
              </Button>
            </motion.div>
            <Typography variant="h6" sx={{ mt: 2 }} color="error">
              Press for Emergency
            </Typography>
          </Paper>
        </Grid>

        {/* Emergency Options */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Emergency Options
            </Typography>
            <Grid container spacing={2}>
              {[
                { type: 'medical', label: 'Medical Emergency', icon: <MedicalIcon /> },
                { type: 'fire', label: 'Fire Emergency', icon: <FireTruckIcon /> },
                { type: 'security', label: 'Security Threat', icon: <SecurityIcon /> },
                { type: 'fall', label: 'Fall Detected', icon: <WarningIcon /> },
              ].map((option) => (
                <Grid item xs={6} key={option.type}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      bgcolor: activeStep === 0 ? 'background.paper' : 'action.disabledBackground',
                      opacity: activeStep === 0 ? 1 : 0.5,
                    }}
                    onClick={() => {
                      if (activeStep === 0) {
                        setEmergencyType(option.type);
                        setOpenConfirmDialog(true);
                      }
                    }}
                  >
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Avatar
                        sx={{
                          mx: 'auto',
                          mb: 1,
                          bgcolor: getEmergencyColor(option.type) + '.main',
                          width: 56,
                          height: 56,
                        }}
                      >
                        {option.icon}
                      </Avatar>
                      <Typography variant="body2">{option.label}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Emergency Contacts */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Emergency Contacts
            </Typography>
            <List>
              {[
                { name: 'Emergency Services', phone: '911', type: 'services' },
                { name: 'Primary Contact - John Doe', phone: '+1 (555) 123-4567', type: 'family' },
                { name: 'Secondary Contact - Jane Doe', phone: '+1 (555) 987-6543', type: 'family' },
              ].map((contact, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: contact.type === 'services' ? 'error.main' : 'primary.main' }}>
                        {contact.type === 'services' ? <HospitalIcon /> : <PeopleIcon />}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={contact.name}
                      secondary={contact.phone}
                    />
                    <ListItemSecondaryAction>
                      <IconButton edge="end" color="primary" href={`tel:${contact.phone}`}>
                        <PhoneIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < 2 && <Divider variant="inset" component="li" />}
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Location Information */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Your Location
            </Typography>
            {location ? (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <LocationIcon color="primary" sx={{ mr: 1 }} />
                  <Typography>
                    Latitude: {location.lat.toFixed(6)}, Longitude: {location.lng.toFixed(6)}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="body2" color="success.main">
                    Location accuracy: {location.accuracy.toFixed(0)} meters
                  </Typography>
                </Box>
              </>
            ) : (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {locationError ? (
                  <>
                    <CancelIcon color="error" sx={{ mr: 1 }} />
                    <Typography color="error">{locationError}</Typography>
                  </>
                ) : (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    <Typography>Getting your location...</Typography>
                  </>
                )}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Confirmation Dialog */}
      <Dialog open={openConfirmDialog} onClose={() => setOpenConfirmDialog(false)}>
        <DialogTitle sx={{ bgcolor: 'error.main', color: 'white' }}>
          <WarningIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Confirm Emergency
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <DialogContentText>
            You are about to trigger an emergency alert. This will:
          </DialogContentText>
          <List>
            <ListItem>
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'error.main' }}>
                  <PhoneIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Notify Emergency Services"
                secondary="911 will be contacted automatically"
              />
            </ListItem>
            <ListItem>
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <PeopleIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Alert Family Members"
                secondary="Your emergency contacts will be notified"
              />
            </ListItem>
            <ListItem>
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <LocationIcon />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Share Your Location"
                secondary="Your current location will be shared"
              />
            </ListItem>
          </List>

          <TextField
            fullWidth
            multiline
            rows={3}
            margin="normal"
            label="Additional Information (Optional)"
            placeholder="Describe what's happening..."
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancel} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={handleSOSTrigger}
            variant="contained"
            color="error"
            autoFocus
          >
            Confirm SOS
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Emergency;