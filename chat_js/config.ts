// Chat JS Server Configuration
// Set environment variables or use defaults

const config = {
  // Server Settings
  port: process.env.PORT || 3004,
  nodeEnv: process.env.NODE_ENV || 'development',
  
  // CORS Settings
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:3002,http://localhost:3001',
  
  // WebSocket Settings
  wsHost: process.env.WS_HOST || 'localhost',
  wsPort: process.env.WS_PORT || 3004,
  
  // OpenAI Configuration
  openaiApiKey: process.env.OPENAI_API_KEY || '',
  
  // QuickBooks Configuration
  qboClientId: process.env.QBO_CLIENT_ID || '',
  qboClientSecret: process.env.QBO_CLIENT_SECRET || '',
  
  // Session Management
  sessionTimeout: parseInt(process.env.SESSION_TIMEOUT || '3600000', 10),
  maxSessions: parseInt(process.env.MAX_SESSIONS || '1000', 10),
  
  // Logging
  logLevel: process.env.LOG_LEVEL || 'info',
  logFile: process.env.LOG_FILE || 'logs/chat-server.log',
  
  // Database Configuration
  databaseUrl: process.env.DATABASE_URL || '',
  
  // Intent Server Configuration
  intentServerEnabled: process.env.INTENT_SERVER_ENABLED === 'true' || true,
  defaultIntent: process.env.DEFAULT_INTENT || 'qb',
  
  // Security
  jwtSecret: process.env.JWT_SECRET || 'dev-websocket-secret-change-in-production',
  rateLimitEnabled: process.env.RATE_LIMIT_ENABLED === 'true' || true,
  maxConnectionsPerIp: parseInt(process.env.MAX_CONNECTIONS_PER_IP || '10', 10),
  
  // Development settings
  isDevelopment: process.env.NODE_ENV !== 'production',
  isProduction: process.env.NODE_ENV === 'production'
};

export default config; 