# Story Galaxy Hackathon Demo

## Architecture
This demo uses a session-based architecture where a **Console** (Desktop) and **Mobile** (Phone) share a session ID.

1. **Console** requests a new session from the Server.
2. **Server** creates a session and starts a mock "Game Loop" interval.
3. **Server** returns `session_id` and `join_url`.
4. **Console** displays QR code.
5. **Mobile** scans QR and connects via WebSocket.
6. **Server** pushes `Action` JSON payloads every 1 second.
7. **Mobile** renders UI based on `ui_hint` in the payload.

## Running the Backend
The frontend includes a fallback "Local Mode" (using BroadcastChannel) if the backend is down. To run the full experience:

1. Navigate to server directory:
   ```bash
   cd server
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the server:
   ```bash
   npm start
   ```
   Server runs on port **8080**.

## API Endpoints

### Create Session
- **POST** `/session`
- **Response**:
  ```json
  {
    "session_id": "XY123",
    "join_url": "http://192.168.1.5:3000/#/mobile/XY123"
  }
  ```

### WebSocket Stream
- **URL**: `ws://localhost:8080/session/:id/stream`
- **Direction**: Server -> Client only (in this demo)

## Action Schema
The server pushes these objects:

```typescript
interface ActionPayload {
  action: string;      // System ID (e.g., "SCAN_SECTOR")
  intention: string;   // Narrative intent
  ui_hint: 'dialogue' | 'input' | 'alert' | 'success' | 'scan';
  dialogue: string;    // Text to display
  reason: string;      // Debug info
  timestamp: number;
}
```