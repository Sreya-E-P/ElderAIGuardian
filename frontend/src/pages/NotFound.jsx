import React from 'react';
import { Box, Paper, Typography, Button, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { Error as ErrorIcon } from '@mui/icons-material';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 8, textAlign: 'center' }}>
        <ErrorIcon sx={{ fontSize: 100, color: 'error.main', mb: 2 }} />
        <Typography variant="h1" gutterBottom>404</Typography>
        <Typography variant="h4" gutterBottom>Page Not Found</Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          The page you're looking for doesn't exist or has been moved.
        </Typography>
        <Button 
          variant="contained" 
          size="large" 
          onClick={() => navigate('/')}
          sx={{ mt: 2 }}
        >
          Go to Dashboard
        </Button>
      </Box>
    </Container>
  );
};

export default NotFound;
