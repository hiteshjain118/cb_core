// Load environment variables from .env file
import 'dotenv/config';

// Initialize custom logger with line numbers
import './logger';

import express from 'express';
import http from 'http';
import { WebSocketServer, WebSocket } from 'ws';
import cors from 'cors';
import { v4 as uuidv4 } from 'uuid';
import config from './config';

// Import our TypeScript types directly from source
import {
  ChatMessage,
  ChatMemory
} from './src/types';

// Import Intent Server types (Intent Registry etc.)
import {
  INTENT_REGISTRY
} from './src/types/intent-registry';

// Import Session class
import Session from './src/session';

// Import QBServer
import { QBServer } from './src/index';

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server });

// Middleware
app.use(cors({
  origin: config.corsOrigin.split(','),
  credentials: true
}));
app.use(express.json());

// Create intent registry and QB server
const intentRegistry = INTENT_REGISTRY;

// Store connected clients
const clients = new Map();
const sessions = new Map();
// Store conversation memory per session
const conversationMemory = new Map();

// WebSocket connection handling
wss.on('connection', (ws, req) => {
  const clientId = uuidv4();
  
  // Parse query parameters to get threadId and userId
  if (!req.url) {
    console.error('No URL in WebSocket connection request');
    ws.close(1008, 'No URL in request');
    return;
  }
  
  const url = new URL(req.url, `http://${req.headers.host}`);
  const threadId = url.searchParams.get('threadId');
  const userId = url.searchParams.get('userId');
  
  if (!threadId || !userId) {
    console.error('Missing threadId or userId in WebSocket connection');
    ws.close(1008, 'Missing threadId or userId');
    return;
  }
  
  console.log(`Client connected: ${clientId} for thread: ${threadId}, user: ${userId}`);
  
  // Store client connection with thread info
  clients.set(clientId, {
    ws,
    threadId,
    userId,
    connected: true
  });
  
  // Create or get existing session for this thread
  let session = sessions.get(threadId);
  if (!session) {
    session = new Session(BigInt(threadId), BigInt(userId), new Date());
    sessions.set(threadId, session);
    console.log(`Created new session for thread: ${threadId}`);
  } else {
    console.log(`Using existing session for thread: ${threadId}`);
  }
  
  // Send welcome message
  ws.send(JSON.stringify({
    type: 'connection',
    clientId: clientId,
    threadId: threadId,
    message: 'Connected to chat server',
    timestamp: new Date().toISOString()
  }));
  
  // Handle incoming messages
  ws.on('message', (data) => {
    try {
      // Convert RawData to string
      const messageString = data.toString();
      const message = JSON.parse(messageString);
      const messageThreadId = message.threadId || threadId;
      
      // Verify the message is for the correct thread
      if (messageThreadId !== threadId) {
        console.error(`Thread mismatch: message for ${messageThreadId}, connected to ${threadId}`);
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Thread mismatch',
          timestamp: new Date().toISOString()
        }));
        return;
      }
      
      const session = sessions.get(threadId);
      if (!session) {
        console.error(`Session not found for threadId: ${threadId}`);
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Session not found',
          timestamp: new Date().toISOString()
        }));
        return;
      }
      
      console.log(`Received from ${clientId} in thread ${threadId}:`, message);

      // Send immediate acknowledgment to client
      ws.send(JSON.stringify({
        type: 'message_received',
        clientId: clientId,
        threadId: threadId,
        messageId: message.messageId || Date.now().toString(),
        timestamp: new Date().toISOString()
      }));

      // Process message asynchronously
      const userMessageContent = message.body || message.message || JSON.stringify(message);
      
      // Handle message processing in background
      setImmediate(async () => {
        try {
          console.log(`Processing message for thread ${threadId}...`);
          const response = await session.handleUserMessage(userMessageContent);
          console.log(`Response for thread ${threadId}: ${response}`);
          
          if (response) {
            // Extract message content from response
            let messageContent = response.body || response.message || response.content;
            
            // If no content found, the response might be the message itself
            if (!messageContent && typeof response === 'string') {
              messageContent = response;
            }
            
            // If still no content, there might be an issue with the response format
            if (!messageContent) {
              console.warn(`No message content found in response:`, response);
              messageContent = 'I received your message but had trouble generating a response.';
            }
            
            console.log(`Sending AI response to client: ${messageContent}`);
            
            // Send AI response to client
            ws.send(JSON.stringify({
              type: 'chat',
              clientId: clientId,
              threadId: threadId,
              message: messageContent,
              timestamp: new Date().toISOString()
            }));
          } else {
            console.error(`No response from session for thread ${threadId}`);
            ws.send(JSON.stringify({
              type: 'error',
              clientId: clientId,
              threadId: threadId,
              message: 'AI agent is having issues processing your request',
              timestamp: new Date().toISOString()
            }));
          }
        } catch (error) {
          console.error(`Error processing message for thread ${threadId}:`, error);
          ws.send(JSON.stringify({
            type: 'error',
            clientId: clientId,
            threadId: threadId,
            message: 'An error occurred while processing your message',
            timestamp: new Date().toISOString()
          }));
        }
      });
    } catch (error) {
      console.error('Error parsing message:', error);
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Invalid message format',
        timestamp: new Date().toISOString()
      }));
    }
  });
  
  // Handle client disconnect
  ws.on('close', (code, reason) => {
    console.log(`Client disconnected: ${clientId} from thread ${threadId}, code: ${code}, reason: ${reason}`);
    
    // Remove client from clients map
    clients.delete(clientId);
    
    // Check if this was the last client for this thread
    const threadClients = Array.from(clients.values()).filter(client => client.threadId === threadId);
    if (threadClients.length === 0) {
      console.log(`No more clients for thread ${threadId}, cleaning up session`);
      sessions.delete(threadId);
    }
  });
  
  // Handle errors
  ws.on('error', (error) => {
    console.error(`WebSocket error for client ${clientId} in thread ${threadId}:`, error);
    handleClientDisconnect(clientId);
  });
});

