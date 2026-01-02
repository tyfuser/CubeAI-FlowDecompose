/**
 * Realtime Shooting Advisor WebSocket Handler
 * 
 * Extends the story-galaxy-controller server with realtime shooting session support.
 * Handles frame buffer reception (Base64 JPEG) and advice push to clients.
 * 
 * Requirements: 9.1, 9.2, 9.3
 */

const SHOOTING_SESSIONS = new Map(); // sessionId -> ShootingSession

/**
 * Shooting session state
 */
class ShootingSession {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.clients = new Set();      // Mobile clients
    this.consoles = new Set();     // Console clients (for monitoring)
    this.createdAt = Date.now();
    this.lastHeartbeat = Date.now();
    this.heartbeatInterval = null;
    this.analysisCallback = null;
    this.totalFramesReceived = 0;
    this.totalAdviceSent = 0;
    this.currentTask = null;      // Current task state
    this.telemetryInterval = null; // Interval for sending telemetry
    this.taskSwitchInterval = null; // Interval for switching tasks
  }

  addClient(ws) {
    this.clients.add(ws);
    console.log(`[Shooting] 📱 Mobile client joined session ${this.sessionId}, total: ${this.clients.size}`);
    
    // 立即发送智能任务和遥测数据
    console.log('[Shooting] 🎬 Sending initial task and telemetry to new client');
    sendMockTask(this);
    sendMockTelemetry(this);
    
    // 开始定期发送遥测数据（每500ms）
    if (!this.telemetryInterval && this.clients.size > 0) {
      console.log('[Shooting] ⏱️ Starting telemetry interval');
      this.telemetryInterval = setInterval(() => {
        sendMockTelemetry(this);
      }, 500);
    }
    
    // 每10秒可能切换任务（模拟环境变化）
    if (!this.taskSwitchInterval && this.clients.size > 0) {
      console.log('[Shooting] 🔄 Starting task switch interval');
      this.taskSwitchInterval = setInterval(() => {
        // 30% 概率切换任务
        if (Math.random() < 0.3) {
          console.log('[Task] 🌍 Environment changed, selecting new task...');
          sendMockTask(this);
        }
      }, 10000);
    }
    
    // Notify consoles
    this.notifyConsoles({
      type: 'client_connected',
      client_count: this.clients.size,
      timestamp: Date.now()
    });
  }

  removeClient(ws) {
    this.clients.delete(ws);
    console.log(`[Shooting] Mobile client left session ${this.sessionId}, remaining: ${this.clients.size}`);
    
    // 如果没有客户端了，停止所有定时器
    if (this.clients.size === 0) {
      if (this.telemetryInterval) {
        clearInterval(this.telemetryInterval);
        this.telemetryInterval = null;
      }
      if (this.taskSwitchInterval) {
        clearInterval(this.taskSwitchInterval);
        this.taskSwitchInterval = null;
      }
    }
    
    // Notify consoles
    this.notifyConsoles({
      type: 'client_disconnected',
      client_count: this.clients.size,
      timestamp: Date.now()
    });
  }

  addConsole(ws) {
    this.consoles.add(ws);
    console.log(`[Shooting] Console joined session ${this.sessionId}, total consoles: ${this.consoles.size}`);
  }

  removeConsole(ws) {
    this.consoles.delete(ws);
    console.log(`[Shooting] Console left session ${this.sessionId}, remaining consoles: ${this.consoles.size}`);
  }

  hasClients() {
    return this.clients.size > 0 || this.consoles.size > 0;
  }

  /**
   * Notify all console clients
   * @param {Object} message - Message to send
   */
  notifyConsoles(message) {
    const payload = JSON.stringify(message);
    this.consoles.forEach(console => {
      if (console.readyState === 1) { // OPEN
        console.send(payload);
      }
    });
  }

  /**
   * Broadcast advice to all connected mobile clients
   * @param {Object} advice - Advice payload to send
   */
  broadcastAdvice(advice) {
    const payload = JSON.stringify({
      type: 'advice',
      ...advice,
      timestamp: Date.now()
    });

    this.clients.forEach(client => {
      if (client.readyState === 1) { // OPEN
        client.send(payload);
        this.totalAdviceSent++;
      }
    });

    // Notify consoles about advice sent
    this.notifyConsoles({
      type: 'advice_sent',
      advice: advice,
      timestamp: Date.now()
    });
  }

  /**
   * Send heartbeat to all clients
   */
  sendHeartbeat() {
    const payload = JSON.stringify({
      type: 'heartbeat',
      timestamp: Date.now(),
      session_id: this.sessionId
    });

    this.clients.forEach(client => {
      if (client.readyState === 1) {
        client.send(payload);
      }
    });
    this.lastHeartbeat = Date.now();
  }

  /**
   * Start heartbeat interval (5 seconds per Requirement 9.5)
   */
  startHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, 5000);
  }

  /**
   * Stop heartbeat interval
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Get session statistics
   */
  getStats() {
    return {
      session_id: this.sessionId,
      created_at: this.createdAt,
      active_clients: this.clients.size,
      total_frames_received: this.totalFramesReceived,
      total_advice_sent: this.totalAdviceSent,
      last_heartbeat: this.lastHeartbeat
    };
  }
}

