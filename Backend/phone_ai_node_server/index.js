const express = require('express');
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');
const cors = require('cors');

// Import realtime shooting module
const {
  setupShootingRoutes,
  setupShootingWebSocket
} = require('./realtime-shooting');

const app = express();
app.use(cors());
app.use(express.json());

// Check for SSL certificates
const certPath = path.join(__dirname, 'localhost+3.pem');
const keyPath = path.join(__dirname, 'localhost+3-key.pem');
const useHttps = fs.existsSync(certPath) && fs.existsSync(keyPath);

let server;
if (useHttps) {
  const sslOptions = {
    key: fs.readFileSync(keyPath),
    cert: fs.readFileSync(certPath),
  };
  server = https.createServer(sslOptions, app);
  console.log('🔒 SSL certificates found, using HTTPS');
} else {
  server = http.createServer(app);
  console.log('⚠️  No SSL certificates, using HTTP');
}

const wss = new WebSocketServer({ server });

const SESSIONS = new Map(); // sessionId -> { clients: Set<ws>, interval: fn }

const MOCK_ACTIONS = [
  {
    action: "INIT_SYSTEM",
    intention: "Establish neural link",
    ui_hint: "alert",
    dialogue: "Initializing Story Galaxy Interface... Connection stable.",
    reason: "System startup sequence initiated."
  },
  {
    action: "SCAN_SECTOR",
    intention: "Locate corrupted fragments",
    ui_hint: "scan",
    dialogue: "Scanning Sector 7... Anomalies detected in the narrative flow.",
    reason: "User entered a new zone."
  },
  {
    action: "ENCOUNTER_GLITCH",
    intention: "Present challenge",
    ui_hint: "dialogue",
    dialogue: "The Silence is overwhelming here. 'I... cannot remember the color of the rose.'",
    reason: "Narrative conflict introduction."
  },
  {
    action: "REQUEST_INPUT",
    intention: "Solicit player creativity",
    ui_hint: "input",
    dialogue: "We need a spark. What color was the rose? Transmit your memory now.",
    reason: "Interactive puzzle element."
  },
  {
    action: "RESTORE_FRAGMENT",
    intention: "Reward player action",
    ui_hint: "success",
    dialogue: "Data received. Reconstructing... It's beautiful. The sector is stabilizing.",
    reason: "Puzzle solved successfully."
  }
];

// Start pumping actions to a session
function startSessionPump(sessionId) {
  const session = SESSIONS.get(sessionId);
  if (!session) return;

  if (session.interval) clearInterval(session.interval);

  let actionIndex = 0;

  // Send first action immediately
  const send = () => {
    const template = MOCK_ACTIONS[actionIndex % MOCK_ACTIONS.length];
    const payload = JSON.stringify({
      ...template,
      timestamp: Date.now()
    });

    session.clients.forEach(client => {
      if (client.readyState === 1) { // OPEN
        client.send(payload);
      }
    });

    actionIndex++;
  };

  send();
  session.interval = setInterval(send, 1000); // 1s interval
}

