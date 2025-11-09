import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Header from './components/Header';
import AlertsDashboard from './components/AlertsDashboard';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h5: {
      fontWeight: 600,
    },
  },
});

class App extends React.Component {
  constructor(props) {
    super(props);
    this.notificationQueue = [];
    this.isProcessing = false;
    
    this.state = {
      systemStatus: {
        nids: { status: 'starting', message: 'Initializing Network IDS...' },
        hids: { status: 'starting', message: 'Initializing Host IDS...' },
      },
      alerts: [],
      metrics: { cpu: 0, memory_percent: 0 },
      loading: true,
      error: null,
      isConnected: false,
    };
    
    // Bind methods
    this.showNotification = this.showNotification.bind(this);
    this.processQueue = this.processQueue.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }

  // Show notification function
  showNotification(title, message, severity = 'info', duration = 3000) {
    const notification = { 
      id: Date.now(), 
      title, 
      message, 
      severity, 
      open: true, 
      duration 
    };
    this.notificationQueue.push(notification);
    this.processQueue();
  }

  // Process notification queue
  processQueue() {
    if (this.notificationQueue.length === 0 || this.isProcessing) return;
    
    this.isProcessing = true;
    const nextNotification = this.notificationQueue.shift();
    this.setState({ 
      currentNotification: nextNotification,
      open: true 
    });
    
    // Auto-close the notification after duration
    if (nextNotification.duration) {
      setTimeout(() => {
        this.handleClose(null, 'timeout');
      }, nextNotification.duration);
    }
  }

  // Handle notification close
  handleClose(event, reason) {
    if (reason === 'clickaway') return;
    this.setState({ open: false });
    setTimeout(() => {
      this.isProcessing = false;
      this.processQueue();
    }, 300);
  }

  // Initialize WebSocket connection
  initializeWebSocket = () => {
    try {
      this.ws = new WebSocket('ws://localhost:8000/ws/dashboard');
      
      this.ws.onopen = () => {
        console.log('WebSocket Connected');
        this.setState({ 
          isConnected: true,
          error: null
        });
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle different types of messages
          switch (data.type) {
            case 'alert':
              this.setState(prevState => ({
                alerts: [data.payload, ...prevState.alerts].slice(0, 100)
              }));
              this.showNotification('Alert', data.payload.message, 'warning');
              break;
              
            case 'metrics':
              this.setState(prevState => ({
                metrics: {
                  ...prevState.metrics,
                  ...data.payload
                }
              }));
              break;
              
            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.setState({ 
          isConnected: false,
          error: 'Connection error. Will attempt to reconnect...'
        });
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket Disconnected');
        this.setState({ isConnected: false });
        
        // Try to reconnect after 5 seconds
        setTimeout(() => {
          if (!this.state.isConnected) {
            console.log('Attempting to reconnect WebSocket...');
            this.initializeWebSocket();
          }
        }, 5000);
      };
      
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      this.setState({
        isConnected: false,
        error: 'Failed to connect to WebSocket server. Make sure the backend is running.'
      });
      
      // Try to reconnect after 10 seconds
      setTimeout(() => {
        if (!this.state.isConnected) {
          console.log('Retrying WebSocket connection...');
          this.initializeWebSocket();
        }
      }, 10000);
    }
  };

  // Lifecycle method: componentDidMount
  componentDidMount() {
    // NIDS Starting
    setTimeout(() => {
      this.setState(prevState => ({
        systemStatus: {
          ...prevState.systemStatus,
          nids: { status: 'starting', message: 'Loading network signatures...' }
        }
      }));
      
      this.showNotification('NIDS', 'Network IDS is starting up...', 'info');
      
      // Simulate NIDS starting up
      setTimeout(() => {
        this.setState(prevState => ({
          systemStatus: {
            ...prevState.systemStatus,
            nids: { status: 'running', message: 'Monitoring network traffic...' }
          }
        }));
        this.showNotification('NIDS', 'Network IDS is now running', 'success');
        
        // HIDS Starting
        setTimeout(() => {
          this.setState(prevState => ({
            systemStatus: {
              ...prevState.systemStatus,
              hids: { status: 'starting', message: 'Initializing system monitoring...' }
            }
          }));
          this.showNotification('HIDS', 'Host IDS is starting up...', 'info');
          
          // Simulate HIDS starting up
          setTimeout(() => {
            this.setState(prevState => ({
              systemStatus: {
                ...prevState.systemStatus,
                hids: { status: 'running', message: 'Monitoring system activities...' }
              },
              loading: false
            }));
            this.showNotification('HIDS', 'Host IDS is now running', 'success');
            
            // Initialize WebSocket connection
            this.initializeWebSocket();
            
          }, 2000);
          
        }, 1000);
        
      }, 2000);
      
    }, 1000);
  }
  
  // Lifecycle method: componentWillUnmount
  componentWillUnmount() {
    // Clean up WebSocket connection
    if (this.ws) {
      this.ws.onclose = null; // Prevent reconnection attempts
      this.ws.close();
    }
    
    // Clear any pending timeouts
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
  }

  render() {
    const { error, loading, isConnected } = this.state;

    if (loading) {
      return (
        <ThemeProvider theme={darkTheme}>
          <CssBaseline />
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100vh',
            bgcolor: 'background.default'
          }}>
            <CircularProgress />
          </Box>
        </ThemeProvider>
      );
    }

    if (error) {
      return (
        <ThemeProvider theme={darkTheme}>
          <CssBaseline />
          <Box sx={{ 
            p: 3,
            bgcolor: 'background.default',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <Header />
            <Box sx={{ 
              flexGrow: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              textAlign: 'center',
              p: 3
            }}>
              <Alert 
                severity="error" 
                sx={{ 
                  maxWidth: 600,
                  width: '100%',
                  mb: 2
                }}
              >
                {error}
              </Alert>
              {!isConnected && (
                <CircularProgress size={24} sx={{ mt: 2 }} />
              )}
            </Box>
          </Box>
        </ThemeProvider>
      );
    }
    
    return (
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <Box sx={{ 
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          bgcolor: 'background.default'
        }}>
          <Header />
          <Box 
            component="main" 
            sx={{ 
              flexGrow: 1,
              p: { xs: 2, sm: 3 },
              pt: { xs: 8, sm: 9 },
              overflow: 'auto',
              bgcolor: 'background.default'
            }}
          >
            <Container 
              maxWidth={false} 
              sx={{ 
                maxWidth: '1440px',
                px: { xs: 2, sm: 3 },
                py: 2
              }}
            >
              {!isConnected && (
                <Alert 
                  severity="warning" 
                  sx={{ 
                    mb: 3,
                    width: '100%',
                    maxWidth: '100%'
                  }}
                >
                  Connecting to WebSocket server...
                </Alert>
              )}
              <AlertsDashboard isConnected={isConnected} />
            </Container>
          </Box>
        </Box>
      </ThemeProvider>
    );
  }
}

export default App;
