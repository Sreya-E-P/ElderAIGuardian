import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const HeroShowcase = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4">Hero Technologies Showcase</Typography>
        <Typography variant="body1">Coming soon...</Typography>
      </Paper>
    </Box>
  );
};

export default HeroShowcase;