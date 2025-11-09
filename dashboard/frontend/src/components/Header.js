import React from 'react';
import { AppBar, Toolbar, Typography, Box, IconButton, Badge } from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import SecurityIcon from '@mui/icons-material/Security';
import { styled } from '@mui/material/styles';

const StyledBadge = styled(Badge)(({ theme }) => ({
  '& .MuiBadge-badge': {
    right: -3,
    top: 13,
    border: `2px solid ${theme.palette.background.paper}`,
    padding: '0 4px',
  },
}));

const Header = () => {
  // In a real app, this would come from your state/context
  const alertCount = 5; // Example count
  
  return (
    <AppBar position="static" color="default" elevation={0}>
      <Toolbar>
        <SecurityIcon sx={{ mr: 2, color: 'primary.main' }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
          Hybrid IDS Dashboard
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton color="inherit" size="large">
            <StyledBadge badgeContent={alertCount} color="error">
              <NotificationsIcon />
            </StyledBadge>
          </IconButton>
          
          <Box sx={{ ml: 2, textAlign: 'right' }}>
            <Typography variant="subtitle2" sx={{ lineHeight: 1 }}>
              System Status
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ 
                width: 10, 
                height: 10, 
                borderRadius: '50%', 
                bgcolor: 'success.main',
                mr: 1
              }} />
              <Typography variant="caption" color="textSecondary">
                Operational
              </Typography>
            </Box>
          </Box>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
