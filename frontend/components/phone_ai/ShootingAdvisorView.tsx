/**
 * ShootingAdvisorView Component
 * 
 * Main view for realtime shooting advisor mode.
 * Integrates camera capture with advice display and haptic feedback.
 * 
 * Requirements: 7.2, 10.1-10.6
 */
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { CameraCapture, CameraCaptureRef, FrameBuffer } from './CameraCapture';
import { AdviceDisplay, AdvicePayload } from './AdviceDisplay';

interface ShootingAdvisorViewProps {
  sessionId: string;
}

// WebSocket message types
interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

// Telemetry data interface
interface TelemetryData {
  avg_speed_px_frame: number;
  speed_variance: number;
  motion_smoothness: number;
  primary_direction_deg: number;
  subject_occupancy: number;
  confidence: number;
  timestamp: number;
}

// Task data interface
interface TaskData {
  task_id: string;
  task_name: string;
  description: string;
  target_duration_s: number;
  risk_level: string;
  success_criteria: string;
  target_motion?: string;
  target_speed_range?: [number, number];
  state: string;
  progress: number;
  timestamp: number;
}

// Environment analysis interface
interface EnvironmentData {
  environment_tags: string[];
  shootability_score: number;
  constraints: string[];
  recommended_risk_level: string;
  theme_candidates: string[];
  confidence: number;
  timestamp: number;
  analysis?: string;
}

// AI Thinking data interface
interface AIThinkingData {
  stage: string;
  thought: string;
  evidence: string[];
  timestamp: number;
}

// HUD Components
interface HUDOverlayProps {
  telemetry: TelemetryData | null;
  currentTask: TaskData | null;
  currentAdvice: AdvicePayload | null;
}

const CoachCapsule: React.FC<{
  task: TaskData | null;
  advice: AdvicePayload | null;
  isRecording: boolean;
}> = ({ task, advice, isRecording }) => {
  // 始终显示，即使没有数据也显示默认提示
  const getMessage = () => {
    if (advice && advice.priority === 'critical') {
      return advice.message;
    }
    if (task) {
      switch (task.state) {
        case 'executing':
          return task.description || '跟随引导，向右平移';
        case 'recovery':
          return '稳住！太快了！';
        case 'done':
          return '🎉 任务完成！';
        case 'task_picked':
          return task.description || '准备开始拍摄';
        default:
          return task.description || '跟随引导，向右平移';
      }
    }
    if (advice) {
      return advice.message;
    }
    // 默认消息
    if (isRecording) {
      return '保持稳定，跟随引导';
    }
    return '准备开始拍摄';
  };

  const getCapsuleColor = () => {
    if (advice?.priority === 'critical') return 'bg-red-600/90 animate-pulse';
    if (task?.state === 'recovery') return 'bg-orange-500/90 animate-pulse';
    if (task?.state === 'done') return 'bg-green-500/90';
    return 'bg-black/70';
  };

  return (
    <div className="fixed top-5 left-1/2 transform -translate-x-1/2 z-[100] pointer-events-none">
      <div className={`px-4 py-2 rounded-full backdrop-blur-md text-white text-sm font-medium border border-white/20 shadow-lg ${getCapsuleColor()}`}>
        {getMessage()}
      </div>
    </div>
  );
};