// Helper function to handle client disconnection
function handleClientDisconnect(clientId: string) {
  const client = clients.get(clientId);
  if (client) {
    const { threadId } = client;
    clients.delete(clientId);
    
    // Check if this was the last client for this thread
    const threadClients = Array.from(clients.values()).filter(client => client.threadId === threadId);
    if (threadClients.length === 0) {
      console.log(`No more clients for thread ${threadId}, cleaning up session`);
      sessions.delete(threadId);
    }
  }
}


// HTTP routes
app.get('/api/status', (req, res) => {
  res.json({
    status: 'running',
    service: 'chat_js_server',
    clients: clients.size,
    sessions: conversationMemory.size,
    uptime: process.uptime(),
    modules: {
      session: !!Session,
      qbServer: !!QBServer,
      chatMemory: !!ChatMemory
    },
    timestamp: new Date().toISOString()
  });
});

app.get('/api/clients', (req, res) => {
  const clientList = Array.from(clients.entries()).map(([id, client]) => ({
    id,
    threadId: client.threadId.toString(),
    userId: client.userId.toString(),
    connected: client.connected
  }));
  
  res.json({
    clients: clientList,
    count: clientList.length
  });
});

// Start server
server.listen(config.port, () => {
  console.log(`Chat server running on port ${config.port}`);
  console.log(`WebSocket server ready for connections`);
  console.log(`HTTP API available at http://localhost:${config.port}/api`);
  console.log(`Environment: ${config.nodeEnv}`);
  console.log(`TypeScript modules loaded successfully`);
  console.log(`Custom logger initialized with line numbers`);
  
  if (config.isDevelopment) {
    console.log(`CORS Origins: ${config.corsOrigin}`);
    console.log(`Intent Server: ${config.intentServerEnabled ? 'Enabled' : 'Disabled'}`);
    console.log(`Default Intent: ${config.defaultIntent}`);
  }
});
