import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Avatar,
  LinearProgress,
  Chip,
  Button,
  IconButton,
  Alert,
  AlertTitle,
  Divider,
  Tooltip,
  Badge,
  Collapse,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Warning as WarningIcon,
  MedicalServices as MedicalIcon,
  LocalPharmacy as PharmacyIcon,
  Favorite as HeartIcon,
  Spa as WellnessIcon,
  Notifications as NotificationIcon,
  ArrowForward as ArrowForwardIcon,
  Phone as PhoneIcon,
  Message as MessageIcon,
  Videocam as VideoIcon,
  Memory as MemoryIcon,
  Hub as HubIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from 'react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Legend,
  Filler,
} from 'chart.js';
import { format, subDays } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import api from '../services/api';
import { useWebSocket } from '../contexts/WebSocketContext';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Legend,
  Filler
);

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { lastMessage, isConnected, heroTechnologies, sendMessage } = useWebSocket();
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [showDevOps, setShowDevOps] = useState(false);
  const [autoHealEnabled, setAutoHealEnabled] = useState(true);
  const [healingInProgress, setHealingInProgress] = useState(false);

  // Fetch dashboard data
  const { data: dashboardData, isLoading, refetch: refetchDashboard } = useQuery(
    'dashboard',
    async () => {
      const response = await api.get('/dashboard/');
      return response.data;
    },
    {
      refetchInterval: 30000,
    }
  );

  // Fetch system metrics
  const { data: metricsData, refetch: refetchMetrics } = useQuery(
    'metrics',
    async () => {
      const response = await api.get('/metrics');
      return response.data;
    },
    {
      refetchInterval: 10000,
      onSuccess: (data) => {
        setMetrics(data);
      },
    }
  );

  // Trigger self-healing mutation
  const healMutation = useMutation(
    async () => {
      setHealingInProgress(true);
      const response = await api.post('/devops/heal');
      return response.data;
    },
    {
      onSuccess: (data) => {
        setHealingInProgress(false);
        setAlerts((prev) => [
          {
            id: `heal_${Date.now()}`,
            severity: 'success',
            title: 'Self-Healing Complete',
            message: `Actions taken: ${data.actions_taken.join(', ') || 'None needed'}`,
            timestamp: new Date().toISOString(),
          },
          ...prev,
        ].slice(0, 5));
        refetchMetrics();
        refetchDashboard();
      },
      onError: (error) => {
        setHealingInProgress(false);
        setAlerts((prev) => [
          {
            id: `heal_error_${Date.now()}`,
            severity: 'error',
            title: 'Self-Healing Failed',
            message: error.response?.data?.detail || 'Unknown error',
            timestamp: new Date().toISOString(),
          },
          ...prev,
        ].slice(0, 5));
      },
    }
  );

  // Handle real-time alerts from WebSocket
  useEffect(() => {
    if (lastMessage) {
      try {
        const message = typeof lastMessage === 'string' ? JSON.parse(lastMessage) : lastMessage;

        if (message.type === 'alert') {
          setAlerts((prev) => [message.data, ...prev].slice(0, 5));
        }

        if (message.type === 'metrics') {
          setMetrics(message.data);
        }

        if (message.type === 'fall_detected') {
          setAlerts((prev) => [
            {
              id: `fall_${Date.now()}`,
              severity: 'error',
              title: '🚨 Fall Detected!',
              message: 'Emergency services have been notified',
              action: '/emergency',
              timestamp: message.timestamp,
            },
            ...prev,
          ].slice(0, 5));
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  // Auto-heal when components are unhealthy
  useEffect(() => {
    if (autoHealEnabled && metrics?.components) {
      const unhealthyComponents = Object.entries(metrics.components)
        .filter(([_, healthy]) => !healthy)
        .map(([name]) => name);

      if (unhealthyComponents.length > 0 && !healingInProgress) {
        console.log('Unhealthy components detected:', unhealthyComponents);
        healMutation.mutate();
      }
    }
  }, [metrics, autoHealEnabled, healingInProgress]);

  // Medication adherence chart data
  const adherenceData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Medication Adherence',
        data: [95, 88, 92, 85, 98, 100, 90],
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Wellness trends chart data
  const wellnessData = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
      {
        label: 'Mood Score',
        data: [4.2, 4.5, 4.8, 4.6],
        backgroundColor: 'rgba(153, 102, 255, 0.2)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 2,
        tension: 0.4,
      },
      {
        label: 'Activity Level',
        data: [65, 72, 78, 70],
        backgroundColor: 'rgba(255, 159, 64, 0.2)',
        borderColor: 'rgba(255, 159, 64, 1)',
        borderWidth: 2,
        tension: 0.4,
      },
    ],
  };

  // Scam detection stats
  const scamData = {
    labels: ['Safe', 'Suspicious', 'Scam'],
    datasets: [
      {
        data: [45, 12, 3],
        backgroundColor: ['#4caf50', '#ff9800', '#f44336'],
        borderWidth: 0,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  };

  const handleManualHeal = () => {
    healMutation.mutate();
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <LinearProgress sx={{ width: '100%' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Hero Technologies Banner */}
      <Paper
        sx={{
          p: 2,
          mb: 3,
          background: 'linear-gradient(135deg, #1a237e 0%, #311b92 100%)',
          color: 'white',
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                <MemoryIcon sx={{ mr: 1 }} />
                Microsoft Hero Technologies
              </Typography>
              <Chip
                label={isConnected ? 'Connected' : 'Disconnected'}
                size="small"
                color={isConnected ? 'success' : 'error'}
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              {heroTechnologies?.foundry && (
                <Tooltip title="Microsoft Foundry Active - Model Router">
                  <Chip
                    icon={<MemoryIcon />}
                    label="Foundry"
                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                  />
                </Tooltip>
              )}
              {heroTechnologies?.mcp && (
                <Tooltip title="Azure MCP Active - Tool Integration">
                  <Chip
                    icon={<HubIcon />}
                    label="MCP"
                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                  />
                </Tooltip>
              )}
              {heroTechnologies?.agent_framework && (
                <Tooltip title="Microsoft Agent Framework Active - Supervisor">
                  <Chip
                    icon={<SettingsIcon />}
                    label="Agent Framework"
                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                  />
                </Tooltip>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Welcome Section */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h4" gutterBottom>
              Welcome back, {user?.name || 'User'}! 👋
            </Typography>
            <Typography variant="body1">
              Your health and safety are our top priority. Here's your daily summary.
            </Typography>
          </Grid>
          <Grid item xs={12} md={4} sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
            <Button
              variant="contained"
              color="error"
              size="large"
              startIcon={<WarningIcon />}
              onClick={() => navigate('/emergency')}
              sx={{
                mr: 1,
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': { boxShadow: '0 0 0 0 rgba(244, 67, 54, 0.7)' },
                  '70%': { boxShadow: '0 0 0 10px rgba(244, 67, 54, 0)' },
                  '100%': { boxShadow: '0 0 0 0 rgba(244, 67, 54, 0)' },
                },
              }}
            >
              SOS Emergency
            </Button>
            <IconButton color="inherit" sx={{ bgcolor: 'rgba(255,255,255,0.1)' }}>
              <Badge badgeContent={alerts.length} color="error">
                <NotificationIcon />
              </Badge>
            </IconButton>
          </Grid>
        </Grid>
      </Paper>

      {/* Alerts Section */}
      <AnimatePresence>
        {alerts.length > 0 && (
          <Box sx={{ mb: 3 }}>
            {alerts.map((alert, index) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: 100 }}
                transition={{ delay: index * 0.1 }}
              >
                <Alert
                  severity={alert.severity}
                  sx={{ mb: 1 }}
                  action={
                    alert.action ? (
                      <Button color="inherit" size="small" onClick={() => navigate(alert.action)}>
                        View
                      </Button>
                    ) : null
                  }
                  onClose={() => setAlerts((prev) => prev.filter(a => a.id !== alert.id))}
                >
                  <AlertTitle>{alert.title}</AlertTitle>
                  {alert.message}
                </Alert>
              </motion.div>
            ))}
          </Box>
        )}
      </AnimatePresence>

      {/* DevOps Dashboard Section */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SpeedIcon color="primary" />
            <Typography variant="h6">System Health & DevOps</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoHealEnabled}
                  onChange={(e) => setAutoHealEnabled(e.target.checked)}
                  size="small"
                />
              }
              label="Auto-Heal"
            />
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon />}
              onClick={() => setShowDevOps(!showDevOps)}
            >
              {showDevOps ? 'Hide' : 'Show'} Details
            </Button>
            <Button
              variant="contained"
              size="small"
              color="warning"
              startIcon={<SecurityIcon />}
              onClick={handleManualHeal}
              disabled={healingInProgress}
            >
              {healingInProgress ? 'Healing...' : 'Manual Heal'}
            </Button>
          </Box>
        </Box>

        <Collapse in={showDevOps}>
          {metrics && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        Uptime
                      </Typography>
                      <Typography variant="h5">
                        {Math.floor((metrics.uptime_seconds || metrics.uptime || 0) / 3600)}h{' '}
                        {Math.floor(((metrics.uptime_seconds || metrics.uptime || 0) % 3600) / 60)}m
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {(metrics.uptime_seconds || metrics.uptime || 0).toFixed(0)} seconds
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        Total Requests
                      </Typography>
                      <Typography variant="h5">
                        {metrics.total_requests?.toLocaleString() || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Since startup
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        Active WebSockets
                      </Typography>
                      <Typography variant="h5">
                        {metrics.active_websockets || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {metrics.connections?.users || 0} unique users
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        MCP Contexts
                      </Typography>
                      <Typography variant="h5">
                        {metrics.mcp_contexts || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Active conversations
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                Component Health:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {metrics.components && Object.entries(metrics.components).map(([key, healthy]) => (
                  <Tooltip key={key} title={`${key}: ${healthy ? 'Healthy' : 'Unhealthy'}`}>
                    <Chip
                      label={key.replace('_', ' ')}
                      color={healthy ? 'success' : 'error'}
                      size="small"
                      icon={healthy ? <CheckCircleIcon /> : <ErrorIcon />}
                      variant={healthy ? 'filled' : 'outlined'}
                    />
                  </Tooltip>
                ))}
              </Box>

              {metrics.model_stats && (
                <>
                  <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                    Model Statistics:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    {Object.entries(metrics.model_stats).map(([key, value]) => (
                      <Typography key={key} variant="caption" component="div">
                        <strong>{key}:</strong> {value}
                      </Typography>
                    ))}
                  </Box>
                </>
              )}
            </Box>
          )}
        </Collapse>
      </Paper>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <motion.div whileHover={{ scale: 1.05 }} transition={{ type: 'spring', stiffness: 300 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    <MedicalIcon />
                  </Avatar>
                  <Typography variant="h6">Health Score</Typography>
                </Box>
                <Typography variant="h3" color="primary" gutterBottom>
                  {dashboardData?.healthScore || 85}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={dashboardData?.healthScore || 85}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div whileHover={{ scale: 1.05 }} transition={{ type: 'spring', stiffness: 300 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                    <PharmacyIcon />
                  </Avatar>
                  <Typography variant="h6">Medications</Typography>
                </Box>
                <Typography variant="h3" color="success.main" gutterBottom>
                  {dashboardData?.medicationsTaken || 0}/{dashboardData?.totalMedications || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {dashboardData?.nextMedication || 'No upcoming reminders'}
                </Typography>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div whileHover={{ scale: 1.05 }} transition={{ type: 'spring', stiffness: 300 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                    <HeartIcon />
                  </Avatar>
                  <Typography variant="h6">Heart Rate</Typography>
                </Box>
                <Typography variant="h3" color="warning.main" gutterBottom>
                  {dashboardData?.heartRate || 72}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  BPM - Normal range
                </Typography>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div whileHover={{ scale: 1.05 }} transition={{ type: 'spring', stiffness: 300 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                    <WellnessIcon />
                  </Avatar>
                  <Typography variant="h6">Steps Today</Typography>
                </Box>
                <Typography variant="h3" color="info.main" gutterBottom>
                  {dashboardData?.steps || 3245}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Goal: 5000 steps
                </Typography>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Medication Adherence - This Week
            </Typography>
            <Box sx={{ height: 300 }}>
              <Line data={adherenceData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Scam Detection Stats
            </Typography>
            <Box sx={{ height: 300 }}>
              <Doughnut data={scamData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Wellness Trends
            </Typography>
            <Box sx={{ height: 300 }}>
              <Bar data={wellnessData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<MedicalIcon />}
              onClick={() => navigate('/medication')}
              sx={{ py: 1.5 }}
            >
              Log Medication
            </Button>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<WellnessIcon />}
              onClick={() => navigate('/wellness')}
              sx={{ py: 1.5 }}
            >
              Track Mood
            </Button>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<PhoneIcon />}
              onClick={() => window.open('tel:+1234567890')}
              sx={{ py: 1.5 }}
            >
              Call Family
            </Button>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<VideoIcon />}
              onClick={() => navigate('/family-portal')}
              sx={{ py: 1.5 }}
            >
              Video Call
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Footer with Hero Tech Attribution */}
      <Box sx={{ mt: 3, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          Powered by Microsoft Hero Technologies: Foundry • MCP • Agent Framework • Agentic DevOps
        </Typography>
      </Box>
    </Box>
  );
};

export default Dashboard;