/**
 * Create a new shooting session
 * @param {string} sessionId - Session identifier
 * @returns {ShootingSession} - Created session
 */
function createShootingSession(sessionId) {
  const session = new ShootingSession(sessionId);
  SHOOTING_SESSIONS.set(sessionId, session);
  session.startHeartbeat();
  console.log(`[Shooting] Created session ${sessionId}`);
  return session;
}

/**
 * Get or create a shooting session
 * @param {string} sessionId - Session identifier
 * @returns {ShootingSession} - Session instance
 */
function getOrCreateShootingSession(sessionId) {
  if (!SHOOTING_SESSIONS.has(sessionId)) {
    return createShootingSession(sessionId);
  }
  return SHOOTING_SESSIONS.get(sessionId);
}

/**
 * Get a shooting session
 * @param {string} sessionId - Session identifier
 * @returns {ShootingSession|null} - Session or null if not found
 */
function getShootingSession(sessionId) {
  return SHOOTING_SESSIONS.get(sessionId) || null;
}

/**
 * Delete a shooting session
 * @param {string} sessionId - Session identifier
 */
function deleteShootingSession(sessionId) {
  const session = SHOOTING_SESSIONS.get(sessionId);
  if (session) {
    session.stopHeartbeat();
    SHOOTING_SESSIONS.delete(sessionId);
    console.log(`[Shooting] Deleted session ${sessionId}`);
  }
}

/**
 * Handle incoming frame buffer from mobile client
 * @param {ShootingSession} session - Session instance
 * @param {Object} payload - Frame buffer payload
 * @param {WebSocket} ws - WebSocket connection
 */
function handleFrameBuffer(session, payload, ws) {
  const { frames, fps, timestamp } = payload;
  
  console.log(`[Shooting] handleFrameBuffer called, frames count: ${frames?.length || 0}`);
  
  if (!frames || !Array.isArray(frames)) {
    ws.send(JSON.stringify({
      type: 'error',
      code: 'INVALID_FRAME_BUFFER',
      message: '无效的帧缓冲区格式',
      recoverable: true,
      timestamp: Date.now()
    }));
    return;
  }

  session.totalFramesReceived += frames.length;
  console.log(`[Shooting] Total frames received: ${session.totalFramesReceived}`);

  // Notify consoles about frames received
  session.notifyConsoles({
    type: 'frames_received',
    count: frames.length,
    total: session.totalFramesReceived,
    timestamp: Date.now()
  });

  // Forward to Python backend for analysis if callback is set
  if (session.analysisCallback) {
    session.analysisCallback({
      session_id: session.sessionId,
      frames: frames,
      fps: fps || 30,
      timestamp: timestamp || Date.now()
    });
  } else {
    // Mock advice generation for testing (when Python backend is not connected)
    generateMockAdvice(session);
    
    // 发送模拟遥测数据（用于 HUD 显示）
    sendMockTelemetry(session);
    
    // 发送模拟任务数据（如果还没有任务）
    if (!session.currentTask) {
      sendMockTask(session);
    }
  }

  // Send acknowledgment
  ws.send(JSON.stringify({
    type: 'frame_ack',
    frame_count: frames.length,
    timestamp: Date.now()
  }));
}

