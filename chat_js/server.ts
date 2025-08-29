// Load environment variables from .env file
import 'dotenv/config';

// Initialize custom logger with line numbers
import './logger';

import express from 'express';
import http from 'http';
import { WebSocketServer } from 'ws';
import cors from 'cors';
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
  
  console.log(`Client connected: ${userId} for thread: ${threadId}`);
  
  // Create or get existing session for this thread
  let session = sessions.get(threadId);
  if (!session) {
    session = new Session(BigInt(threadId), BigInt(userId), new Date(), ws);
    sessions.set(threadId, session);
    console.log(`Created new session for thread: ${threadId}`);
  } else {
    console.log(`Using existing session for thread: ${threadId}`);
  }
  
  // Send welcome message
  ws.send(JSON.stringify({
    type: 'connection',
    // clientId: clientId,
    userId: userId,
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
      
      console.log(`Received from ${userId} in thread ${threadId}:`, message);
      session.handleUserMessage(message.body || message.message || JSON.stringify(message));
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
    console.log(`Client disconnected: ${userId} from thread ${threadId}, code: ${code}, reason: ${reason}`);
    
    // Remove client from clients map
    clients.delete(userId);
    
    // Check if this was the last client for this thread
    const threadClients = Array.from(clients.values()).filter(client => client.threadId === threadId);
    if (threadClients.length === 0) {
      console.log(`No more clients for thread ${threadId}, cleaning up session`);
      sessions.delete(threadId);
    }
  });
  
  // Handle errors
  ws.on('error', (error) => {
    console.error(`WebSocket error for client ${userId} in thread ${threadId}:`, error);
    handleClientDisconnect(userId);
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

// Graceful shutdown handling
process.on('SIGINT', async () => {
  console.log('\nReceived SIGINT, shutting down gracefully...');
  
  // Close WebSocket server
  wss.close(() => {
    console.log('WebSocket server closed');
  });
  
  // Close HTTP server
  server.close(() => {
    console.log('HTTP server closed');
  });
  
  // Cleanup Prisma connections
  try {
    const PrismaService = await import('./src/services/prismaService').catch(() => null);
    if (PrismaService) {
      await PrismaService.default.disconnect();
      console.log('Prisma connections closed');
    }
  } catch (error) {
    console.warn('Failed to cleanup Prisma service:', error);
  }
  
  // Close all sessions
  for (const session of sessions.values()) {
    if (session.cleanup) {
      await session.cleanup();
    }
  }
  
  console.log('Graceful shutdown complete');
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('\nReceived SIGTERM, shutting down gracefully...');
  
  // Same cleanup as SIGINT
  wss.close(() => {
    console.log('WebSocket server closed');
  });
  
  server.close(() => {
    console.log('HTTP server closed');
  });
  
  try {
    const PrismaService = await import('./src/services/prismaService').catch(() => null);
    if (PrismaService) {
      await PrismaService.default.disconnect();
      console.log('Prisma connections closed');
    }
  } catch (error) {
    console.warn('Failed to cleanup Prisma service:', error);
  }
  
  for (const session of sessions.values()) {
    if (session.cleanup) {
      await session.cleanup();
    }
  }
  
  console.log('Graceful shutdown complete');
  process.exit(0);
});
