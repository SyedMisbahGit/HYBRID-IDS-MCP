import React, { useEffect, useState } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import { 
  Box, 
  Typography, 
  CircularProgress, 
  Paper, 
  Fade,
  Zoom
} from '@material-ui/core';
import { CheckCircle, Error } from '@material-ui/icons';

const useStyles = makeStyles((theme) => ({
  root: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
    zIndex: 9999,
  },
  card: {
    padding: theme.spacing(4),
    textAlign: 'center',
    maxWidth: 500,
    width: '100%',
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    margin: theme.spacing(2, 0),
    padding: theme.spacing(2),
    borderRadius: theme.shape.borderRadius,
    backgroundColor: theme.palette.background.paper,
  },
  status: {
    marginLeft: 'auto',
    display: 'flex',
    alignItems: 'center',
  },
  success: {
    color: theme.palette.success.main,
  },
  error: {
    color: theme.palette.error.main,
  },
}));

const services = [
  { id: 'nids', name: 'Network IDS', port: 8000 },
  { id: 'hids', name: 'Host IDS', port: 8001 },
  { id: 'dashboard', name: 'Dashboard', port: 3000 },
];

export default function StartupSequence({ onComplete }) {
  const classes = useStyles();
  const [activeService, setActiveService] = useState(0);
  const [completed, setCompleted] = useState({});
  const [show, setShow] = useState(true);

  useEffect(() => {
    const timer = setInterval(() => {
      if (activeService < services.length) {
        const currentService = services[activeService];
        // Simulate service check
        fetch(`http://localhost:${currentService.port}`)
          .then(() => {
            setCompleted(prev => ({
              ...prev,
              [currentService.id]: { success: true, error: null }
            }));
          })
          .catch(() => {
            setCompleted(prev => ({
              ...prev,
              [currentService.id]: { success: false, error: 'Connection failed' }
            }));
          })
          .finally(() => {
            if (activeService === services.length - 1) {
              setTimeout(() => {
                setShow(false);
                onComplete();
              }, 1500);
            }
            setActiveService(prev => prev + 1);
          });
      }
    }, 1500);

    return () => clearInterval(timer);
  }, [activeService, onComplete]);

  if (!show) return null;

  return (
    <Fade in={show}>
      <Box className={classes.root}>
        <Paper elevation={3} className={classes.card}>
          <Typography variant="h4" gutterBottom>
            🚀 Starting Hybrid IDS
          </Typography>
          <Typography variant="subtitle1" color="textSecondary" gutterBottom>
            Initializing security services...
          </Typography>
          
          {services.map((service, index) => (
            <Zoom in={index <= activeService} key={service.id}>
              <div className={classes.item}>
                <Typography>{service.name}</Typography>
                <div className={classes.status}>
                  {completed[service.id]?.success ? (
                    <CheckCircle className={classes.success} />
                  ) : completed[service.id]?.error ? (
                    <>
                      <Error className={classes.error} />
                      <Typography variant="caption" className={classes.error}>
                        {completed[service.id].error}
                      </Typography>
                    </>
                  ) : (
                    <CircularProgress size={20} />
                  )}
                </div>
              </div>
            </Zoom>
          ))}
        </Paper>
      </Box>
    </Fade>
  );
}