// Mock advice templates for testing
const MOCK_ADVICE_TEMPLATES = [
  {
    priority: 'positive',
    category: 'stability',
    message: '稳如泰山！保持当前状态。',
    trigger_haptic: false,
  },
  {
    priority: 'warning',
    category: 'stability',
    message: '手持略有不稳，请夹紧双肘，屏住呼吸。',
    trigger_haptic: false,
  },
  {
    priority: 'info',
    category: 'composition',
    message: '正在进行向右横移，请坚持到底，不要中途上下晃动。',
    trigger_haptic: false,
  },
  {
    priority: 'positive',
    category: 'speed',
    message: '运镜速度完美！',
    trigger_haptic: false,
  },
  {
    priority: 'warning',
    category: 'speed',
    message: '移速太快了！请慢一点，给观众留出观察细节的时间。',
    trigger_haptic: false,
  },
];

let mockAdviceIndex = 0;
let lastMockAdviceTime = 0;

/**
 * Send mock telemetry data for HUD display
 * @param {ShootingSession} session - Session instance
 */
function sendMockTelemetry(session) {
  // 模拟运动数据
  const mockTelemetry = {
    type: 'telemetry',
    avg_speed_px_frame: 5.0 + Math.random() * 2, // 3-7 px/frame
    speed_variance: 1.0 + Math.random() * 2, // 1-3
    motion_smoothness: 0.6 + Math.random() * 0.3, // 0.6-0.9
    primary_direction_deg: Math.random() * 360, // 0-360
    subject_occupancy: 0.2 + Math.random() * 0.3, // 0.2-0.5
    confidence: 0.7 + Math.random() * 0.2, // 0.7-0.9
    timestamp: Date.now()
  };

  // Broadcast to all mobile clients
  session.clients.forEach(client => {
    if (client.readyState === 1) { // OPEN
      client.send(JSON.stringify(mockTelemetry));
    }
  });
}

