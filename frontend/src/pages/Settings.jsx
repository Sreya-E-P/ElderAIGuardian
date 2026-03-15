import React from 'react';
import { Box, Paper, Typography, Grid, Card, CardContent, Switch, FormControlLabel } from '@mui/material';
import { Settings as SettingsIcon } from '@mui/icons-material';

const Settings = () => {
  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'grey.700', color: 'white' }}>
        <Typography variant="h4">Settings</Typography>
        <Typography variant="body1">Configure your preferences</Typography>
      </Paper>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>Notifications</Typography>
              <FormControlLabel control={<Switch defaultChecked />} label="Push Notifications" />
              <FormControlLabel control={<Switch defaultChecked />} label="Email Alerts" />
              <FormControlLabel control={<Switch />} label="SMS Notifications" />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings;
