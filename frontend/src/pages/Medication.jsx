import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  Alert,
  AlertTitle,
  LinearProgress,
  Divider,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  LocalPharmacy as PharmacyIcon,
  CheckCircle as TakenIcon,
  Schedule as ScheduleIcon,
  Warning as MissedIcon,
  Add as AddIcon,
  Notifications as ReminderIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from 'react-query';
import { motion } from 'framer-motion';
import { useAuthStore } from '../stores/authStore';
import api from '../services/api';

const Medication = () => {
  const { user } = useAuthStore();
  const [openDialog, setOpenDialog] = useState(false);
  const [newMed, setNewMed] = useState({ name: '', dosage: '', schedule: '' });
  const [savedLogs, setSavedLogs] = useState([]);

  // Fetch medications list
  const { data: medData, isLoading, refetch } = useQuery(
    'medications',
    async () => {
      const response = await api.get(`/medication/list/${user?.id || 'dev_user'}`);
      return response.data;
    },
    { retry: 1 }
  );

  // Fetch adherence stats
  const { data: adherenceData } = useQuery(
    'adherence',
    async () => {
      const response = await api.get(`/medication/adherence/${user?.id || 'dev_user'}?days=7`);
      return response.data;
    },
    { retry: 1 }
  );

  // Record taken/missed
  const recordMutation = useMutation(
    async ({ medId, medName, status }) => {
      const response = await api.post('/medication/adherence/record', {
        user_id: user?.id || 'dev_user',
        medication_id: medId,
        medication_name: medName,
        status,
        scheduled_time: new Date().toISOString(),
        taken_time: status === 'taken' ? new Date().toISOString() : null,
      });
      return response.data;
    },
    {
      onSuccess: (data, vars) => {
        setSavedLogs(prev => [
          { name: vars.medName, status: vars.status, time: new Date().toLocaleTimeString() },
          ...prev,
        ]);
      },
    }
  );

  // Send reminder
  const reminderMutation = useMutation(
    async () => {
      const response = await api.post('/medication/remind', {
        user_id: user?.id || 'dev_user',
      });
      return response.data;
    }
  );

  // Mock medications for display when none in DB yet
  const displayMeds = medData?.medications?.length > 0
    ? medData.medications
    : [
        { id: 'mock1', name: 'Lisinopril', dosage: '10mg', schedule: ['8:00 AM'], active: true },
        { id: 'mock2', name: 'Metformin', dosage: '500mg', schedule: ['8:00 AM', '6:00 PM'], active: true },
        { id: 'mock3', name: 'Atorvastatin', dosage: '20mg', schedule: ['9:00 PM'], active: true },
      ];

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
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
          background: 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)',
          color: 'white',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <PharmacyIcon sx={{ fontSize: 48 }} />
            <Box>
              <Typography variant="h4" fontWeight="bold">Medication Manager</Typography>
              <Typography variant="body1" sx={{ opacity: 0.9 }}>
                Powered by Medication Agent + Azure Communication Services
              </Typography>
            </Box>
          </Box>
          <Button
            variant="contained"
            color="success"
            startIcon={<ReminderIcon />}
            onClick={() => reminderMutation.mutate()}
            disabled={reminderMutation.isLoading}
            sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}
          >
            Send Reminder
          </Button>
        </Box>
      </Paper>

      {reminderMutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Medication reminder sent via Azure Communication Services!
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Adherence Card */}
        <Grid item xs={12} md={4}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight="bold">
                📊 7-Day Adherence
              </Typography>
              <Box sx={{ textAlign: 'center', my: 2 }}>
                <Typography variant="h2" color="success.main">
                  {adherenceData?.adherence_rate || 85.5}%
                </Typography>
                <Chip
                  label={adherenceData?.trend || 'improving'}
                  color="success"
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Box>
              <LinearProgress
                variant="determinate"
                value={adherenceData?.adherence_rate || 85.5}
                color="success"
                sx={{ height: 10, borderRadius: 5, mb: 1 }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption">
                  Taken: {adherenceData?.taken || 12}
                </Typography>
                <Typography variant="caption" color="error">
                  Missed: {adherenceData?.missed || 2}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Today's Medications */}
        <Grid item xs={12} md={8}>
          <Card elevation={3}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold">
                  💊 Today's Medications
                </Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  variant="outlined"
                  onClick={() => setOpenDialog(true)}
                >
                  Add Medication
                </Button>
              </Box>

              <List>
                {displayMeds.map((med, index) => (
                  <React.Fragment key={med.id}>
                    <motion.div whileHover={{ scale: 1.01 }}>
                      <ListItem sx={{ px: 0 }}>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'success.main' }}>
                            <PharmacyIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primaryTypographyProps={{ component: 'div' }}
                          secondaryTypographyProps={{ component: 'div' }}
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle1" fontWeight="bold">
                                {med.name}
                              </Typography>
                              <Chip label={med.dosage} size="small" variant="outlined" />
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 0.5 }}>
                              <Typography variant="caption" color="text.secondary">
                                Schedule: {Array.isArray(med.schedule) ? med.schedule.join(', ') : med.schedule}
                              </Typography>
                            </Box>
                          }
                        />
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            size="small"
                            variant="contained"
                            color="success"
                            startIcon={<TakenIcon />}
                            onClick={() => recordMutation.mutate({ medId: med.id, medName: med.name, status: 'taken' })}
                            disabled={recordMutation.isLoading}
                          >
                            Taken
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            startIcon={<MissedIcon />}
                            onClick={() => recordMutation.mutate({ medId: med.id, medName: med.name, status: 'missed' })}
                            disabled={recordMutation.isLoading}
                          >
                            Skip
                          </Button>
                        </Box>
                      </ListItem>
                    </motion.div>
                    {index < displayMeds.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent logs */}
        {savedLogs.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>✅ Today's Log</Typography>
              <List dense>
                {savedLogs.map((log, i) => (
                  <ListItem key={i}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: log.status === 'taken' ? 'success.main' : 'error.main', width: 32, height: 32 }}>
                        {log.status === 'taken' ? <TakenIcon fontSize="small" /> : <MissedIcon fontSize="small" />}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={`${log.name} — ${log.status}`}
                      secondary={log.time}
                      primaryTypographyProps={{ component: 'div' }}
                      secondaryTypographyProps={{ component: 'div' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        )}
      </Grid>

      {/* Add Medication Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Medication</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Medication Name"
            value={newMed.name}
            onChange={(e) => setNewMed({ ...newMed, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Dosage (e.g. 10mg)"
            value={newMed.dosage}
            onChange={(e) => setNewMed({ ...newMed, dosage: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Schedule (e.g. 8:00 AM, 8:00 PM)"
            value={newMed.schedule}
            onChange={(e) => setNewMed({ ...newMed, schedule: e.target.value })}
            margin="normal"
            helperText="Comma-separated times"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="success"
            onClick={() => {
              // In production would call API — for demo just close
              setOpenDialog(false);
              setNewMed({ name: '', dosage: '', schedule: '' });
            }}
          >
            Add Medication
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Medication;