// 任务模板库 - 根据环境推荐不同的任务
const TASK_TEMPLATES = [
  {
    task_id: 'truck_right',
    task_name: '缓慢右移',
    description: '跟随引导，向右平移',
    target_motion: 'truck_right',
    icon: '>>>',
    condition: 'spacious',
    shooting_goal: '展示空间层次关系',
    what_to_capture: '捕捉环境中的纵深感和不同层次的物体',
    reasons: {
      spacious: '环境宽敞，适合横向移动展示空间关系',
      bright: '光线充足，平移可以展现更多细节',
      default: '基础横移运镜，适合大多数场景',
    }
  },
  {
    task_id: 'truck_left',
    task_name: '缓慢左移',
    description: '跟随引导，向左平移',
    target_motion: 'truck_left',
    icon: '<<<',
    condition: 'spacious',
    shooting_goal: '揭示画面左侧的隐藏区域',
    what_to_capture: '捕捉镜头左侧的环境细节和空间延伸',
    reasons: {
      spacious: '环境宽敞，向左移动可以揭示隐藏区域',
      default: '反向横移，提供不同视角',
    }
  },
  {
    task_id: 'dolly_in',
    task_name: '缓慢推进',
    description: '保持稳定，缓慢向前推进',
    target_motion: 'dolly_in',
    icon: '↓↓↓',
    condition: 'clear_subject',
    shooting_goal: '强调画面主体的重要性',
    what_to_capture: '聚焦拍摄主体的细节特写，突出视觉焦点',
    reasons: {
      clear_subject: '检测到明确主体，推进可以强调重点',
      bright: '光线良好，推进可以捕捉更多细节',
      default: '推进运镜，聚焦主体',
    }
  },
  {
    task_id: 'dolly_out',
    task_name: '缓慢拉远',
    description: '保持稳定，缓慢向后拉远',
    target_motion: 'dolly_out',
    icon: '↑↑↑',
    condition: 'clear_subject',
    shooting_goal: '展示主体与环境的关系',
    what_to_capture: '从特写拉远到全景，展现主体在环境中的位置',
    reasons: {
      clear_subject: '主体明确，拉远可以展示环境关系',
      default: '拉远运镜，展现全景',
    }
  },
  {
    task_id: 'anchor_hold',
    task_name: '稳定锚点',
    description: '保持静止，稳定画面',
    target_motion: 'static',
    icon: '⊙',
    condition: 'crowded',
    shooting_goal: '建立稳定的画面锚点',
    what_to_capture: '静止捕捉当前画面作为叙事基准点',
    reasons: {
      crowded: '环境复杂，先稳定画面建立锚点',
      dark: '光线不足，静止拍摄减少模糊',
      unstable: '检测到运动不稳定，建议先静止',
      default: '稳定锚点，建立基准画面',
    }
  },
  {
    task_id: 'pan_right',
    task_name: '向右摇移',
    description: '水平旋转，向右扫描',
    target_motion: 'pan_right',
    icon: '⟳',
    condition: 'panorama',
    shooting_goal: '全景展示环境概览',
    what_to_capture: '扫描拍摄整个环境，建立空间印象',
    reasons: {
      panorama: '适合全景扫描，展现宽广视野',
      default: '旋转运镜，展现环境全貌',
    }
  },
];

/**
 * 分析环境（基于简单规则，模拟 AI 判断）
 * @param {ShootingSession} session - Session instance
 * @returns {Object} Environment analysis
 */
function analyzeEnvironment(session) {
  const frameCount = session.totalFramesReceived;
  const time = Date.now();
  
  // 模拟不同的环境状态
  const hour = new Date().getHours();
  const isDay = hour >= 6 && hour < 18;
  
  let environment = {
    brightness: isDay ? 'bright' : 'dark',
    complexity: frameCount < 20 ? 'simple' : (frameCount % 50 < 25 ? 'simple' : 'complex'),
    motion: session.currentTask ? 'active' : 'static',
    subject: frameCount % 30 < 15 ? 'clear' : 'unclear',
  };
  
  // 生成环境分析
  let tags = [];
  let constraints = [];
  let analysis = '';
  let shootability = 0.7;
  
  if (environment.brightness === 'bright') {
    tags.push('明亮');
    analysis = '环境光线充足';
    shootability += 0.2;
  } else {
    tags.push('暗光');
    constraints.push('光线不足');
    analysis = '环境光线较暗';
    shootability -= 0.1;
  }
  
  if (environment.complexity === 'simple') {
    tags.push('简洁');
    analysis += '，画面简洁清晰';
    shootability += 0.1;
  } else {
    tags.push('复杂');
    constraints.push('画面元素较多');
    analysis += '，画面元素丰富';
  }
  
  if (environment.subject === 'clear') {
    tags.push('主体明确');
    analysis += '，主体突出';
    shootability += 0.1;
  } else {
    tags.push('主体模糊');
    constraints.push('主体不够突出');
    analysis += '，需要明确主体';
  }
  
  return {
    environment,
    tags,
    constraints,
    analysis,
    shootability: Math.min(0.95, Math.max(0.3, shootability)),
    condition: environment.brightness === 'bright' && environment.subject === 'clear' ? 'clear_subject' :
               environment.complexity === 'simple' ? 'spacious' : 'crowded',
  };
}

