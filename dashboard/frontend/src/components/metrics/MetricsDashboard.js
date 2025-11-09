import React, { useMemo } from 'react';
import { 
  Box, 
  Grid,
  Paper,
  Typography, 
  Card, 
  CardContent,
  useTheme,
  useMediaQuery
} from '@mui/material';
import { 
  Timeline, 
  TimelineItem, 
  TimelineSeparator, 
  TimelineConnector, 
  TimelineContent, 
  TimelineDot,
  TimelineOppositeContent
} from '@mui/lab';
import { 
  Security as SecurityIcon,
  Warning as WarningIcon,
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  NetworkCheck as NetworkIcon,
  SsidChart as SsidChartIcon
} from '@mui/icons-material';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import AttackMap from './AttackMap';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const SeverityPieChart = ({ data = [] }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const severityData = useMemo(() => {
    const severityCount = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };
    
    if (Array.isArray(data)) {
      data.forEach(alert => {
        if (alert && alert.severity && severityCount[alert.severity] !== undefined) {
          severityCount[alert.severity]++;
        }
      });
    }
    
    return Object.entries(severityCount).map(([name, value]) => ({
      name,
      value,
      color: {
        critical: '#d32f2f',
        high: '#f57c00',
        medium: '#fbc02d',
        low: '#388e3c'
      }[name]
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={isMobile ? 200 : 250}>
      <PieChart>
        <Pie
          data={severityData}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={isMobile ? 60 : 80}
          fill="#8884d8"
          dataKey="value"
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
        >
          {severityData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip 
          formatter={(value, name) => [value, name]} 
          contentStyle={{
            backgroundColor: '#1e1e1e',
            border: '1px solid #333',
            borderRadius: '4px',
            color: '#fff'
          }}
        />
        <Legend 
          layout={isMobile ? 'horizontal' : 'vertical'}
          verticalAlign={isMobile ? 'bottom' : 'middle'}
          align={isMobile ? 'center' : 'right'}
          wrapperStyle={{
            paddingTop: isMobile ? '10px' : 0,
            paddingLeft: isMobile ? 0 : '10px',
            fontSize: '12px'
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

const AlertTimeline = ({ alerts }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const recentAlerts = useMemo(() => {
    return [...alerts]
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, 5);
  }, [alerts]);

  const getTimelineIcon = (type) => {
    switch (type) {
      case 'S-IDS':
        return <SecurityIcon color="primary" />;
      case 'A-IDS':
        return <WarningIcon color="warning" />;
      case 'H-IDS':
        return <StorageIcon color="secondary" />;
      default:
        return <TimelineIcon color="action" />;
    }
  };

  return (
    <Box sx={{ maxHeight: isMobile ? '300px' : '400px', overflow: 'auto', pr: 1 }}>
      <Timeline position="alternate">
        {recentAlerts.map((alert, index) => (
          <TimelineItem key={index}>
            <TimelineOppositeContent
              sx={{ m: 'auto 0' }}
              align="right"
              variant="body2"
              color="text.secondary"
            >
              {new Date(alert.timestamp).toLocaleTimeString()}
            </TimelineOppositeContent>
            <TimelineSeparator>
              <TimelineDot color={
                alert.severity === 'critical' ? 'error' :
                alert.severity === 'high' ? 'warning' :
                alert.severity === 'medium' ? 'info' : 'success'
              }>
                {getTimelineIcon(alert.source || '')}
              </TimelineDot>
              {index < recentAlerts.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent sx={{ py: '12px', px: 2 }}>
              <Typography variant="subtitle2" component="span">
                {alert.type || 'Security Alert'}
              </Typography>
              <Typography variant="caption" display="block" color="text.secondary">
                {alert.source && `${alert.source} → ${alert.destination || 'N/A'}`}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {alert.description || 'No description available'}
              </Typography>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    </Box>
  );
};

const AlertTrendsChart = ({ alerts }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const trendData = useMemo(() => {
    const now = new Date();
    const lastHour = new Date(now.getTime() - 60 * 60 * 1000);
    
    // Group alerts by 5-minute intervals
    const interval = 5 * 60 * 1000; // 5 minutes in ms
    const intervals = [];
    let currentTime = lastHour.getTime();
    
    while (currentTime <= now.getTime()) {
      intervals.push({
        time: new Date(currentTime),
        count: 0,
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
      });
      currentTime += interval;
    }
    
    // Count alerts in each interval
    alerts.forEach(alert => {
      const alertTime = new Date(alert.timestamp).getTime();
      if (alertTime >= lastHour.getTime()) {
        const intervalIndex = Math.floor((alertTime - lastHour.getTime()) / interval);
        if (intervalIndex >= 0 && intervalIndex < intervals.length) {
          intervals[intervalIndex].count++;
          if (['critical', 'high', 'medium', 'low'].includes(alert.severity)) {
            intervals[intervalIndex][alert.severity]++;
          }
        }
      }
    });
    
    return intervals.map(interval => ({
      time: interval.time,
      Alerts: interval.count,
      Critical: interval.critical,
      High: interval.high,
      Medium: interval.medium,
      Low: interval.low
    }));
  }, [alerts]);

  return (
    <ResponsiveContainer width="100%" height={isMobile ? 250 : 300}>
      <LineChart
        data={trendData}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#444" />
        <XAxis 
          dataKey="time" 
          tickFormatter={(time) => new Date(time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          stroke="#888"
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          stroke="#888"
          tick={{ fontSize: 12 }}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: '#1e1e1e',
            border: '1px solid #333',
            borderRadius: '4px',
            color: '#fff'
          }}
          labelFormatter={(label) => `Time: ${new Date(label).toLocaleTimeString()}`}
        />
        <Legend 
          wrapperStyle={{
            paddingTop: '10px',
            fontSize: '12px'
          }}
        />
        <Line 
          type="monotone" 
          dataKey="Alerts" 
          stroke="#8884d8" 
          activeDot={{ r: 8 }} 
          strokeWidth={2}
        />
        <Line 
          type="monotone" 
          dataKey="Critical" 
          stroke="#d32f2f" 
          strokeWidth={2}
        />
        <Line 
          type="monotone" 
          dataKey="High" 
          stroke="#f57c00" 
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

const AlertTypeChart = ({ alerts }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const typeData = useMemo(() => {
    const types = {};
    
    alerts.forEach(alert => {
      const type = alert.type || 'Unknown';
      types[type] = (types[type] || 0) + 1;
    });
    
    return Object.entries(types).map(([name, value]) => ({
      name: name.length > 15 ? `${name.substring(0, 15)}...` : name,
      value,
      fullName: name
    }));
  }, [alerts]);

  return (
    <ResponsiveContainer width="100%" height={isMobile ? 200 : 250}>
      <BarChart
        data={typeData}
        layout="vertical"
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#444" />
        <XAxis 
          type="number" 
          stroke="#888"
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          dataKey="name" 
          type="category" 
          width={100}
          stroke="#888"
          tick={{ fontSize: 12 }}
        />
        <Tooltip 
          formatter={(value, name, props) => [value, props.payload.fullName || name]}
          contentStyle={{
            backgroundColor: '#1e1e1e',
            border: '1px solid #333',
            borderRadius: '4px',
            color: '#fff'
          }}
        />
        <Bar 
          dataKey="value" 
          fill="#8884d8" 
          radius={[0, 4, 4, 0]}
          animationDuration={1500}
        >
          {typeData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

const MetricsDashboard = ({ alerts = [] }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Calculate summary statistics
  const stats = useMemo(() => {
    const now = new Date();
    const lastHour = new Date(now.getTime() - 60 * 60 * 1000);
    
    const lastHourAlerts = alerts.filter(
      alert => new Date(alert.timestamp) >= lastHour
    );
    
    const severityCount = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };
    
    alerts.forEach(alert => {
      if (severityCount[alert.severity] !== undefined) {
        severityCount[alert.severity]++;
      }
    });
    
    return {
      totalAlerts: alerts.length,
      alertsLastHour: lastHourAlerts.length,
      avgPerMinute: lastHourAlerts.length > 0 
        ? (lastHourAlerts.length / 60).toFixed(1) 
        : 0,
      criticalAlerts: severityCount.critical,
      highAlerts: severityCount.high,
      mediumAlerts: severityCount.medium,
      lowAlerts: severityCount.low
    };
  }, [alerts]);

  const StatCard = ({ title, value, icon: Icon, color = 'primary' }) => (
    <Card 
      variant="outlined" 
      sx={{ 
        height: '100%',
        borderLeft: `4px solid ${theme.palette[color].main}`,
        backgroundColor: 'background.paper',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: theme.shadows[4]
        }
      }}
    >
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h5" component="div">
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
          </Box>
          <Box
            sx={{
              backgroundColor: theme.palette[color].light,
              borderRadius: '50%',
              width: 40,
              height: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: theme.palette[color].contrastText
            }}
          >
            <Icon />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ flexGrow: 1, p: isMobile ? 1 : 2, overflow: 'auto' }}>
      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Total Alerts" 
            value={stats.totalAlerts.toLocaleString()} 
            icon={TimelineIcon}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Alerts (Last Hour)" 
            value={stats.alertsLastHour} 
            icon={SsidChartIcon}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Critical Alerts" 
            value={stats.criticalAlerts} 
            icon={WarningIcon}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard 
            title="Avg/Min (Last Hour)" 
            value={stats.avgPerMinute} 
            icon={NetworkIcon}
            color="success"
          />
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Left Column */}
        <Grid item xs={12} lg={8}>
          <Grid container spacing={3} direction="column">
            {/* Attack Map */}
            <Grid item xs={12}>
              <Paper 
                elevation={3} 
                sx={{ 
                  p: 2, 
                  height: '400px',
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <Box display="flex" alignItems="center" mb={2}>
                  <NetworkIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6" component="h2">Network Attack Map</Typography>
                </Box>
                <Box flexGrow={1} minHeight={0}>
                  <AttackMap alerts={alerts} />
                </Box>
              </Paper>
            </Grid>
            
            {/* Alert Trends */}
            <Grid item xs={12}>
              <Paper elevation={3} sx={{ p: 2 }}>
                <Box display="flex" alignItems="center" mb={2}>
                  <TimelineIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6" component="h2">Alert Trends (Last Hour)</Typography>
                </Box>
                <AlertTrendsChart alerts={alerts} />
              </Paper>
            </Grid>
          </Grid>
        </Grid>

        {/* Right Column */}
        <Grid item xs={12} lg={4}>
          <Grid container spacing={3} direction="column">
            {/* Severity Distribution */}
            <Grid item xs={12}>
              <Paper elevation={3} sx={{ p: 2, height: '100%' }}>
                <Box display="flex" alignItems="center" mb={2}>
                  <WarningIcon color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6" component="h2">Severity Distribution</Typography>
                </Box>
                <SeverityPieChart alerts={alerts} />
              </Paper>
            </Grid>
            
            {/* Alert Types */}
            <Grid item xs={12}>
              <Paper elevation={3} sx={{ p: 2, height: '100%' }}>
                <Box display="flex" alignItems="center" mb={2}>
                  <StorageIcon color="secondary" sx={{ mr: 1 }} />
                  <Typography variant="h6" component="h2">Alert Types</Typography>
                </Box>
                <AlertTypeChart alerts={alerts} />
              </Paper>
            </Grid>
            
            {/* Recent Activity */}
            <Grid item xs={12}>
              <Paper elevation={3} sx={{ p: 2 }}>
                <Box display="flex" alignItems="center" mb={2}>
                  <TimelineIcon color="action" sx={{ mr: 1 }} />
                  <Typography variant="h6" component="h2">Recent Activity</Typography>
                </Box>
                <AlertTimeline alerts={alerts} />
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MetricsDashboard;
