# WebSocket Chat Server

A real-time chat application built with Node.js and WebSockets, featuring room-based messaging, user management, and a modern web client interface.

## Features

- **Real-time messaging** using WebSocket connections
- **Room-based chat** - users can join different chat rooms
- **User management** - unique client IDs and usernames
- **Typing indicators** - shows when users are typing
- **HTTP API** - status, rooms, and client information endpoints
- **Modern web client** - responsive HTML interface
- **Auto-reconnection** - handles connection drops gracefully

## Project Structure

```
chat_js/
├── server.js          # Main WebSocket server
├── package.json       # Dependencies and scripts
├── public/            # Static web client files
│   └── index.html    # Chat client interface
└── README.md         # This file
```

## Installation

1. Navigate to the project directory:
   ```bash
   cd chat_js
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the server:
   ```bash
   npm start
   ```

   Or for development with auto-restart:
   ```bash
   npm run dev
   ```

## Usage

### Starting the Server

The server runs on port 3004 by default. You can change this by setting the `PORT` environment variable:

```bash
PORT=3005 npm start
```

### Web Client

1. Open your browser and navigate to `http://localhost:3004`
2. Click "Connect" to establish a WebSocket connection
3. Enter a username and room name, then click "Join Room"
4. Start chatting!

### API Endpoints

- `GET /api/status` - Server status and statistics
- `GET /api/rooms` - List of active rooms and members
- `GET /api/clients` - List of connected clients

## WebSocket Message Types

### Client to Server

- **`join`** - Join a chat room
  ```json
  {
    "type": "join",
    "username": "alice",
    "room": "general"
  }
  ```

- **`chat`** - Send a chat message
  ```json
  {
    "type": "chat",
    "message": "Hello, world!"
  }
  ```

- **`leave`** - Leave current room
  ```json
  {
    "type": "leave"
  }
  ```

- **`typing`** - Typing indicator
  ```json
  {
    "type": "typing",
    "isTyping": true
  }
  ```

### Server to Client

- **`connection`** - Connection established
- **`joined`** - Successfully joined a room
- **`join`** - Another user joined the room
- **`leave`** - Another user left the room
- **`chat`** - Chat message from another user
- **`typing`** - Typing indicator from another user
- **`error`** - Error message

## Architecture

### Server Components

- **Express HTTP server** - Handles API requests and serves static files
- **WebSocket server** - Manages real-time connections
- **Client manager** - Tracks connected clients and their states
- **Room manager** - Handles room creation, joining, and leaving
- **Message router** - Routes messages to appropriate handlers

### Client Features

- **Connection management** - Connect/disconnect to WebSocket server
- **Room management** - Join rooms with custom usernames
- **Real-time messaging** - Send and receive messages instantly
- **Typing indicators** - Show when others are typing
- **Responsive design** - Works on desktop and mobile devices

## Development

### Prerequisites

- Node.js 14+ 
- npm or yarn

### Dependencies

- **`ws`** - WebSocket server implementation
- **`express`** - HTTP server framework
- **`cors`** - Cross-origin resource sharing
- **`uuid`** - Unique identifier generation
- **`nodemon`** - Development auto-restart (dev dependency)

### Running Tests

Currently no test suite is implemented. To add tests:

1. Install a testing framework (Jest, Mocha, etc.)
2. Create test files in a `tests/` directory
3. Add test script to `package.json`

### Deployment

The server can be deployed to various platforms:

- **Heroku** - Set `PORT` environment variable
- **AWS EC2** - Use PM2 or systemd for process management
- **Docker** - Create a Dockerfile for containerization
- **Vercel/Netlify** - For the static client files

## Security Considerations

- **Input validation** - All messages are validated before processing
- **Rate limiting** - Consider implementing message rate limiting
- **Authentication** - Add user authentication for production use
- **HTTPS/WSS** - Use secure connections in production

## Performance

- **Memory efficient** - Uses Maps and Sets for O(1) lookups
- **Scalable** - Can handle hundreds of concurrent connections
- **Low latency** - Direct WebSocket communication
- **Resource cleanup** - Automatic cleanup of disconnected clients

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Change the port in the server configuration
   - Kill processes using the default port

2. **WebSocket connection failed**
   - Check if the server is running
   - Verify the WebSocket URL format
   - Check firewall settings

3. **Messages not appearing**
   - Ensure you're connected to the WebSocket
   - Check browser console for errors
   - Verify you've joined a room

### Debug Mode

Enable debug logging by setting the `DEBUG` environment variable:

```bash
DEBUG=* npm start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Future Enhancements

- [ ] User authentication and profiles
- [ ] Private messaging
- [ ] File sharing
- [ ] Message persistence
- [ ] Push notifications
- [ ] Mobile app
- [ ] Voice/video chat
- [ ] Message encryption
- [ ] Admin panel
- [ ] Analytics dashboard 