/**
 * 智能选择任务（基于环境分析）
 * @param {ShootingSession} session - Session instance
 * @returns {Object} Selected task template and reasoning
 */
function selectSmartTask(session) {
  // 分析环境
  const envAnalysis = analyzeEnvironment(session);
  
  // 发送环境分析给客户端
  const envPayload = {
    type: 'environment',
    environment_tags: envAnalysis.tags,
    shootability_score: envAnalysis.shootability,
    constraints: envAnalysis.constraints,
    recommended_risk_level: 'low',
    theme_candidates: ['空间展示', '主体特写', '运动捕捉'],
    confidence: 0.8,
    timestamp: Date.now(),
    analysis: envAnalysis.analysis,
  };
  
  session.clients.forEach(client => {
    if (client.readyState === 1) {
      client.send(JSON.stringify(envPayload));
    }
  });
  
  // 发送 AI 思考过程
  const thinkingPayload = {
    type: 'ai_thinking',
    stage: 'deciding',
    thought: `基于环境分析，我正在为你匹配最合适的拍摄任务和内容...`,
    evidence: [
      `环境可拍性: ${(envAnalysis.shootability * 100).toFixed(0)}%`,
      `环境特征: ${envAnalysis.tags.join(', ')}`,
      `推荐场景类型: ${envAnalysis.condition === 'clear_subject' ? '主体特写' : 
                       envAnalysis.condition === 'spacious' ? '空间展示' : '稳定建立'}`,
    ],
    timestamp: Date.now(),
  };
  
  session.clients.forEach(client => {
    if (client.readyState === 1) {
      client.send(JSON.stringify(thinkingPayload));
    }
  });
  
  // 根据环境选择任务
  const frameCount = session.totalFramesReceived;
  let selectedTask;
  let reason;
  
  if (frameCount < 10) {
    // 开始时：先稳定
    selectedTask = TASK_TEMPLATES.find(t => t.task_id === 'anchor_hold');
    reason = selectedTask.reasons.default;
  } else if (envAnalysis.constraints.length > 1) {
    // 环境复杂：静止
    selectedTask = TASK_TEMPLATES.find(t => t.task_id === 'anchor_hold');
    reason = selectedTask.reasons.crowded || selectedTask.reasons.default;
  } else {
    // 根据环境条件选择任务
    const suitableTasks = TASK_TEMPLATES.filter(t => 
      t.condition === envAnalysis.condition || t.condition === 'spacious'
    );
    selectedTask = suitableTasks[Math.floor(Math.random() * suitableTasks.length)];
    reason = selectedTask.reasons[envAnalysis.condition] || 
             selectedTask.reasons[envAnalysis.environment.brightness] ||
             selectedTask.reasons.default;
  }
  
  return {
    task: selectedTask,
    reason: reason,
    environment: envAnalysis,
  };
}

/**
 * Send mock task data for HUD display
 * @param {ShootingSession} session - Session instance
 */
function sendMockTask(session) {
  // 智能选择任务（包含环境分析和推理）
  const selection = selectSmartTask(session);
  const taskTemplate = selection.task;
  
  // 创建任务
  const mockTask = {
    type: 'task',
    task_id: taskTemplate.task_id,
    task_name: taskTemplate.task_name,
    description: taskTemplate.description,
    target_duration_s: 4.0,
    risk_level: 'low',
    success_criteria: '匀速移动，节奏平稳',
    target_motion: taskTemplate.target_motion,
    target_speed_range: [3, 8],
    state: 'executing',
    progress: 0.0,
    timestamp: Date.now(),
    icon: taskTemplate.icon,
    reason: selection.reason, // AI 推荐理由
    shooting_goal: taskTemplate.shooting_goal, // 拍摄目标
    what_to_capture: taskTemplate.what_to_capture, // 要拍什么
  };

  session.currentTask = mockTask;

  console.log(`[AI Analysis] Environment: ${selection.environment.tags.join(', ')} | Score: ${(selection.environment.shootability * 100).toFixed(0)}%`);
  console.log(`[AI Decision] Selected: ${mockTask.task_name} | Reason: ${selection.reason}`);

  // Broadcast to all mobile clients
  session.clients.forEach(client => {
    if (client.readyState === 1) { // OPEN
      client.send(JSON.stringify(mockTask));
    }
  });
}

