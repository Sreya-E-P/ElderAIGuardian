import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Chip,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from 'react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { useAuthStore } from '../stores/authStore';
import { useWebSocket } from '../contexts/WebSocketContext';
import api from '../services/api';

const FamilyPortal = () => {
  const { elderId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { lastMessage, isConnected, sendMessage } = useWebSocket();
  const [pendingAlerts, setPendingAlerts] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);

  // Subscribe to alerts when component mounts
  useEffect(() => {
    if (isConnected && elderId) {
      sendMessage('subscribe_alerts', { user_id: elderId });
    }
    
    return () => {
      if (isConnected) {
        sendMessage('unsubscribe_alerts', {});
      }
    };
  }, [isConnected, elderId, sendMessage]);

  // Handle incoming pending alerts
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'pending_alert') {
      setPendingAlerts(prev => [lastMessage.data, ...prev].slice(0, 20));
      
      // Show browser notification if permitted
      if (Notification.permission === 'granted') {
        new Notification(' New Emergency Alert', {
          body: lastMessage.data.message || 'Your loved one needs immediate attention',
          icon: '/favicon.ico'
        });
      }
    }
  }, [lastMessage]);

  // Request notification permission
  useEffect(() => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Fetch dashboard data
  const { data, isLoading, refetch } = useQuery(
    ['familyDashboard', elderId],
    async () => {
      const response = await api.get(`/family/dashboard/${elderId}`);
      return response.data;
    },
    {
      onSuccess: (data) => {
        setDashboardData(data);
      },
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Acknowledge alert mutation
  const acknowledgeMutation = useMutation(
    async (alertId) => {
      const response = await api.post(`/family/acknowledge/${alertId}`);
      return response.data;
    },
    {
      onSuccess: (data) => {
        // Remove acknowledged alert from pending list
        setPendingAlerts(prev => prev.filter(alert => alert.id !== data.alert_id));
        refetch();
      },
    }
  );

  const handleAcknowledge = (alertId) => {
    acknowledgeMutation.mutate(alertId);
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          Family Guardian Portal
        </Typography>
        <Typography variant="body1">
          Real-time updates for your loved one's safety and wellbeing
        </Typography>
        {!isConnected && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            WebSocket disconnected. Real-time updates may be delayed.
          </Alert>
        )}
      </Paper>

      {/* Pending Alerts Section */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <WarningIcon color="error" sx={{ mr: 1 }} />
          Pending Alerts {pendingAlerts.length > 0 && `(${pendingAlerts.length})`}
        </Typography>
        {pendingAlerts.length === 0 ? (
          <Typography color="text.secondary">No pending alerts</Typography>
        ) : (
          <List>
            {pendingAlerts.map((alert, index) => (
              <React.Fragment key={index}>
                <ListItem
                  secondaryAction={
                    <Button
                      variant="contained"
                      color="primary"
                      size="small"
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={acknowledgeMutation.isLoading}
                    >
                      Acknowledge
                    </Button>
                  }
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1">
                          {alert.message || 'Emergency Alert'}
                        </Typography>
                        <Chip
                          label={`Level ${alert.escalation_level || 1}`}
                          size="small"
                          color={alert.escalation_level > 1 ? 'error' : 'warning'}
                        />
                      </Box>
                    }
                    secondary={
                      <>
                        <Typography variant="body2" color="text.secondary">
                          Type: {alert.type}  Sent: {new Date(alert.sent_at).toLocaleString()}
                        </Typography>
                        {alert.time_elapsed_seconds > 300 && (
                          <Typography variant="caption" color="error">
                             Response overdue
                          </Typography>
                        )}
                      </>
                    }
                  />
                </ListItem>
                {index < pendingAlerts.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>

      {/* Dashboard Stats */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Health Status
              </Typography>
              <Typography variant="h4" color="primary">
                {dashboardData?.guardian_status || 'ACTIVE'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Emergency Contacts
              </Typography>
              <Typography variant="h4">
                {dashboardData?.emergency_contacts || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Response Rate
              </Typography>
              <Typography variant="h4" color="success.main">
                {dashboardData?.closed_loop_metrics?.confirmation_rate || 100}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Avg Response Time
              </Typography>
              <Typography variant="h4">
                {dashboardData?.closed_loop_metrics?.avg_response_time_seconds || 0}s
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Emergency Contacts List */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Emergency Contacts
        </Typography>
        <List>
          {dashboardData?.emergency_contacts_list?.map((contact, index) => (
            <React.Fragment key={contact.id}>
              <ListItem>
                <Avatar sx={{ mr: 2, bgcolor: contact.priority === 'primary' ? 'primary.main' : 'secondary.main' }}>
                  <PersonIcon />
                </Avatar>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">{contact.name}</Typography>
                      <Chip
                        label={contact.priority}
                        size="small"
                        color={contact.priority === 'primary' ? 'primary' : 'default'}
                      />
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body2">{contact.relationship}</Typography>
                      <Typography variant="body2">{contact.phone}</Typography>
                      {contact.email && <Typography variant="body2">{contact.email}</Typography>}
                    </>
                  }
                />
                <Button
                  variant="outlined"
                  startIcon={<PhoneIcon />}
                  href={`tel:${contact.phone}`}
                  sx={{ mr: 1 }}
                >
                  Call
                </Button>
                {contact.email && (
                  <Button
                    variant="outlined"
                    startIcon={<EmailIcon />}
                    href={`mailto:${contact.email}`}
                  >
                    Email
                  </Button>
                )}
              </ListItem>
              {index < dashboardData?.emergency_contacts_list.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </Paper>

      {/* Recent Activity */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent Activity
        </Typography>
        <List>
          {dashboardData?.recent_activity?.map((activity, index) => (
            <React.Fragment key={activity.id}>
              <ListItem>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        {activity.type} - {activity.emergency_type}
                      </Typography>
                      <Chip
                        label={activity.severity}
                        size="small"
                        color={activity.severity === 'CRITICAL' ? 'error' : 'warning'}
                      />
                      {activity.confirmed && (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="Confirmed"
                          size="small"
                          color="success"
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body2">
                        {new Date(activity.timestamp).toLocaleString()}
                      </Typography>
                      {activity.response_time && (
                        <Typography variant="caption" color="text.secondary">
                          Response time: {activity.response_time}s
                        </Typography>
                      )}
                    </>
                  }
                />
              </ListItem>
              {index < dashboardData?.recent_activity.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </Paper>
    </Box>
  );
};

export default FamilyPortal;
