import React from 'react';
import { Box, Typography, Paper, LinearProgress, Grid } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import SecurityIcon from '@mui/icons-material/Security';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';

const SystemStatus = ({ status }) => {
  const components = [
    {
      id: 'nids',
      name: 'Network IDS',
      description: 'Monitors network traffic for suspicious activities',
      icon: <NetworkCheckIcon fontSize="large" />,
    },
    {
      id: 'hids',
      name: 'Host IDS',
      description: 'Monitors system files and processes for changes',
      icon: <SecurityIcon fontSize="large" />,
    },
  ];

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h6" gutterBottom>System Components</Typography>
      <Grid container spacing={3}>
        {components.map((component) => (
          <Grid item xs={12} sm={6} key={component.id}>
            <Paper 
              sx={{ 
                p: 2, 
                height: '100%',
                borderLeft: 4,
                borderColor: status[component.id]?.status === 'online' ? 'success.main' : 'warning.main',
                opacity: status[component.id]?.status === 'online' ? 1 : 0.7,
                transition: 'all 0.3s ease-in-out',
              }}
            >
              <Box display="flex" alignItems="center" mb={1}>
                <Box mr={2} color={status[component.id]?.status === 'online' ? 'success.main' : 'warning.main'}>
                  {component.icon}
                </Box>
                <Box flexGrow={1}>
                  <Typography variant="h6">
                    {component.name}
                    {status[component.id]?.status === 'online' ? (
                      <CheckCircleIcon 
                        fontSize="small" 
                        color="success" 
                        sx={{ ml: 1, verticalAlign: 'middle' }} 
                      />
                    ) : (
                      <WarningIcon 
                        fontSize="small" 
                        color="warning" 
                        sx={{ ml: 1, verticalAlign: 'middle' }} 
                      />
                    )}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {component.description}
                  </Typography>
                </Box>
              </Box>
              
              {status[component.id]?.status === 'starting' && (
                <Box mt={1}>
                  <Typography variant="caption" display="block" gutterBottom>
                    {status[component.id]?.message || 'Initializing...'}
                  </Typography>
                  <LinearProgress />
                </Box>
              )}
              
              {status[component.id]?.status === 'error' && (
                <Box mt={1}>
                  <Typography variant="caption" color="error" display="block">
                    {status[component.id]?.message || 'Initialization failed'}
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default SystemStatus;
