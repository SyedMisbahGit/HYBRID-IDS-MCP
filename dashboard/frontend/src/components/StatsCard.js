import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { styled } from '@mui/material/styles';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

const StyledCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.2s, box-shadow 0.2s',
  '&:hover': {
    transform: 'translateY(-4px)',
    boxShadow: theme.shadows[8],
  },
}));

const StatIcon = styled(Box)(({ theme, color = 'primary.main' }) => ({
  display: 'inline-flex',
  padding: theme.spacing(1.5),
  borderRadius: '12px',
  backgroundColor: theme.palette.mode === 'dark' 
    ? `${theme.palette[color.split('.')[0]]?.dark}33` 
    : `${theme.palette[color.split('.')[0]]?.light}80`,
  color: theme.palette[color.split('.')[0]]?.main || color,
  marginBottom: theme.spacing(2),
}));

const StatsCard = ({ title, value, color = 'primary.main', icon, trend = 0 }) => {
  const TrendIcon = trend >= 0 ? TrendingUpIcon : TrendingDownIcon;
  const trendColor = trend >= 0 ? 'success.main' : 'error.main';
  
  return (
    <StyledCard elevation={3}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography color="textSecondary" variant="subtitle2" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
              {value}
            </Typography>
          </Box>
          <StatIcon color={color}>
            <Box component="span" className="material-icons">
              {icon}
            </Box>
          </StatIcon>
        </Box>
        
        <Box mt={1} display="flex" alignItems="center">
          <TrendIcon 
            fontSize="small" 
            sx={{ 
              color: trendColor,
              mr: 0.5,
              transform: trend < 0 ? 'rotate(0deg)' : 'rotate(0deg)'
            }} 
          />
          <Typography 
            variant="caption" 
            sx={{ 
              color: trendColor,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {Math.abs(trend)}% from last hour
          </Typography>
        </Box>
      </CardContent>
    </StyledCard>
  );
};

export default StatsCard;
