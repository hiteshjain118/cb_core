# Environment Setup for chat_js Server

The chat_js server uses environment variables for configuration. You can set these in your system environment or create a `.env` file.

## Environment Variables

### Server Settings
```bash
PORT=3004                    # Server port (default: 3004)
NODE_ENV=development         # Environment (development/production)
```

### CORS Settings
```bash
CORS_ORIGIN=http://localhost:3002,http://localhost:3001  # Allowed origins
```

### WebSocket Settings
```bash
WS_HOST=localhost           # WebSocket host (default: localhost)
WS_PORT=3004               # WebSocket port (default: 3004)
```

### OpenAI Configuration
```bash
OPENAI_API_KEY=your-api-key-here     # OpenAI API key for GPT features
```

### QuickBooks Configuration
```bash
QBO_CLIENT_ID=your-client-id         # QuickBooks client ID
QBO_CLIENT_SECRET=your-secret        # QuickBooks client secret
```

### Session Management
```bash
SESSION_TIMEOUT=3600000     # Session timeout in ms (default: 1 hour)
MAX_SESSIONS=1000          # Maximum concurrent sessions
```

### Logging
```bash
LOG_LEVEL=info             # Log level (debug, info, warn, error)
LOG_FILE=logs/chat-server.log  # Log file path
```

### Database Configuration
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/db  # Database URL
```

### Intent Server Configuration
```bash
INTENT_SERVER_ENABLED=true  # Enable intent server (default: true)
DEFAULT_INTENT=qb          # Default intent (default: qb)
```

### Security
```bash
JWT_SECRET=your-jwt-secret          # JWT secret for WebSocket auth
RATE_LIMIT_ENABLED=true            # Enable rate limiting
MAX_CONNECTIONS_PER_IP=10          # Max connections per IP
```

## Setting Up Environment Variables

### Option 1: Create a .env file
Create a `.env` file in the chat_js directory:

```bash
cd chat_js
cat > .env << 'EOF'
PORT=3004
NODE_ENV=development
CORS_ORIGIN=http://localhost:3002,http://localhost:3001
OPENAI_API_KEY=your-openai-api-key-here
QBO_CLIENT_ID=your-quickbooks-client-id
QBO_CLIENT_SECRET=your-quickbooks-client-secret
EOF
```

### Option 2: Export environment variables
```bash
export PORT=3004
export NODE_ENV=development
export CORS_ORIGIN=http://localhost:3002,http://localhost:3001
export OPENAI_API_KEY=your-openai-api-key-here
# ... add other variables as needed
```

### Option 3: Use with npm scripts
```bash
# In package.json, you can set environment variables:
"scripts": {
  "start": "PORT=3004 NODE_ENV=development node server.js",
  "dev": "PORT=3004 NODE_ENV=development nodemon server.js"
}
```

## Default Configuration

If no environment variables are set, the server will use defaults defined in `config.js`:

- **Port**: 3004
- **Environment**: development
- **CORS Origins**: http://localhost:3002,http://localhost:3001
- **WebSocket Host**: localhost
- **Intent Server**: Enabled
- **Default Intent**: qb
- **Rate Limiting**: Enabled
- **Max Connections per IP**: 10

## Configuration Validation

The server will log the current configuration on startup when in development mode:

```
Chat server running on port 3004
WebSocket server ready for connections
HTTP API available at http://localhost:3004/api
Environment: development
TypeScript modules loaded successfully
CORS Origins: http://localhost:3002,http://localhost:3001
Intent Server: Enabled
Default Intent: qb
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the PORT environment variable
2. **CORS errors**: Update CORS_ORIGIN to include your frontend URL
3. **Intent server errors**: Check QBO_CLIENT_ID and QBO_CLIENT_SECRET
4. **WebSocket connection failures**: Verify WS_PORT matches your frontend configuration 