/**
 * Generate mock advice for testing
 * @param {ShootingSession} session - Session instance
 */
function generateMockAdvice(session) {
  const now = Date.now();
  // Only generate advice every 3 seconds
  if (now - lastMockAdviceTime < 3000) {
    return;
  }
  lastMockAdviceTime = now;
  
  const advice = MOCK_ADVICE_TEMPLATES[mockAdviceIndex % MOCK_ADVICE_TEMPLATES.length];
  mockAdviceIndex++;
  
  session.broadcastAdvice({
    ...advice,
    suppress_duration_ms: 3000,
  });
}

/**
 * Handle WebSocket message for shooting session
 * @param {ShootingSession} session - Session instance
 * @param {string} message - Raw message string
 * @param {WebSocket} ws - WebSocket connection
 */
function handleShootingMessage(session, message, ws) {
  try {
    const payload = JSON.parse(message);
    
    switch (payload.type) {
      case 'frames':
        handleFrameBuffer(session, payload, ws);
        break;
      
      case 'heartbeat':
        // Client heartbeat - respond with server heartbeat
        ws.send(JSON.stringify({
          type: 'heartbeat_ack',
          timestamp: Date.now()
        }));
        break;
      
      case 'status':
        // Client requesting session status
        ws.send(JSON.stringify({
          type: 'status',
          ...session.getStats()
        }));
        break;
      
      default:
        console.log(`[Shooting] Unknown message type: ${payload.type}`);
    }
  } catch (error) {
    console.error(`[Shooting] Error parsing message:`, error);
    ws.send(JSON.stringify({
      type: 'error',
      code: 'PARSE_ERROR',
      message: '消息解析失败',
      recoverable: true,
      timestamp: Date.now()
    }));
  }
}

/**
 * Setup shooting session routes on Express app
 * @param {Express} app - Express application
 */
function setupShootingRoutes(app) {
  // Create shooting session
  app.post('/shooting/session', (req, res) => {
    const sessionId = Math.random().toString(36).substring(2, 8).toUpperCase();
    
    let clientOrigin = req.headers.origin || 'http://localhost:3000';
    
    // Convert to HTTPS for camera access
    if (clientOrigin.startsWith('http://') && clientOrigin.includes(':3000')) {
      clientOrigin = clientOrigin.replace('http://', 'https://');
    }
    
    // Handle localhost replacement for mobile access
    if (clientOrigin.includes('localhost') || clientOrigin.includes('127.0.0.1')) {
      const hostHeader = req.headers.host;
      if (hostHeader && !hostHeader.includes('localhost')) {
        const hostname = hostHeader.split(':')[0];
        clientOrigin = clientOrigin.replace(/localhost|127\.0\.0\.1/g, hostname);
      }
    }
    
    const joinUrl = `${clientOrigin}/#/shooting-mobile/${sessionId}`;
    
    createShootingSession(sessionId);
    
    console.log(`[Shooting] Created session ${sessionId}`);
    console.log(`[Shooting] Join URL: ${joinUrl}`);
    
    res.json({
      session_id: sessionId,
      join_url: joinUrl,
      ws_url: `/shooting/${sessionId}/stream`
    });
  });

  // Get shooting session info
  app.get('/shooting/session/:id', (req, res) => {
    const session = getShootingSession(req.params.id);
    if (!session) {
      return res.status(404).json({
        error: 'Session not found',
        code: 'SESSION_NOT_FOUND'
      });
    }
    res.json(session.getStats());
  });

  // Delete shooting session
  app.delete('/shooting/session/:id', (req, res) => {
    const session = getShootingSession(req.params.id);
    if (!session) {
      return res.status(404).json({
        error: 'Session not found',
        code: 'SESSION_NOT_FOUND'
      });
    }
    deleteShootingSession(req.params.id);
    res.status(204).send();
  });

  // Push advice to session (called by Python backend)
  app.post('/shooting/session/:id/advice', (req, res) => {
    const session = getShootingSession(req.params.id);
    if (!session) {
      return res.status(404).json({
        error: 'Session not found',
        code: 'SESSION_NOT_FOUND'
      });
    }
    
    const advice = req.body;
    session.broadcastAdvice(advice);
    
    res.json({
      success: true,
      clients_notified: session.clients.size
    });
  });
}

