import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Slider,
  Chip,
  Alert,
  AlertTitle,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  TextField,
} from '@mui/material';
import {
  Spa as SpaIcon,
  DirectionsWalk as WalkIcon,
  Bedtime as SleepIcon,
  WaterDrop as WaterIcon,
  Lightbulb as TipIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { useMutation, useQuery } from 'react-query';
import { motion } from 'framer-motion';
import { useAuthStore } from '../stores/authStore';
import api from '../services/api';

const moodEmojis = ['😢', '😕', '😐', '🙂', '😄'];
const moodLabels = ['Terrible', 'Bad', 'Okay', 'Good', 'Great'];

const Wellness = () => {
  const { user } = useAuthStore();
  const [mood, setMood] = useState(3);
  const [sleepHours, setSleepHours] = useState(7);
  const [steps, setSteps] = useState('');
  const [waterGlasses, setWaterGlasses] = useState(0);
  const [savedItems, setSavedItems] = useState([]);

  // Fetch wellness report
  const { data: report, isLoading: reportLoading } = useQuery(
    'wellnessReport',
    async () => {
      const response = await api.get('/wellness/report?days=7');
      return response.data;
    },
    { retry: 1 }
  );

  // Fetch wellness tip
  const { data: tipData } = useQuery(
    'wellnessTip',
    async () => {
      const response = await api.get('/wellness/tips');
      return response.data;
    },
    { retry: 1 }
  );

  const moodMutation = useMutation(
    async () => {
      const response = await api.post('/wellness/mood', {
        mood,
        label: moodLabels[mood - 1],
        timestamp: new Date().toISOString(),
      });
      return response.data;
    },
    {
      onSuccess: (data) => {
        setSavedItems(prev => [{ type: 'mood', message: data.message || `Mood logged: ${moodLabels[mood - 1]}` }, ...prev]);
      },
    }
  );

  const sleepMutation = useMutation(
    async () => {
      const response = await api.post('/wellness/sleep', {
        hours: sleepHours,
        quality: sleepHours >= 7 ? 'good' : sleepHours >= 5 ? 'fair' : 'poor',
        timestamp: new Date().toISOString(),
      });
      return response.data;
    },
    {
      onSuccess: (data) => {
        setSavedItems(prev => [{ type: 'sleep', message: data.message || `Sleep logged: ${sleepHours} hours` }, ...prev]);
      },
    }
  );

  const activityMutation = useMutation(
    async () => {
      const response = await api.post('/wellness/activity', {
        activity_type: 'walking',
        steps: parseInt(steps) || 0,
        timestamp: new Date().toISOString(),
      });
      return response.data;
    },
    {
      onSuccess: (data) => {
        setSavedItems(prev => [{ type: 'activity', message: data.message || `Activity logged: ${steps} steps` }, ...prev]);
        setSteps('');
      },
    }
  );

  const waterMutation = useMutation(
    async (glasses) => {
      const response = await api.post('/wellness/water', {
        glasses,
        timestamp: new Date().toISOString(),
      });
      return response.data;
    },
    {
      onSuccess: (data) => {
        setSavedItems(prev => [{ type: 'water', message: data.message || `Water logged: ${waterGlasses} glasses` }, ...prev]);
      },
    }
  );

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(135deg, #00695c 0%, #004d40 100%)',
          color: 'white',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <SpaIcon sx={{ fontSize: 48 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">Wellness Tracking</Typography>
            <Typography variant="body1" sx={{ opacity: 0.9 }}>
              Track your mood, sleep, activity, and hydration — monitored by your Wellness Agent
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Daily Tip */}
      {tipData?.tip && (
        <Alert icon={<TipIcon />} severity="info" sx={{ mb: 3 }}>
          <AlertTitle>Today's Wellness Tip</AlertTitle>
          {tipData.tip}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Mood Tracker */}
        <Grid item xs={12} md={6}>
          <motion.div whileHover={{ scale: 1.01 }}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                  <SpaIcon color="success" sx={{ fontSize: 32 }} />
                  <Typography variant="h6" fontWeight="bold">How are you feeling?</Typography>
                </Box>

                <Box sx={{ textAlign: 'center', mb: 2 }}>
                  <Typography variant="h1">{moodEmojis[mood - 1]}</Typography>
                  <Typography variant="h6" color="success.main">{moodLabels[mood - 1]}</Typography>
                </Box>

                <Slider
                  value={mood}
                  min={1}
                  max={5}
                  step={1}
                  marks
                  onChange={(_, val) => setMood(val)}
                  color="success"
                  sx={{ mb: 2 }}
                />

                <Button
                  fullWidth
                  variant="contained"
                  color="success"
                  onClick={() => moodMutation.mutate()}
                  disabled={moodMutation.isLoading}
                  startIcon={moodMutation.isLoading ? <CircularProgress size={18} color="inherit" /> : <CheckIcon />}
                >
                  {moodMutation.isLoading ? 'Saving...' : 'Log Mood'}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Sleep Tracker */}
        <Grid item xs={12} md={6}>
          <motion.div whileHover={{ scale: 1.01 }}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                  <SleepIcon color="primary" sx={{ fontSize: 32 }} />
                  <Typography variant="h6" fontWeight="bold">Last Night's Sleep</Typography>
                </Box>

                <Box sx={{ textAlign: 'center', mb: 2 }}>
                  <Typography variant="h2" color="primary">{sleepHours}h</Typography>
                  <Chip
                    label={sleepHours >= 7 ? 'Good sleep' : sleepHours >= 5 ? 'Fair sleep' : 'Need more rest'}
                    color={sleepHours >= 7 ? 'success' : sleepHours >= 5 ? 'warning' : 'error'}
                    size="small"
                  />
                </Box>

                <Slider
                  value={sleepHours}
                  min={0}
                  max={12}
                  step={0.5}
                  onChange={(_, val) => setSleepHours(val)}
                  color="primary"
                  sx={{ mb: 2 }}
                />

                <Button
                  fullWidth
                  variant="contained"
                  color="primary"
                  onClick={() => sleepMutation.mutate()}
                  disabled={sleepMutation.isLoading}
                  startIcon={sleepMutation.isLoading ? <CircularProgress size={18} color="inherit" /> : <CheckIcon />}
                >
                  {sleepMutation.isLoading ? 'Saving...' : 'Log Sleep'}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Activity Tracker */}
        <Grid item xs={12} md={6}>
          <motion.div whileHover={{ scale: 1.01 }}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                  <WalkIcon color="warning" sx={{ fontSize: 32 }} />
                  <Typography variant="h6" fontWeight="bold">Activity & Steps</Typography>
                </Box>

                <TextField
                  fullWidth
                  label="Steps today"
                  type="number"
                  value={steps}
                  onChange={(e) => setSteps(e.target.value)}
                  placeholder="e.g. 3500"
                  sx={{ mb: 2 }}
                  inputProps={{ min: 0, max: 100000 }}
                />

                <Button
                  fullWidth
                  variant="contained"
                  color="warning"
                  onClick={() => activityMutation.mutate()}
                  disabled={activityMutation.isLoading || !steps}
                  startIcon={activityMutation.isLoading ? <CircularProgress size={18} color="inherit" /> : <CheckIcon />}
                >
                  {activityMutation.isLoading ? 'Saving...' : 'Log Activity'}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Water Tracker */}
        <Grid item xs={12} md={6}>
          <motion.div whileHover={{ scale: 1.01 }}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                  <WaterIcon color="info" sx={{ fontSize: 32 }} />
                  <Typography variant="h6" fontWeight="bold">Water Intake</Typography>
                </Box>

                <Box sx={{ textAlign: 'center', mb: 2 }}>
                  <Typography variant="h2" color="info.main">{waterGlasses}</Typography>
                  <Typography variant="body2" color="text.secondary">glasses of water today</Typography>
                </Box>

                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', mb: 2 }}>
                  <Button variant="outlined" onClick={() => setWaterGlasses(Math.max(0, waterGlasses - 1))}>-</Button>
                  {[1, 2, 4, 6, 8].map(n => (
                    <Button key={n} size="small" variant="outlined" color="info" onClick={() => setWaterGlasses(n)}>
                      {n}
                    </Button>
                  ))}
                  <Button variant="outlined" onClick={() => setWaterGlasses(waterGlasses + 1)}>+</Button>
                </Box>

                <Button
                  fullWidth
                  variant="contained"
                  color="info"
                  onClick={() => waterMutation.mutate(waterGlasses)}
                  disabled={waterMutation.isLoading || waterGlasses === 0}
                  startIcon={waterMutation.isLoading ? <CircularProgress size={18} color="inherit" /> : <CheckIcon />}
                >
                  {waterMutation.isLoading ? 'Saving...' : 'Log Water Intake'}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Recent logs */}
        {savedItems.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>✅ Today's Logs</Typography>
              <List dense>
                {savedItems.map((item, i) => (
                  <ListItem key={i}>
                    <ListItemText
                      primary={item.message}
                      primaryTypographyProps={{ component: 'div' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}

        {/* Weekly report */}
        {report && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
              <Typography variant="h6" gutterBottom fontWeight="bold">📊 7-Day Wellness Summary</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {report.statistics?.mood?.average?.toFixed(1) || '—'}
                    </Typography>
                    <Typography variant="caption">Avg Mood</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {report.statistics?.sleep?.average_hours?.toFixed(1) || '—'}h
                    </Typography>
                    <Typography variant="caption">Avg Sleep</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main">
                      {report.statistics?.activity?.total_steps?.toLocaleString() || '—'}
                    </Typography>
                    <Typography variant="caption">Total Steps</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="info.main">
                      {report.statistics?.water?.average_daily?.toFixed(1) || '—'}
                    </Typography>
                    <Typography variant="caption">Avg Water/Day</Typography>
                  </Box>
                </Grid>
              </Grid>

              {report.insights && report.insights.length > 0 && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" gutterBottom>AI Insights:</Typography>
                  {report.insights.map((insight, i) => (
                    <Chip key={i} label={insight} size="small" sx={{ mr: 0.5, mb: 0.5 }} color="success" variant="outlined" />
                  ))}
                </>
              )}
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default Wellness;