// REST API: Create Session
app.post('/session', (req, res) => {
  const sessionId = Math.random().toString(36).substring(2, 8).toUpperCase();

  // Use the origin from the request to construct the join URL
  let clientOrigin = req.headers.origin || 'http://localhost:3000';

  // 如果请求是 HTTP 但端口是 3000，强制转换为 HTTPS（摄像头访问需要）
  if (clientOrigin.startsWith('http://') && clientOrigin.includes(':3000')) {
    clientOrigin = clientOrigin.replace('http://', 'https://');
    console.log(`[Session] 自动将 origin 转换为 HTTPS: ${clientOrigin}`);
  }

  // 重要：将 localhost 替换为实际 IP 地址，以便手机访问
  // 从请求头获取客户端 IP，或使用连接的实际 IP
  const clientIP = req.headers['x-forwarded-for'] ||
    req.headers['x-real-ip'] ||
    req.connection.remoteAddress ||
    req.socket.remoteAddress;

  // 获取服务器监听的 IP（通常是 0.0.0.0，需要获取实际 IP）
  // 简单方法：从 Host 头提取，或使用环境变量
  const serverIP = process.env.SERVER_IP ||
    (clientOrigin.includes('localhost') ?
      (req.headers.host ? req.headers.host.split(':')[0] : 'localhost') :
      clientOrigin.match(/https?:\/\/([^:]+)/)?.[1]);

  // 如果 origin 包含 localhost，尝试替换为实际 IP
  if (clientOrigin.includes('localhost') || clientOrigin.includes('127.0.0.1')) {
    // 尝试从 Host 头获取
    const hostHeader = req.headers.host;
    if (hostHeader && !hostHeader.includes('localhost')) {
      const hostname = hostHeader.split(':')[0];
      clientOrigin = clientOrigin.replace(/localhost|127\.0\.0\.1/g, hostname);
      console.log(`[Session] 将 localhost 替换为 ${hostname}: ${clientOrigin}`);
    } else {
      // 如果无法从请求获取，使用默认 IP（需要用户配置）
      console.warn(`[Session] 警告: origin 包含 localhost，手机可能无法访问`);
      console.warn(`[Session] 建议: 使用 IP 地址访问电脑端，例如 https://10.10.11.18:3000`);
    }
  }

  const joinUrl = `${clientOrigin}/#/mobile/${sessionId}`;

  console.log(`[Session] Created ${sessionId}`);
  console.log(`[Session] Join URL: ${joinUrl}`);

  SESSIONS.set(sessionId, { clients: new Set(), interval: null });
  startSessionPump(sessionId);

  res.json({ session_id: sessionId, join_url: joinUrl });
});

// REST API: Get Session Info (Optional debug endpoint)
app.get('/session/:id', (req, res) => {
  const session = SESSIONS.get(req.params.id);
  if (!session) return res.status(404).json({ error: "Session not found" });
  res.json({ active_clients: session.clients.size });
});

// WebSocket: Stream
wss.on('connection', (ws, req) => {
  // Parse URL: /session/:id/stream or /shooting/:id/stream
  const urlParts = req.url.split('/');

  // Check if this is a shooting session - delegate to shooting handler
  if (urlParts[1] === 'shooting') {
    // Shooting sessions are handled by setupShootingWebSocket
    // Don't close the connection, let the shooting handler deal with it
    console.log(`[WS] Shooting session connection detected, delegating to shooting handler`);
    return;
  }

  // expected format: ["", "session", "SESSION_ID", "stream"]
  const sessionId = urlParts[2];

  if (!sessionId) {
    ws.close();
    return;
  }

  console.log(`[WS] Client connecting to ${sessionId}`);

  // Auto-create session if it doesn't exist (robustness for demo)
  if (!SESSIONS.has(sessionId)) {
    SESSIONS.set(sessionId, { clients: new Set(), interval: null });
    startSessionPump(sessionId);
  }

  const session = SESSIONS.get(sessionId);
  session.clients.add(ws);

  ws.on('close', () => {
    session.clients.delete(ws);
    console.log(`[WS] Client disconnected from ${sessionId}`);
    // Optional: Cleanup empty sessions
    if (session.clients.size === 0) {
      // setTimeout(() => { ... }, 60000); 
    }
  });
});

const PORT = process.env.PORT || 8080;

// Setup realtime shooting routes and WebSocket handler
setupShootingRoutes(app);
setupShootingWebSocket(wss);

// 监听 0.0.0.0 以允许局域网访问
server.listen(PORT, '0.0.0.0', () => {
  const protocol = useHttps ? 'https' : 'http';
  const wsProtocol = useHttps ? 'wss' : 'ws';
  console.log(`Story Galaxy Server running on port ${PORT}`);
  console.log(`- REST: ${protocol}://0.0.0.0:${PORT} (accessible from LAN)`);
  console.log(`- WS:   ${wsProtocol}://0.0.0.0:${PORT} (accessible from LAN)`);
  console.log(`\nRealtime Shooting Advisor endpoints:`);
  console.log(`- POST /shooting/session - Create shooting session`);
  console.log(`- GET  /shooting/session/:id - Get session info`);
  console.log(`- WS   /shooting/:id/stream - WebSocket stream`);
  console.log(`\nTo access from mobile device:`);
  console.log(`- Find your local IP: ip addr show | grep "inet "`);
  console.log(`- Use: ${protocol}://YOUR_LOCAL_IP:3000`);
});