/**
 * Setup WebSocket handler for shooting sessions
 * @param {WebSocketServer} wss - WebSocket server
 */
function setupShootingWebSocket(wss) {
  wss.on('connection', (ws, req) => {
    console.log(`[Shooting WS] Connection received, URL: ${req.url}`);
    
    // Parse URL: /shooting/:id/stream or /shooting/:id/console
    const urlParts = req.url.split('/');
    
    // Check if this is a shooting session connection
    if (urlParts[1] !== 'shooting') {
      console.log(`[Shooting WS] Not a shooting URL, ignoring`);
      return; // Let other handlers deal with it
    }
    
    const sessionId = urlParts[2];
    const endpoint = urlParts[3]; // 'stream' or 'console'
    
    console.log(`[Shooting WS] Session: ${sessionId}, Endpoint: ${endpoint}`);
    
    if (!sessionId) {
      ws.close(4000, 'Session ID required');
      return;
    }
    
    // Get or create session
    const session = getOrCreateShootingSession(sessionId);
    
    if (endpoint === 'console') {
      // Console connection (for monitoring)
      console.log(`[Shooting WS] Console connecting to session ${sessionId}`);
      session.addConsole(ws);
      
      // Send welcome message with current stats
      ws.send(JSON.stringify({
        type: 'connected',
        role: 'console',
        session_id: sessionId,
        stats: session.getStats(),
        timestamp: Date.now()
      }));
      
      // Handle close
      ws.on('close', () => {
        session.removeConsole(ws);
      });
      
      // Handle errors
      ws.on('error', (error) => {
        console.error(`[Shooting WS] Console error in session ${sessionId}:`, error);
        session.removeConsole(ws);
      });
    } else {
      // Mobile client connection (stream)
      console.log(`[Shooting WS] Mobile client connecting to session ${sessionId}`);
      session.addClient(ws);
      
      // Send welcome message
      ws.send(JSON.stringify({
        type: 'connected',
        role: 'mobile',
        session_id: sessionId,
        timestamp: Date.now()
      }));
      
      // Handle messages
      ws.on('message', (message) => {
        handleShootingMessage(session, message.toString(), ws);
      });
      
      // Handle close
      ws.on('close', () => {
        session.removeClient(ws);
        
        // Clean up empty sessions after a delay
        if (!session.hasClients()) {
          setTimeout(() => {
            if (!session.hasClients()) {
              deleteShootingSession(sessionId);
            }
          }, 60000); // 1 minute cleanup delay
        }
      });
      
      // Handle errors
      ws.on('error', (error) => {
        console.error(`[Shooting WS] Mobile error in session ${sessionId}:`, error);
        session.removeClient(ws);
      });
    }
  });
}

module.exports = {
  SHOOTING_SESSIONS,
  ShootingSession,
  createShootingSession,
  getOrCreateShootingSession,
  getShootingSession,
  deleteShootingSession,
  handleFrameBuffer,
  handleShootingMessage,
  setupShootingRoutes,
  setupShootingWebSocket
};
