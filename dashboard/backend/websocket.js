const WebSocket = require('ws');
const http = require('http');

// Create HTTP server
const server = http.createServer();
const wss = new WebSocket.Server({ server, path: '/ws/dashboard' });

// WebSocket connection handler
wss.on('connection', (ws) => {
    console.log('New WebSocket connection');
    
    // Send a welcome message
    ws.send(JSON.stringify({
        type: 'connection',
        message: 'Connected to WebSocket server',
        timestamp: new Date().toISOString()
    }));

    // Handle incoming messages
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            console.log('Received:', data);
            
            // Echo the message back to the client
            ws.send(JSON.stringify({
                type: 'echo',
                data: data,
                timestamp: new Date().toISOString()
            }));
        } catch (error) {
            console.error('Error processing message:', error);
        }
    });

    // Handle client disconnection
    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// Start the server
const PORT = 8000;
server.listen(PORT, () => {
    console.log(`WebSocket server running on ws://localhost:${PORT}/ws/dashboard`);
});

// Generate sample alerts periodically
setInterval(() => {
    const sampleAlert = {
        type: 'alert',
        payload: {
            id: Date.now(),
            type: 'nids',
            severity: Math.random() > 0.5 ? 'high' : 'medium',
            message: 'Sample alert from WebSocket server',
            timestamp: new Date().toISOString(),
            source: 'websocket',
            details: {
                protocol: 'TCP',
                src_ip: '192.168.1.' + Math.floor(Math.random() * 255),
                src_port: Math.floor(1000 + Math.random() * 50000),
                dest_ip: '192.168.1.100',
                dest_port: 80,
                rule_id: Math.floor(1000 + Math.random() * 9000)
            }
        }
    };

    // Send to all connected clients
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(sampleAlert));
        }
    });
}, 5000); // Send an alert every 5 seconds