const DirectionChevrons: React.FC<{
  task: TaskData | null;
  telemetry: TelemetryData | null;
  isRecording: boolean;
}> = ({ task, telemetry, isRecording }) => {
  // 始终显示方向指示，即使没有任务也显示默认（向右）
  const getChevronDirection = () => {
    let expectedDirection = 0; // 默认向右
    let direction = 'truck_right'; // 默认向右平移

    if (task && task.target_motion) {
      direction = task.target_motion;
      switch (task.target_motion) {
        case 'truck_right':
          expectedDirection = 0;
          break;
        case 'truck_left':
          expectedDirection = 180;
          break;
        case 'pan_right':
          expectedDirection = 90;
          break;
        case 'pan_left':
          expectedDirection = 270;
          break;
        case 'dolly_in':
          expectedDirection = 0; // 向前
          break;
        case 'dolly_out':
          expectedDirection = 180; // 向后
          break;
        default:
          expectedDirection = 0;
      }
    }

    let isCorrect = true;
    if (telemetry && task && task.state === 'executing') {
      const currentDirection = telemetry.primary_direction_deg;
      const angleDiff = Math.abs(currentDirection - expectedDirection);
      isCorrect = angleDiff < 45; // Within 45 degrees
    }

    return {
      direction,
      isCorrect,
      expectedDirection
    };
  };

  const chevronInfo = getChevronDirection();

  const getChevronSymbol = (direction: string) => {
    switch (direction) {
      case 'truck_right':
      case 'pan_right':
        return '>';
      case 'truck_left':
      case 'pan_left':
        return '<';
      case 'dolly_in':
        return '↓';
      case 'dolly_out':
        return '↑';
      default:
        return '>';
    }
  };

  // 只在录制时显示
  if (!isRecording && !task) return null;

  const chevronClass = chevronInfo.isCorrect
    ? 'text-white animate-pulse'
    : 'text-red-400 animate-bounce';

  return (
    <div className="fixed top-1/2 right-4 transform -translate-y-1/2 z-[100] pointer-events-none">
      <div className={`text-5xl font-bold drop-shadow-lg ${chevronClass}`}>
        {getChevronSymbol(chevronInfo.direction).repeat(3)}
      </div>
    </div>
  );
};

const BalanceMeter: React.FC<{
  telemetry: TelemetryData | null;
  task: TaskData | null;
  isRecording: boolean;
}> = ({ telemetry, task, isRecording }) => {
  // 始终显示水平仪，使用默认值或实际数据
  let balanceScore = 0.5; // 默认中间位置
  let smoothnessScore = 0.5;
  let speedVarianceScore = 0.5;

  if (telemetry) {
    smoothnessScore = telemetry.motion_smoothness || 0.5;
    speedVarianceScore = Math.max(0, 1 - (telemetry.speed_variance || 0) / 10);
    balanceScore = (smoothnessScore + speedVarianceScore) / 2;
  }

  // Convert to position on the meter (-50 to +50)
  const position = (balanceScore - 0.5) * 100;

  const getMeterColor = () => {
    if (balanceScore > 0.8) return 'bg-green-400';
    if (balanceScore > 0.6) return 'bg-yellow-400';
    return 'bg-red-400';
  };

  // 只在录制时显示
  if (!isRecording && !task) return null;

  return (
    <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-[100] pointer-events-none">
      <div className="bg-black/70 backdrop-blur-md rounded-full px-8 py-3 border border-white/30 shadow-lg">
        <div className="flex items-center space-x-3">
          {/* 水平仪滑块 */}
          <div className="w-40 h-1.5 bg-gray-700 rounded-full relative overflow-hidden">
            {/* 中心绿色安全区 */}
            <div className="absolute left-[45%] right-[45%] top-0 bottom-0 bg-green-500/30" />
            {/* 滑块指示器 */}
            <div
              className={`h-full w-1 rounded-full transition-all duration-200 ${getMeterColor()}`}
              style={{
                position: 'absolute',
                left: `${50 + position * 0.4}%`, // 限制在槽内移动
                top: '50%',
                transform: 'translate(-50%, -50%)',
                boxShadow: balanceScore < 0.6 ? '0 0 8px rgba(239, 68, 68, 0.8)' : 'none',
              }}
            />
            {/* 中心刻度线 */}
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/60 transform -translate-x-1/2" />
          </div>
        </div>
      </div>
    </div>
  );
};

const HUDOverlay: React.FC<HUDOverlayProps & { isRecording: boolean }> = ({
  telemetry,
  currentTask,
  currentAdvice,
  isRecording
}) => {
  return (
    <>
      <CoachCapsule task={currentTask} advice={currentAdvice} isRecording={isRecording} />
      <DirectionChevrons task={currentTask} telemetry={telemetry} isRecording={isRecording} />
      <BalanceMeter telemetry={telemetry} task={currentTask} isRecording={isRecording} />
    </>
  );
};

// Telemetry data interface
interface TelemetryData {
  avg_speed_px_frame: number;
  speed_variance: number;
  motion_smoothness: number;
  primary_direction_deg: number;
  subject_occupancy: number;
  confidence: number;
  timestamp: number;
}

// Task data interface
interface TaskData {
  task_id: string;
  task_name: string;
  description: string;
  target_duration_s: number;
  risk_level: string;
  success_criteria: string;
  target_motion?: string;
  target_speed_range?: [number, number];
  state: string;
  progress: number;
  timestamp: number;
}

