import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { 
  Box, 
  Button, 
  Chip,
  Typography, 
  Paper, 
  Tabs, 
  Tab, 
  IconButton, 
  Tooltip, 
  useTheme, 
  useMediaQuery,
  CircularProgress,
  Snackbar,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tooltip,
  IconButton,
  Paper,
  Tabs,
  Tab,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { 
  PlayArrow as PlayArrowIcon, 
  Stop as StopIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Dashboard as DashboardIcon,
  TableView as TableViewIcon,
  AutoFixHigh as AutoFixHighIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  Storage as StorageIcon,
  Public as PublicIcon,
  Traffic as TrafficIcon
} from '@mui/icons-material';
import AlertsTable from './AlertsTable';
import MetricsDashboard from './metrics/MetricsDashboard';
import { v4 as uuidv4 } from 'uuid';

// Enhanced data generators with realistic attack patterns
const generateSidsAlerts = () => {
  const severities = ['low', 'medium', 'high', 'critical'];
  const types = [
    'Port Scan', 'DDoS', 'SQL Injection', 'XSS', 'Brute Force',
    'Credential Stuffing', 'DNS Tunneling', 'Man-in-the-Middle',
    'Phishing Attempt', 'Malware Download', 'Exploit Kit', 'Zero-Day Exploit'
  ];
  
  const sources = [
    '192.168.1.10', '10.0.0.5', '172.16.0.1', '104.18.1.1',
    '45.33.2.79', '185.199.108.153', '140.82.121.4', '172.217.14.206'
  ];
  
  const destinations = [
    '192.168.1.100', '10.0.0.10', '172.16.0.100',
    '192.168.1.200', '10.0.0.20', '172.16.0.200'
  ];
  
  const ports = [22, 80, 443, 3306, 5432, 8080, 8443];
  const protocols = ['TCP', 'UDP', 'ICMP'];
  const attackType = types[Math.floor(Math.random() * types.length)];
  const severityWeights = {
    'Port Scan': [0.4, 0.4, 0.15, 0.05],
    'DDoS': [0.1, 0.2, 0.5, 0.2],
    'SQL Injection': [0.1, 0.2, 0.4, 0.3],
    'XSS': [0.2, 0.3, 0.3, 0.2],
    'Brute Force': [0.3, 0.4, 0.2, 0.1],
    'default': [0.3, 0.4, 0.2, 0.1]
  };
  
  const weights = attackType in severityWeights ? severityWeights[attackType] : severityWeights.default;
  const severity = weightedRandom(severities, weights);
  
  const alert = {
    id: uuidv4(),
    timestamp: new Date().toISOString(),
    type: attackType,
    severity: severity,
    source: sources[Math.floor(Math.random() * sources.length)],
    destination: destinations[Math.floor(Math.random() * destinations.length)],
    source_port: Math.floor(Math.random() * 65535),
    dest_port: ports[Math.floor(Math.random() * ports.length)],
    protocol: protocols[Math.floor(Math.random() * protocols.length)],
    bytes: Math.floor(Math.random() * 10000) + 100,
    packets: Math.floor(Math.random() * 100) + 1,
    source_type: Math.random() > 0.7 ? 'external' : 'internal',
    confidence: (0.7 + Math.random() * 0.3).toFixed(2),
    description: ''
  };
  
  // Generate realistic descriptions based on alert type
  switch(attackType) {
    case 'Port Scan':
      alert.description = `Port scan detected from ${alert.source} targeting port ${alert.dest_port}`;
      break;
    case 'DDoS':
      alert.description = `Possible DDoS attack from ${alert.source} with ${alert.packets} packets`;
      break;
    case 'SQL Injection':
      alert.description = `SQL injection attempt detected in web request from ${alert.source}`;
      break;
    case 'XSS':
      alert.description = `Cross-site scripting (XSS) attempt detected from ${alert.source}`;
      break;
    case 'Brute Force':
      alert.description = `Brute force attempt on ${alert.destination}:${alert.dest_port} from ${alert.source}`;
      break;
    default:
      alert.description = `Suspicious ${attackType.toLowerCase()} activity detected from ${alert.source}`;
  }
  
  return alert;
};

const generateAidsAlerts = () => {
  const severities = ['low', 'medium', 'high', 'critical'];
  const behaviors = [
    'Data Exfiltration', 'Lateral Movement', 'Privilege Escalation', 
    'Command Injection', 'Suspicious Process', 'Abnormal API Calls',
    'Registry Tampering', 'Scheduled Task Creation', 'Service Manipulation'
  ];
  
  const processes = [
    'powershell.exe', 'cmd.exe', 'wscript.exe', 'msbuild.exe',
    'regsvr32.exe', 'rundll32.exe', 'certutil.exe', 'bitsadmin.exe'
  ];
  
  const users = ['admin', 'system', 'svc_web', 'sqlservice', 'backup'];
  const hosts = ['WEB-01', 'DB-01', 'APP-01', 'FILESERVER-01'];
  const behavior = behaviors[Math.floor(Math.random() * behaviors.length)];
  
  // Weight severities based on behavior
  let severity;
  if (['Data Exfiltration', 'Privilege Escalation', 'Command Injection'].includes(behavior)) {
    severity = weightedRandom(severities, [0.1, 0.2, 0.4, 0.3]);
  } else if (['Lateral Movement', 'Service Manipulation'].includes(behavior)) {
    severity = weightedRandom(severities, [0.2, 0.3, 0.3, 0.2]);
  } else {
    severity = weightedRandom(severities, [0.3, 0.4, 0.2, 0.1]);
  }
  
  const alert = {
    id: uuidv4(),
    timestamp: new Date().toISOString(),
    type: 'Anomaly',
    behavior: behavior,
    severity: severity,
    process: processes[Math.floor(Math.random() * processes.length)],
    user: users[Math.floor(Math.random() * users.length)],
    host: hosts[Math.floor(Math.random() * hosts.length)],
    source: 'A-IDS',
    confidence: (0.6 + Math.random() * 0.4).toFixed(2),
    description: ''
  };
  
  // Generate descriptive messages
  switch(behavior) {
    case 'Data Exfiltration':
      alert.description = `Unusual data transfer (${Math.floor(Math.random() * 1000)}MB) by ${alert.process}`;
      break;
    case 'Lateral Movement':
      alert.description = `Suspicious network connection to ${hosts[Math.floor(Math.random() * hosts.length)]}`;
      break;
    case 'Privilege Escalation':
      alert.description = `Process ${alert.process} attempted to gain elevated privileges`;
      break;
    default:
      alert.description = `Suspicious behavior detected: ${behavior}`;
  }
  
  return alert;
};

const generateHidsAlerts = () => {
  const severities = ['low', 'medium', 'high', 'critical'];
  const events = [
    'File Modification', 'New Process', 'Suspicious Login', 'Registry Change',
    'Scheduled Task', 'Service Installation', 'Kernel Module', 'Rootkit Activity'
  ];
  
  const files = [
    '/etc/passwd', '/var/log/auth.log', '/etc/shadow', '/tmp/suspicious.sh',
    '/bin/bash', '/usr/bin/python', '/tmp/exploit', '/var/www/html/index.php'
  ];
  
  const users = ['root', 'admin', 'apache', 'mysql', 'nobody'];
  const event = events[Math.floor(Math.random() * events.length)];
  
  // Weight severities based on event type
  let severity;
  if (['Rootkit Activity', 'Suspicious Login', 'Kernel Module'].includes(event)) {
    severity = weightedRandom(severities, [0.05, 0.15, 0.4, 0.4]);
  } else if (['File Modification', 'Registry Change'].includes(event)) {
    severity = weightedRandom(severities, [0.2, 0.3, 0.3, 0.2]);
  } else {
    severity = weightedRandom(severities, [0.4, 0.3, 0.2, 0.1]);
  }
  
  const alert = {
    id: uuidv4(),
    timestamp: new Date().toISOString(),
    type: 'Host Event',
    event: event,
    severity: severity,
    file: files[Math.floor(Math.random() * files.length)],
    user: users[Math.floor(Math.random() * users.length)],
    hostname: `host-${Math.floor(Math.random() * 50) + 1}`,
    source: 'H-IDS',
    description: ''
  };
  
  // Generate descriptive messages
  switch(event) {
    case 'File Modification':
      alert.description = `Critical system file modified: ${alert.file}`;
      break;
    case 'Suspicious Login':
      alert.description = `Unusual login for user ${alert.user} from ${['192.168.1.' + (Math.floor(Math.random() * 50) + 1), '10.0.0.' + (Math.floor(Math.random() * 50) + 1)][Math.floor(Math.random() * 2)]}`;
      break;
    case 'Rootkit Activity':
      alert.description = 'Possible rootkit installation detected';
      break;
    default:
      alert.description = `Host event detected: ${event}`;
  }
  
  return alert;
};

// Helper function for weighted random selection
const weightedRandom = (items, weights) => {
  const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
  const random = Math.random() * totalWeight;
  let weightSum = 0;
  
  for (let i = 0; i < items.length; i++) {
    weightSum += weights[i];
    if (random <= weightSum) return items[i];
  }
  
  return items[items.length - 1];
};

const AlertsDashboard = ({ isConnected = false, onAlertGenerated }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [activeTab, setActiveTab] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [viewMode, setViewMode] = useState('dashboard'); // 'dashboard' or 'table'
  const [sidsAlerts, setSidsAlerts] = useState([]);
  const [aidsAlerts, setAidsAlerts] = useState([]);
  const [hidsAlerts, setHidsAlerts] = useState([]);
  const [notification, setNotification] = useState(null);
  const [generationSpeed, setGenerationSpeed] = useState(1000); // ms between alerts
  const [alertsCount, setAlertsCount] = useState({
    sids: 0,
    aids: 0,
    hids: 0,
    total: 0
  });
  
  // Track all alerts for metrics
  const [allAlerts, setAllAlerts] = useState([]);
  // Track recent traffic for the table
  const [trafficLog, setTrafficLog] = useState([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Refs for cleanup
  const generationInterval = useRef(null);
  const isMounted = useRef(true);

  // Function to handle alert generation and state updates
  const handleNewAlert = useCallback((alert, type) => {
    console.log(`[DEBUG] handleNewAlert called with type: ${type}`, alert);
    
    if (!alert) {
      console.warn('[WARN] handleNewAlert: No alert provided');
      return;
    }
    
    // Update the specific alert type state
    const setAlertsMap = {
      'sids': setSidsAlerts,
      'aids': setAidsAlerts,
      'hids': setHidsAlerts
    };
    
    if (!setAlertsMap[type]) {
      console.error(`[ERROR] handleNewAlert: Invalid alert type: ${type}`);
      return;
    }
    
    // Update the specific alert type and all alerts
    setAlertsMap[type](prev => {
      const updated = [alert, ...prev].slice(0, 1000); // Keep last 1000 alerts
      console.log(`[DEBUG] Updated ${type} alerts, count:`, updated.length);
      return updated;
    });
    
    // Update all alerts for metrics
    setAllAlerts(prev => {
      const updated = [alert, ...prev].slice(0, 5000);
      console.log('[DEBUG] Updated all alerts, count:', updated.length);
      return updated;
    });
    
    // Update traffic log
    const timestamp = new Date().toISOString();
    const trafficEntry = {
      timestamp,
      type: type.toUpperCase(),
      source: alert.source || 'Unknown',
      destination: alert.destination || 'N/A',
      severity: alert.severity || 'info',
      description: alert.description || alert.type || 'Network activity'
    };
    
    setTrafficLog(prev => {
      const updated = [trafficEntry, ...prev].slice(0, 1000);
      console.log('[DEBUG] Updated traffic log, count:', updated.length);
      return updated;
    });
    
    // Update counters
    setAlertsCount(prev => {
      const updated = {
        ...prev,
        [type]: prev[type] + 1,
        total: prev.total + 1
      };
      console.log('[DEBUG] Updated alerts count:', updated);
      return updated;
    });
    
    // Notify parent component if callback is provided
    if (onAlertGenerated) {
      console.log('[DEBUG] Notifying parent component of new alert');
      onAlertGenerated(alert);
    }
    
    // Show notification for medium+ severity alerts
    if (['medium', 'high', 'critical'].includes(alert.severity)) {
      const severityMap = {
        critical: 'error',
        high: 'warning',
        medium: 'info',
        low: 'info'
      };
      
      const title = `${type.toUpperCase()} ${alert.severity.toUpperCase()} Alert`;
      const message = `${alert.type || alert.behavior || alert.event}: ${alert.description}`;
      const severity = severityMap[alert.severity] || 'info';
      
      console.log(`[DEBUG] Showing notification:`, { title, message, severity });
      showNotification(title, message, severity);
    } else {
      console.log('[DEBUG] Alert severity too low for notification:', alert.severity);
    }
  }, [onAlertGenerated]);

  // Generate consistent traffic pattern
  const generateTrafficPattern = useCallback(() => {
    // Consistent traffic pattern with no time-based variations
    const speedMultiplier = 1;
    const burstChance = 0.3; // 30% chance of burst
    
    return { speedMultiplier, burstChance };
  }, []);

  // Generate alerts with consistent patterns
  const generateAlerts = useCallback(() => {
    console.log('[DEBUG] generateAlerts called, isMounted:', isMounted.current);
    if (!isMounted.current) {
      console.warn('[WARN] generateAlerts: Component not mounted, but still trying to generate alerts');
      // Don't return early here, let the alert generation continue
    }
    
    const { burstChance } = generateTrafficPattern();
    const alertType = Math.random();
    
    // Consistent alert type distribution
    const type = alertType < 0.6 ? 'sids' : (alertType < 0.9 ? 'aids' : 'hids');
    
    // Generate the alert
    const alert = type === 'sids' ? generateSidsAlerts() : 
                 (type === 'aids' ? generateAidsAlerts() : generateHidsAlerts());
    handleNewAlert(alert, type);
    
    // Simulate traffic bursts
    if (Math.random() < burstChance) {
      const burstCount = Math.floor(Math.random() * 3) + 1; // 1-3 alerts in a burst
      const burstType = Math.random() > 0.3 ? 'sids' : (Math.random() > 0.5 ? 'aids' : 'hids');
      
      for (let i = 0; i < burstCount; i++) {
        const delay = (i + 1) * (200 + Math.random() * 300); // Stagger the burst alerts
        setTimeout(() => {
          if (!isMounted.current) return;
          const burstAlert = burstType === 'sids' ? generateSidsAlerts() : 
                           (burstType === 'aids' ? generateAidsAlerts() : generateHidsAlerts());
          handleNewAlert(burstAlert, burstType);
        }, delay);
      }
    }
  }, [handleNewAlert, generateTrafficPattern]);

  // Start generating realistic traffic
  const startAlerts = useCallback(() => {
    console.log('[DEBUG] startAlerts called, isRunning:', isRunning, 'isMounted:', isMounted.current);
    if (isRunning) {
      console.log('[DEBUG] startAlerts: Already running, returning early');
      return;
    }
    
    console.log('[DEBUG] Setting isRunning to true');
    setIsRunning(true);
    
    // Initial batch of alerts
    const initialAlerts = Math.floor(Math.random() * 5) + 3; // 3-7 initial alerts
    console.log(`[DEBUG] Generating ${initialAlerts} initial alerts`);
    for (let i = 0; i < initialAlerts; i++) {
      const delay = i * 200;
      console.log(`[DEBUG] Scheduling alert ${i + 1} in ${delay}ms`);
      setTimeout(() => {
        console.log('[DEBUG] Executing scheduled alert', i + 1);
        generateAlerts();
      }, delay);
    }
    
    // Continuous alert generation with dynamic timing
    const scheduleNextAlert = () => {
      if (!isMounted.current) return;
      
      const { speedMultiplier } = generateTrafficPattern();
      const baseDelay = Math.max(200, generationSpeed * speedMultiplier);
      const delay = baseDelay * (0.8 + Math.random() * 0.4); // Add some randomness
      
      generationInterval.current = setTimeout(() => {
        generateAlerts();
        scheduleNextAlert();
      }, delay);
    };
    
    scheduleNextAlert();
    
    return () => {
      if (generationInterval.current) {
        clearTimeout(generationInterval.current);
        generationInterval.current = null;
      }
    };
  }, [isRunning, generationSpeed, generateAlerts, generateTrafficPattern]);

  const stopAlerts = useCallback(() => {
    console.log('stopAlerts called');
    if (generationInterval.current) {
      clearTimeout(generationInterval.current);
      generationInterval.current = null;
    }
    setIsRunning(false);
  }, []);

  const toggleGeneration = useCallback(() => {
    if (isRunning) {
      stopAlerts();
      setIsRunning(false);
    } else {
      startAlerts();
      setIsRunning(true);
    }
  }, [isRunning, startAlerts, stopAlerts]);

  const clearAlerts = useCallback(() => {
    setSidsAlerts([]);
    setAidsAlerts([]);
    setHidsAlerts([]);
    setAllAlerts([]);
    setTrafficLog([]);
    setAlertsCount({
      sids: 0,
      aids: 0,
      hids: 0,
      total: 0
    });
  }, []);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Format timestamp for display
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Get severity color
  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#d32f2f',
      high: '#f57c00',
      medium: '#fbc02d',
      low: '#388e3c',
      info: '#1976d2'
    };
    return colors[severity] || colors.info;
  };

  const changeGenerationSpeed = useCallback((speed) => {
    setGenerationSpeed(speed);
    if (isRunning) {
      stopAlerts();
      // Restart with new speed
      setTimeout(() => startAlerts(), 100);
    }
  }, [isRunning, startAlerts, stopAlerts]);

  const showNotification = useCallback((title, message, severity = 'info') => {
    setNotification({ title, message, severity });
  }, []);

  const generateAlert = useCallback(() => {
    if (!isMounted.current) return;
    
    const alertTypes = ['sids', 'aids', 'hids'];
    const weights = [0.5, 0.3, 0.2]; // Higher chance for network alerts
    const alertType = weightedRandom(alertTypes, weights);
    
    let newAlert;
    const now = new Date();
    
    // Generate timestamp with some random jitter (up to 5 seconds) to simulate real-world timing
    const timestamp = new Date(now.getTime() - Math.random() * 5000).toISOString();
    
    switch(alertType) {
      case 'sids':
        newAlert = generateSidsAlerts();
        newAlert.timestamp = timestamp;
        setSidsAlerts(prev => {
          const updated = [newAlert, ...prev].slice(0, 100);
          return updated;
        });
        break;
      case 'aids':
        newAlert = generateAidsAlerts();
        newAlert.timestamp = timestamp;
        setAidsAlerts(prev => {
          const updated = [newAlert, ...prev].slice(0, 100);
          return updated;
        });
        break;
      case 'hids':
        newAlert = generateHidsAlerts();
        newAlert.timestamp = timestamp;
        setHidsAlerts(prev => {
          const updated = [newAlert, ...prev].slice(0, 100);
          return updated;
        });
        break;
      default:
        return;
    }
    
    // Add to all alerts for metrics
    setAllAlerts(prev => {
      const updated = [newAlert, ...prev].slice(0, 5000); // Keep last 5000 alerts for metrics
      return updated;
    });
    
    // Update counters
    setAlertsCount(prev => {
      const updated = {
        ...prev,
        [alertType]: prev[alertType] + 1,
        total: prev.total + 1
      };
      return updated;
    });
    
    // Notify parent component if callback is provided
    if (onAlertGenerated) {
      onAlertGenerated(newAlert);
    }
    
    // Show notification for medium+ severity alerts
    if (['medium', 'high', 'critical'].includes(newAlert.severity)) {
      showNotification(
        `${alertType.toUpperCase()} ${newAlert.severity.toUpperCase()} Alert`,
        `${newAlert.type || newAlert.behavior || newAlert.event}: ${newAlert.description}`,
        newAlert.severity === 'critical' ? 'error' : 
        newAlert.severity === 'high' ? 'warning' : 'info'
      );
    }
  }, [onAlertGenerated, showNotification]);

  const handleCloseNotification = () => {
    setNotification(null);
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  // Toggle between dashboard and table view
  const toggleViewMode = () => {
    setViewMode(prev => prev === 'dashboard' ? 'table' : 'dashboard');
  };

  // Get current alerts based on active tab
  const currentAlerts = useMemo(() => {
    switch(activeTab) {
      case 0: return sidsAlerts;
      case 1: return aidsAlerts;
      case 2: return hidsAlerts;
      default: return [];
    }
  }, [activeTab, sidsAlerts, aidsAlerts, hidsAlerts]);

  // Start alerts when component mounts
  useEffect(() => {
    console.log('[DEBUG] Component mounted, isRunning:', isRunning);
    
    // Set mounted flag to true when component mounts
    isMounted.current = true;
    
    // Only start if not already running
    if (!isRunning) {
      console.log('[DEBUG] Starting alert generation');
      startAlerts();
    } else {
      console.log('[DEBUG] Alert generation already running');
    }
    
    // Cleanup on unmount
    return () => {
      console.log('[DEBUG] Component unmounting, cleaning up...');
      isMounted.current = false;
      stopAlerts();
    };
  }, []); // Empty dependency array means this runs once on mount

  return (
    <Box component="div" sx={{ width: '100%', p: { xs: 1, sm: 2 } }}>
      {/* Header with Tabs and Controls */}
      <Box 
        component="header"
        sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'stretch', sm: 'center' },
          gap: 2,
          mb: 3,
          borderBottom: 1, 
          borderColor: 'divider',
          pb: 2,
          position: 'sticky',
          top: 0,
          zIndex: 10,
          backgroundColor: theme.palette.background.default,
          backdropFilter: 'blur(8px)',
          pt: 1
        }}
      >
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          aria-label="alert types"
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            minHeight: 'auto',
            '& .MuiTab-root': {
              minHeight: 'auto',
              py: 1,
              px: { xs: 1, sm: 2 },
              fontSize: { xs: '0.75rem', sm: '0.875rem' }
            }
          }}
        >
          <Tab 
            label={
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1,
                flexDirection: isMobile ? 'column' : 'row',
                p: 0.5
              }}>
                <SecurityIcon fontSize={isMobile ? 'small' : 'medium'} />
                <span>S-IDS Alerts</span>
                {alertsCount.sids > 0 && (
                  <Box 
                    sx={{
                      backgroundColor: 'error.main',
                      color: 'white',
                      borderRadius: '10px',
                      minWidth: '20px',
                      height: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.7rem',
                      fontWeight: 'bold'
                    }}
                  >
                    {alertsCount.sids}
                  </Box>
                )}
              </Box>
            } 
          />
          <Tab 
            label={
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1,
                flexDirection: isMobile ? 'column' : 'row',
                p: 0.5
              }}>
                <WarningIcon fontSize={isMobile ? 'small' : 'medium'} />
                <span>A-IDS Alerts</span>
                {alertsCount.aids > 0 && (
                  <Box 
                    sx={{
                      backgroundColor: 'warning.main',
                      color: 'white',
                      borderRadius: '10px',
                      minWidth: '20px',
                      height: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.7rem',
                      fontWeight: 'bold'
                    }}
                  >
                    {alertsCount.aids}
                  </Box>
                )}
              </Box>
            } 
          />
          <Tab 
            label={
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 1,
                flexDirection: isMobile ? 'column' : 'row',
                p: 0.5
              }}>
                <StorageIcon fontSize={isMobile ? 'small' : 'medium'} />
                <span>H-IDS Alerts</span>
                {alertsCount.hids > 0 && (
                  <Box 
                    sx={{
                      backgroundColor: 'info.main',
                      color: 'white',
                      borderRadius: '10px',
                      minWidth: '20px',
                      height: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.7rem',
                      fontWeight: 'bold'
                    }}
                  >
                    {alertsCount.hids}
                  </Box>
                )}
              </Box>
            } 
          />
        </Tabs>
        
        <Box sx={{ 
          display: 'flex', 
          gap: 2,
          alignItems: 'center',
          justifyContent: { xs: 'space-between', sm: 'flex-end' },
          width: { xs: '100%', sm: 'auto' },
          mt: { xs: 1, sm: 0 },
          px: { xs: 1, sm: 0 }
        }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center',
            gap: 1,
            color: isConnected ? 'success.main' : 'error.main'
          }}>
            {isConnected ? (
              <WifiIcon fontSize="small" />
            ) : (
              <WifiOffIcon fontSize="small" />
            )}
            <Typography variant="caption" sx={{ whiteSpace: 'nowrap' }}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={isRunning ? 'Stop Alert Generation' : 'Start Alert Generation'}>
              <span>
                <Button
                  variant="contained"
                  color={isRunning ? 'error' : 'primary'}
                  onClick={toggleGeneration}
                  startIcon={isRunning ? <StopIcon /> : <PlayArrowIcon />}
                  size={isMobile ? 'small' : 'medium'}
                  disabled={!isConnected}
                  sx={{
                    whiteSpace: 'nowrap',
                    minWidth: 'auto',
                    px: { xs: 1.5, sm: 2 },
                    '&.Mui-disabled': {
                      backgroundColor: theme.palette.action.disabledBackground,
                      color: theme.palette.action.disabled
                    }
                  }}
                >
                  {isMobile ? (isRunning ? 'Stop' : 'Start') : (isRunning ? 'Stop Generation' : 'Start Generation')}
                </Button>
              </span>
            </Tooltip>
            
            <Tooltip title="Clear All Alerts">
              <span>
                <Button
                  variant="outlined"
                  onClick={clearAlerts}
                  size={isMobile ? 'small' : 'medium'}
                  disabled={alertsCount.total === 0}
                  sx={{
                    whiteSpace: 'nowrap',
                    minWidth: 'auto',
                    px: { xs: 1.5, sm: 2 },
                    '&.Mui-disabled': {
                      borderColor: theme.palette.action.disabledBackground,
                      color: theme.palette.action.disabled
                    }
                  }}
                >
                  {isMobile ? 'Clear' : 'Clear Alerts'}
                </Button>
              </span>
            </Tooltip>
            
            <Tooltip title={viewMode === 'dashboard' ? 'Switch to Table View' : 'Switch to Dashboard View'}>
              <IconButton
                onClick={toggleViewMode}
                color="primary"
                size={isMobile ? 'small' : 'medium'}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  '&:hover': {
                    backgroundColor: theme.palette.action.hover
                  }
                }}
              >
                {viewMode === 'dashboard' ? <TableViewIcon /> : <DashboardIcon />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Box>

      {/* Main Content */}
      <Box component="main" sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Traffic Log Table */}
        <Paper sx={{ p: 2, flex: 1, overflow: 'auto' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Network Traffic Log</Typography>
            <Typography variant="caption" color="textSecondary">
              Showing {Math.min(rowsPerPage, trafficLog.length)} of {trafficLog.length} entries
            </Typography>
          </Box>
          <TableContainer sx={{ maxHeight: 300, position: 'relative' }}>
            {trafficLog.length === 0 && (
              <Box sx={{ 
                position: 'absolute', 
                top: '50%', 
                left: '50%', 
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                p: 2
              }}>
                <Typography variant="body2" color="textSecondary">
                  No traffic data available. Waiting for alerts...
                </Typography>
              </Box>
            )}
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Destination</TableCell>
                  <TableCell>Severity</TableCell>
                  <TableCell>Description</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {trafficLog.length > 0 ? (
                  trafficLog
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((log, index) => {
                      console.log(`[DEBUG] Rendering traffic log entry ${index}:`, log);
                      return (
                        <TableRow key={index} hover>
                          <TableCell>
                            <Tooltip title={new Date(log.timestamp).toLocaleString()} arrow>
                              <Typography variant="body2" noWrap>
                                {new Date(log.timestamp).toLocaleTimeString()}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              size="small" 
                              label={log.type} 
                              color={log.type === 'SIDS' ? 'primary' : log.type === 'AIDS' ? 'secondary' : 'default'}
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>{log.source}</TableCell>
                          <TableCell>{log.destination}</TableCell>
                          <TableCell>
                            <Box 
                              component="span" 
                              sx={{
                                display: 'inline-block',
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                bgcolor: getSeverityColor(log.severity),
                                mr: 1
                              }}
                            />
                            {log.severity}
                          </TableCell>
                          <TableCell>{log.description}</TableCell>
                        </TableRow>
                      );
                    })
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center' }}>
                      <Typography variant="body2" color="textSecondary">
                        No traffic data available. Waiting for alerts...
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={trafficLog.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </Paper>

        {/* Metrics Dashboard */}
        <Paper sx={{ p: 2, flex: 2, overflow: 'auto' }}>
          <Tabs 
            value={activeTab} 
            onChange={(e, newValue) => setActiveTab(newValue)}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
            sx={{ mb: 2 }}
          >
            <Tab label="Network Alerts" icon={<WifiIcon />} />
            <Tab label="Anomaly Detection" icon={<WarningIcon />} />
            <Tab label="Host Intrusion" icon={<StorageIcon />} />
          </Tabs>
          
          {viewMode === 'table' ? (
            <AlertsTable 
              alerts={currentAlerts} 
              type={activeTab === 0 ? 'sids' : activeTab === 1 ? 'aids' : 'hids'}
            />
          ) : (
            <MetricsDashboard alerts={allAlerts} />
          )}
        </Paper>
      </Box>

      {/* Notification Snackbar */}
      <Snackbar
        open={!!notification}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        sx={{ '& .MuiAlert-filled': { minWidth: '300px' } }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification?.severity || 'info'}
          variant="filled"
          elevation={6}
        >
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
              {notification?.title || 'Notification'}
            </Typography>
            <Typography variant="body2">
              {notification?.message || ''}
            </Typography>
          </Box>
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AlertsDashboard;