// Environment analysis interface
interface EnvironmentData {
  environment_tags: string[];
  shootability_score: number;
  constraints: string[];
  recommended_risk_level: string;
  theme_candidates: string[];
  confidence: number;
  timestamp: number;
}

// Connection states
type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

// Get WebSocket URL based on current environment
function getWsUrl(sessionId: string): string {
  const hostname = window.location.hostname;
  // Phone AI 后端端口（默认 8001，可通过环境变量配置）
  // @ts-ignore - VITE环境变量在构建时注入
  const phoneAiPort = import.meta.env.VITE_PHONE_AI_PORT || '8001';
  
  // 如果前端是 HTTPS，后端也应该支持 WSS（如果配置了 SSL）
  // 否则使用 WS（可能被浏览器阻止混合内容）
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  const wsUrl = `${protocol}//${hostname}:${phoneAiPort}/api/realtime/session/${sessionId}/ws`;
  console.log('[ShootingAdvisor] WebSocket URL:', wsUrl, {
    frontendProtocol: window.location.protocol,
    backendProtocol: protocol,
    hostname,
    port: phoneAiPort,
    note: protocol === 'wss:' ? '需要后端支持 WSS' : '使用 WS（可能被浏览器阻止）'
  });
  
  return wsUrl;
}

export const ShootingAdvisorView: React.FC<ShootingAdvisorViewProps> = ({ sessionId }) => {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
  const [currentAdvice, setCurrentAdvice] = useState<AdvicePayload | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [stats, setStats] = useState({ framesProcessed: 0, adviceReceived: 0, framesCaptured: 0 });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string>('');

  // New state for HUD data
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [currentTask, setCurrentTask] = useState<TaskData | null>(null);
  const [environment, setEnvironment] = useState<EnvironmentData | null>(null);
  const [framePaths, setFramePaths] = useState<string[]>([]);
  const [aiThinking, setAiThinking] = useState<AIThinkingData | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const cameraCaptureRef = useRef<CameraCaptureRef>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Trigger haptic feedback for critical advice (Requirement 7.2)
  const triggerHaptic = useCallback(() => {
    if ('vibrate' in navigator) {
      // Strong vibration pattern for critical advice
      navigator.vibrate([100, 50, 100, 50, 200]);
    }
  }, []);

  // Handle incoming advice
  const handleAdvice = useCallback((advice: AdvicePayload) => {
    setCurrentAdvice(advice);
    setStats(prev => ({ ...prev, adviceReceived: prev.adviceReceived + 1 }));
    
    // Trigger haptic for critical advice (Requirement 7.2)
    if (advice.trigger_haptic || advice.priority === 'critical') {
      triggerHaptic();
    }
  }, [triggerHaptic]);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionState('connecting');
    const wsUrl = getWsUrl(sessionId);
    console.log(`[ShootingAdvisor] 🔌 Connecting to ${wsUrl}`);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[ShootingAdvisor] ✅ WebSocket connected');
      setConnectionState('connected');
      reconnectAttemptsRef.current = 0;
      
      // 立即请求初始任务
      console.log('[ShootingAdvisor] 📤 Requesting initial task');
      ws.send(JSON.stringify({
        type: 'request_task',
        timestamp: Date.now()
      }));
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        
        switch (message.type) {
          case 'connected':
            console.log('[ShootingAdvisor] Session confirmed:', message.session_id);
            break;
          
          case 'advice':
            handleAdvice(message as unknown as AdvicePayload);
            break;

          case 'telemetry':
            setTelemetry(message as unknown as TelemetryData);
            break;

          case 'task':
            console.log('[ShootingAdvisor] Received task:', message);
            setCurrentTask(message as unknown as TaskData);
            break;

          case 'environment':
            console.log('[ShootingAdvisor] 🤖 Received environment:', message);
            setEnvironment(message as unknown as EnvironmentData);
            break;

          case 'ai_thinking':
            console.log('[ShootingAdvisor] 💭 AI thinking:', message);
            setAiThinking(message as unknown as AIThinkingData);
            break;

          case 'frame_ack':
            setStats(prev => ({
              ...prev,
              framesProcessed: prev.framesProcessed + (message.frame_count || 0)
            }));
            break;

          case 'heartbeat':
          case 'heartbeat_ack':
            // Heartbeat received, connection is alive
            break;

          case 'error':
            console.error('[ShootingAdvisor] Server error:', message);
            break;

          default:
            console.log('[ShootingAdvisor] Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('[ShootingAdvisor] Error parsing message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('[ShootingAdvisor] ❌ WebSocket error:', error);
      console.error('[ShootingAdvisor] WebSocket 状态:', {
        readyState: ws.readyState,
        url: wsUrl,
        protocol: window.location.protocol
      });
      
      // 如果是混合内容错误，提示用户
      if (window.location.protocol === 'https:' && wsUrl.startsWith('ws://')) {
        console.error('[ShootingAdvisor] ⚠️  混合内容错误：HTTPS 页面无法连接 HTTP WebSocket');
        console.error('[ShootingAdvisor] 💡 解决方案：需要配置后端支持 WSS');
      }
      
      setConnectionState('error');
    };

    ws.onclose = () => {
      console.log('[ShootingAdvisor] WebSocket closed');
      setConnectionState('disconnected');
      
      // Attempt reconnection with exponential backoff (Requirement 9.4)
      const maxAttempts = 5;
      if (reconnectAttemptsRef.current < maxAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        console.log(`[ShootingAdvisor] Reconnecting in ${delay}ms...`);
        
        reconnectTimeoutRef.current = window.setTimeout(() => {
          reconnectAttemptsRef.current++;
          connectWebSocket();
        }, delay);
      }
    };
  }, [sessionId, handleAdvice]);

  // Send frame buffer to server
  const sendFrameBuffer = useCallback((buffer: FrameBuffer) => {
    console.log('[ShootingAdvisor] sendFrameBuffer called, ws state:', wsRef.current?.readyState);
    
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.log('[ShootingAdvisor] WebSocket not open, cannot send frames');
      return;
    }

    const payload = {
      type: 'frames',
      session_id: sessionId,
      frames: buffer.frames,
      fps: buffer.fps,
      timestamp: buffer.timestamp,
    };

    console.log('[ShootingAdvisor] Sending', buffer.frames.length, 'frames to server');
    wsRef.current.send(JSON.stringify(payload));
  }, [sessionId]);

  // Handle frame buffer from camera
  const handleFrameBuffer = useCallback((buffer: FrameBuffer) => {
    console.log('[ShootingAdvisor] Received frame buffer with', buffer.frames.length, 'frames');
    setStats(prev => ({ ...prev, framesCaptured: prev.framesCaptured + buffer.frames.length }));
    setDebugInfo(`收到 ${buffer.frames.length} 帧, 时间: ${new Date().toLocaleTimeString()}`);

    // Store frame paths for environment scanning
    // In a real implementation, we'd save these frames to temporary files
    // For now, we'll simulate with dummy paths
    const newFramePaths = buffer.frames.map((_, index) =>
      `/tmp/frame_${Date.now()}_${index}.jpg`
    );
    setFramePaths(prev => [...prev, ...newFramePaths].slice(-10)); // Keep last 10

    sendFrameBuffer(buffer);
  }, [sendFrameBuffer]);

  // Trigger environment scan when we have enough frames
  useEffect(() => {
    if (framePaths.length >= 5 && !environment && wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[ShootingAdvisor] Triggering environment scan with', framePaths.length, 'frames');

      const scanMessage = {
        type: 'start_environment_scan',
        frame_paths: framePaths.slice(-5), // Use last 5 frames
        timestamps_ms: framePaths.slice(-5).map((_, index) => Date.now() - (4 - index) * 200)
      };

      wsRef.current.send(JSON.stringify(scanMessage));
    }
  }, [framePaths, environment]);

  // 模拟数据用于测试（当没有真实数据时）
  useEffect(() => {
    if (isRecording && !currentTask && !telemetry) {
      // 创建默认任务用于显示
      const defaultTask: TaskData = {
        task_id: 'default_truck_right',
        task_name: '缓慢右移',
        description: '跟随引导，向右平移',
        target_duration_s: 4.0,
        risk_level: 'low',
        success_criteria: '匀速移动，节奏平稳',
        target_motion: 'truck_right',
        target_speed_range: [3, 8],
        state: 'executing',
        progress: 0.0,
        timestamp: Date.now(),
      };
      setCurrentTask(defaultTask);

      // 创建模拟遥测数据
      const mockTelemetry: TelemetryData = {
        avg_speed_px_frame: 5.0,
        speed_variance: 2.0,
        motion_smoothness: 0.7,
        primary_direction_deg: 0,
        subject_occupancy: 0.3,
        confidence: 0.8,
        timestamp: Date.now(),
      };
      setTelemetry(mockTelemetry);
    }
  }, [isRecording, currentTask, telemetry]);

  // Start/stop recording
  const toggleRecording = useCallback(async () => {
    console.group('🎬 [ShootingAdvisor] toggleRecording');
    console.log('[TOGGLE] 当前状态:', {
      isRecording,
      cameraReady,
      hasRef: !!cameraCaptureRef.current,
      connectionState
    });
    setDebugInfo(`toggle: rec=${isRecording}, cam=${cameraReady}`);
    
    if (isRecording) {
      console.log('[TOGGLE] 停止录制...');
      cameraCaptureRef.current?.stopCapture();
      setIsRecording(false);
      setDebugInfo('已停止录制');
      console.log('[TOGGLE] ✅ 录制已停止');
    } else {
      console.log('[TOGGLE] 开始录制...');
      console.log('[TOGGLE] 检查 cameraCaptureRef:', {
        exists: !!cameraCaptureRef.current,
        isCapturing: cameraCaptureRef.current?.isCapturing,
        hasStream: !!cameraCaptureRef.current?.getStream()
      });
      setDebugInfo('正在启动摄像头...');
      
      if (cameraCaptureRef.current) {
        console.log('[TOGGLE] 调用 startCapture()...');
        try {
          await cameraCaptureRef.current.startCapture();
          console.log('[TOGGLE] ✅ startCapture() 完成');
          setIsRecording(true);
          setCameraReady(true);
          setDebugInfo('录制已开始');
          console.log('[TOGGLE] ✅ 录制状态已更新');
        } catch (error: any) {
          console.error('[TOGGLE] ❌ startCapture() 失败:', error);
          setDebugInfo(`错误: ${error.message || '启动失败'}`);
        }
      } else {
        console.error('[TOGGLE] ❌ cameraCaptureRef 为空！');
        setDebugInfo('错误: cameraCaptureRef 为空');
      }
    }
    console.groupEnd();
  }, [isRecording, cameraReady, connectionState]);

  // Initialize WebSocket connection
  useEffect(() => {
    console.log('[ShootingAdvisor] 🚀 组件挂载，sessionId:', sessionId);
    console.log('[ShootingAdvisor] 初始化 WebSocket 连接...');
    connectWebSocket();

    return () => {
      console.log('[ShootingAdvisor] 🛑 组件卸载，清理资源');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket, sessionId]);
  
  // Debug: Log camera ref changes
  useEffect(() => {
    console.log('[ShootingAdvisor] 📹 CameraCapture ref 状态:', {
      hasRef: !!cameraCaptureRef.current,
      isCapturing: cameraCaptureRef.current?.isCapturing,
      hasStream: !!cameraCaptureRef.current?.getStream()
    });
  }, [cameraReady, isRecording]);

  // Render loading state
  if (connectionState === 'connecting') {
    return (
      <div className="h-screen w-screen bg-black flex flex-col items-center justify-center text-white">
        <div className="w-12 h-12 border-4 border-t-cyan-500 border-r-transparent border-b-cyan-500 border-l-transparent rounded-full animate-spin mb-4" />
        <p className="font-mono text-sm tracking-widest">连接中... {sessionId}</p>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-black overflow-hidden relative">
      {/* Camera layer */}
      <CameraCapture
        ref={(ref) => {
          console.log('[ShootingAdvisor] CameraCapture ref 设置:', {
            hasRef: !!ref,
            previousRef: !!cameraCaptureRef.current
          });
          cameraCaptureRef.current = ref;
        }}
        className="fixed top-0 left-0 w-full h-full z-[1]"
        onFrameBuffer={(buffer) => {
          console.log('[ShootingAdvisor] 📸 收到帧缓冲区:', {
            frameCount: buffer.frames.length,
            fps: buffer.fps,
            timestamp: buffer.timestamp
          });
          handleFrameBuffer(buffer);
        }}
        onError={(error) => {
          console.error('[ShootingAdvisor] ❌ 摄像头错误:', error);
          setDebugInfo(`错误: ${error}`);
        }}
        onCameraReady={() => {
          console.log('[ShootingAdvisor] ✅ 摄像头就绪回调触发');
          setCameraReady(true);
          setDebugInfo(prev => prev || '摄像头已就绪，等待开始');
        }}
        onDebug={(msg) => {
          console.log('[ShootingAdvisor] 📝 摄像头调试:', msg);
          setDebugInfo(msg);
        }}
        mirror={true}
        config={{
          bufferSize: 8,
          captureIntervalMs: 500,
          jpegQuality: 0.75,
          targetWidth: 320,
          targetHeight: 240,
          overlapRatio: 0.3,
        }}
      />

      {/* Advice display layer */}
      <AdviceDisplay
        advice={currentAdvice}
        onDismiss={() => setCurrentAdvice(null)}
        showAdvanced={showAdvanced}
      />

      {/* AI Thinking Display - 显示 AI 的思考过程 */}
      {(environment || aiThinking) && (
        <div className="fixed left-4 top-20 z-[100] max-w-sm pointer-events-none">
          {/* 环境分析 */}
          {environment && (
            <div className="bg-black/80 backdrop-blur-md rounded-lg p-4 mb-2 border border-cyan-500/30 shadow-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-cyan-400 text-lg">🤖</span>
                <span className="text-cyan-300 text-sm font-bold">AI 环境分析</span>
              </div>
              <div className="text-white text-xs space-y-1">
                <p className="text-gray-300">{environment.analysis || '正在分析环境...'}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {environment.environment_tags.map((tag, i) => (
                    <span key={i} className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 rounded-full text-xs">
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="mt-2 pt-2 border-t border-gray-700">
                  <p className="text-gray-400">可拍性评分: <span className="text-green-400">{(environment.shootability_score * 100).toFixed(0)}%</span></p>
                  {environment.constraints.length > 0 && (
                    <p className="text-orange-400 text-xs mt-1">⚠️ {environment.constraints.join(', ')}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* AI 思考过程 */}
          {aiThinking && (
            <div className="bg-black/80 backdrop-blur-md rounded-lg p-4 border border-purple-500/30 shadow-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-purple-400 text-lg animate-pulse">💭</span>
                <span className="text-purple-300 text-sm font-bold">AI 正在思考</span>
              </div>
              <div className="text-white text-xs space-y-1">
                <p className="text-gray-300 italic">"{aiThinking.thought}"</p>
                {aiThinking.evidence.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-700">
                    <p className="text-gray-400 text-xs">判断依据:</p>
                    <ul className="text-gray-400 text-xs mt-1 space-y-0.5">
                      {aiThinking.evidence.map((ev, i) => (
                        <li key={i}>• {ev}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 任务推荐和拍摄指导 */}
          {currentTask && (currentTask.reason || currentTask.shooting_goal) && (
            <div className="bg-black/80 backdrop-blur-md rounded-lg p-4 mt-2 border border-green-500/30 shadow-lg">
              {/* 推荐理由 */}
              {currentTask.reason && (
                <>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-green-400 text-lg">✨</span>
                    <span className="text-green-300 text-sm font-bold">推荐理由</span>
                  </div>
                  <div className="text-white text-xs mb-3">
                    <p className="text-gray-300">{currentTask.reason}</p>
                  </div>
                </>
              )}
              
              {/* 拍摄目标 */}
              {currentTask.shooting_goal && (
                <div className="mb-2 pb-2 border-t border-gray-700 pt-2">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-yellow-400 text-lg">🎯</span>
                    <span className="text-yellow-300 text-xs font-bold">拍摄目标</span>
                  </div>
                  <p className="text-gray-300 text-xs">{currentTask.shooting_goal}</p>
                </div>
              )}
              
              {/* 要拍什么 */}
              {currentTask.what_to_capture && (
                <div className="pb-2 border-t border-gray-700 pt-2">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-blue-400 text-lg">📹</span>
                    <span className="text-blue-300 text-xs font-bold">拍摄内容</span>
                  </div>
                  <p className="text-gray-300 text-xs">{currentTask.what_to_capture}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* HUD Overlay - 最上层，始终显示 */}
      <HUDOverlay
        telemetry={telemetry}
        currentTask={currentTask}
        currentAdvice={currentAdvice}
        isRecording={isRecording}
      />

      {/* UI overlay layer */}
      <div className="fixed top-0 left-0 w-full h-full z-[2] pointer-events-none">
        {/* Top status bar */}
        <div className="pointer-events-auto fixed top-5 w-full px-4 flex justify-between items-start">
          {/* Session info */}
          <div className="bg-black/60 px-3 py-2 rounded-lg backdrop-blur-sm">
            <p className="text-white text-xs font-mono">
              Session: {sessionId}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <div className={`w-2 h-2 rounded-full ${
                connectionState === 'connected' ? 'bg-green-500' : 
                connectionState === 'error' ? 'bg-red-500' : 'bg-yellow-500'
              }`} />
              <span className="text-gray-400 text-xs">
                {connectionState === 'connected' ? '已连接' : 
                 connectionState === 'error' ? '连接错误' : '重连中...'}
              </span>
            </div>
          </div>

          {/* Stats */}
          <div className="bg-black/60 px-3 py-2 rounded-lg backdrop-blur-sm text-right">
            <p className="text-cyan-400 text-xs">
              服务器帧: {stats.framesProcessed}
            </p>
            <p className="text-orange-400 text-xs">
              本地帧: {stats.framesCaptured}
            </p>
            <p className="text-green-400 text-xs">
              建议: {stats.adviceReceived}
            </p>
            <p className="text-yellow-400 text-xs">
              摄像头: {cameraReady ? '就绪' : '未就绪'}
            </p>
            <p className="text-purple-400 text-xs">
              录制: {isRecording ? '是' : '否'}
            </p>
            {debugInfo && (
              <p className="text-pink-400 text-xs mt-1">
                {debugInfo}
              </p>
            )}
          </div>
        </div>

        {/* Center composition guide (non-obstructive per Requirement 10.6) */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[60%] h-[40%] border border-white/20 rounded-lg">
          {/* Rule of thirds lines */}
          <div className="absolute left-[33%] top-0 bottom-0 border-l border-white/10" />
          <div className="absolute left-[66%] top-0 bottom-0 border-l border-white/10" />
          <div className="absolute top-[33%] left-0 right-0 border-t border-white/10" />
          <div className="absolute top-[66%] left-0 right-0 border-t border-white/10" />
        </div>

        {/* Mode indicator */}
        <div className="absolute top-[15%] left-1/2 transform -translate-x-1/2">
          <div className="bg-black/60 px-4 py-2 rounded-full backdrop-blur-sm">
            <span className="text-white text-sm font-medium">
              🎬 实时拍摄建议模式
            </span>
          </div>
        </div>
      </div>

      {/* Bottom control bar */}
      <div className="fixed bottom-8 w-full z-[3] px-4">
        <div className="flex justify-center items-center gap-4">
          {/* Advanced toggle */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`px-4 py-3 rounded-full text-sm font-medium transition-all ${
              showAdvanced 
                ? 'bg-cyan-500/80 text-white' 
                : 'bg-white/20 text-white/70'
            }`}
          >
            {showAdvanced ? '专业模式' : '普通模式'}
          </button>

          {/* Main record button */}
          <button
            onClick={toggleRecording}
            disabled={connectionState !== 'connected'}
            className={`px-10 py-4 rounded-full text-white text-lg font-bold shadow-lg transition-all active:scale-95 disabled:opacity-50 ${
              isRecording
                ? 'bg-red-600 animate-pulse'
                : 'bg-gradient-to-r from-fuchsia-500 to-cyan-500'
            }`}
          >
            {isRecording ? '停止分析' : '开始分析'}
          </button>

          {/* Placeholder for symmetry */}
          <div className="w-[88px]" />
        </div>
      </div>

      {/* Connection error overlay */}
      {connectionState === 'error' && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-lg p-6 max-w-sm border border-red-500/50">
            <h3 className="text-red-400 font-bold text-lg mb-2">⚠️ 连接失败</h3>
            <p className="text-white text-sm mb-4">
              无法连接到服务器，请检查网络连接后重试。
            </p>
            <button
              onClick={connectWebSocket}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
            >
              重新连接
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShootingAdvisorView;

