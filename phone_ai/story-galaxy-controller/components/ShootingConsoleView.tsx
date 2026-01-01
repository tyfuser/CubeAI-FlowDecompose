/**
 * ShootingConsoleView Component
 * 
 * Console view for realtime shooting advisor - displays QR code for mobile to scan.
 * Similar to ConsoleView but for shooting advisor mode.
 * 
 * Flow:
 * 1. Console creates shooting session
 * 2. Displays QR code with join URL
 * 3. Mobile scans QR code and opens ShootingAdvisorView
 * 4. Mobile captures frames and sends to server
 * 5. Server analyzes and sends advice back to mobile
 * 6. Console shows live stats and logs
 */
import React, { useEffect, useState, useRef } from 'react';
import { QRCode } from './QRCode';

interface ShootingConsoleViewProps {
  initialSessionId: string | null;
}

interface SessionStats {
  framesReceived: number;
  adviceSent: number;
  connectedClients: number;
  avgLatencyMs: number;
}

interface LogEntry {
  timestamp: number;
  type: 'info' | 'advice' | 'frame' | 'error' | 'connection';
  message: string;
  data?: any;
}

export const ShootingConsoleView: React.FC<ShootingConsoleViewProps> = ({ initialSessionId }) => {
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId);
  const [joinUrl, setJoinUrl] = useState<string>('');
  const [isLocal, setIsLocal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<SessionStats>({
    framesReceived: 0,
    adviceSent: 0,
    connectedClients: 0,
    avgLatencyMs: 0,
  });
  
  const wsRef = useRef<WebSocket | null>(null);

  // Create or restore session
  useEffect(() => {
    const init = async () => {
      if (sessionId) {
        // Reconstruct URL for existing session
        let href = window.location.href;
        const hashIndex = href.indexOf('#');
        let baseUrl = hashIndex !== -1 ? href.substring(0, hashIndex) : href;
        
        // Keep HTTP for local development (HTTPS requires certificate setup)
        // Mobile camera access will work on localhost or with proper HTTPS setup
        setJoinUrl(`${baseUrl}#/shooting-mobile/${sessionId}`);
        return;
      }

      // Create new session
      setLoading(true);
      try {
        const hostname = window.location.hostname;
        const port = '8000';  // Python 后端端口
        // Use HTTP for backend API (runs on same machine)
        const res = await fetch(`http://${hostname}:${port}/api/realtime/session`, {
          method: 'POST',
        });
        
        if (res.ok) {
          const data = await res.json();
          setSessionId(data.session_id);
          
          // Build join URL for mobile
          let href = window.location.href;
          const hashIndex = href.indexOf('#');
          let baseUrl = hashIndex !== -1 ? href.substring(0, hashIndex) : href;
          
          // Keep the same protocol as current page
          // HTTPS is needed for camera access on mobile, but requires certificate setup
          
          setJoinUrl(`${baseUrl}#/shooting-mobile/${data.session_id}`);
          setIsLocal(false);
          
          addLog('info', `会话已创建: ${data.session_id}`);
        } else {
          throw new Error('Server error');
        }
      } catch (error) {
        console.warn('Backend unreachable, using local session');
        const localSessionId = Math.random().toString(36).substring(2, 8).toUpperCase();
        setSessionId(localSessionId);
        
        let href = window.location.href;
        const hashIndex = href.indexOf('#');
        let baseUrl = hashIndex !== -1 ? href.substring(0, hashIndex) : href;
        
        setJoinUrl(`${baseUrl}#/shooting-mobile/${localSessionId}`);
        setIsLocal(true);
        
        addLog('info', `本地会话已创建: ${localSessionId}`);
      }
      setLoading(false);
    };
    
    init();
  }, [sessionId]);

  // Connect to WebSocket for monitoring
  useEffect(() => {
    if (!sessionId) return;

    const hostname = window.location.hostname;
    const port = '8080';
    // Use wss:// for HTTPS pages, ws:// for HTTP pages
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${hostname}:${port}/shooting/${sessionId}/console`;
    
    console.log(`[ShootingConsole] Connecting to ${wsUrl}`);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      addLog('connection', '控制台已连接到服务器');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleServerMessage(message);
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };

    ws.onerror = (error) => {
      addLog('error', '连接错误');
    };

    ws.onclose = () => {
      addLog('connection', '连接已断开');
    };

    return () => {
      ws.close();
    };
  }, [sessionId]);

  const addLog = (type: LogEntry['type'], message: string, data?: any) => {
    setLogs(prev => [{
      timestamp: Date.now(),
      type,
      message,
      data,
    }, ...prev].slice(0, 50));
  };

  const handleServerMessage = (message: any) => {
    switch (message.type) {
      case 'client_connected':
        setStats(prev => ({ ...prev, connectedClients: prev.connectedClients + 1 }));
        addLog('connection', `手机客户端已连接`);
        break;
      
      case 'client_disconnected':
        setStats(prev => ({ ...prev, connectedClients: Math.max(0, prev.connectedClients - 1) }));
        addLog('connection', `手机客户端已断开`);
        break;
      
      case 'frames_received':
        setStats(prev => ({ 
          ...prev, 
          framesReceived: prev.framesReceived + (message.count || 1) 
        }));
        addLog('frame', `收到 ${message.count || 1} 帧`, message);
        break;
      
      case 'advice_sent':
        setStats(prev => ({ ...prev, adviceSent: prev.adviceSent + 1 }));
        addLog('advice', `发送建议: ${message.advice?.message || ''}`, message.advice);
        break;
      
      case 'stats_update':
        setStats(prev => ({
          ...prev,
          avgLatencyMs: message.avg_latency_ms || prev.avgLatencyMs,
        }));
        break;
      
      default:
        console.log('Unknown message:', message);
    }
  };

  const getLogColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'advice': return 'text-green-400';
      case 'frame': return 'text-cyan-400';
      case 'error': return 'text-red-400';
      case 'connection': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  if (loading || !sessionId) {
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center text-galaxy-light">
        <div className="animate-pulse font-mono">创建拍摄会话中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-space-900 text-gray-200 p-8 flex flex-col items-center relative overflow-hidden">
      <div className="absolute inset-0 star-bg pointer-events-none" />
      
      {/* Header */}
      <header className="z-10 text-center mb-8">
        <h1 className="text-4xl font-serif text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 to-cyan-400 mb-2">
          🎬 实时拍摄建议
        </h1>
        <div className="flex items-center justify-center gap-4 text-xs font-mono tracking-widest uppercase">
          <span className="text-galaxy-light/60">Session: {sessionId}</span>
          <span className={`px-2 py-1 rounded ${isLocal ? 'bg-orange-500/20 text-orange-300' : 'bg-green-500/20 text-green-300'}`}>
            {isLocal ? 'LOCAL' : 'REMOTE'}
          </span>
        </div>
      </header>

      {/* Main content */}
      <main className="z-10 w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* QR Code section */}
        <section className="flex flex-col items-center justify-center space-y-6 bg-space-800/50 p-8 rounded-2xl border border-fuchsia-500/20 backdrop-blur-sm">
          <h2 className="text-xl font-mono text-fuchsia-400 mb-2">📱 手机扫码开始拍摄</h2>
          
          {joinUrl && <QRCode data={joinUrl} size={250} />}
          
          <div className="text-center space-y-2 max-w-sm">
            <p className="text-sm text-gray-400">手机扫描二维码后将打开摄像头</p>
            <a 
              href={joinUrl} 
              target="_blank" 
              rel="noreferrer"
              className="block p-3 bg-space-700 rounded text-xs font-mono text-fuchsia-300 break-all hover:bg-space-700/80 transition-colors"
            >
              {joinUrl}
            </a>
            <p className="text-xs text-orange-400 mt-2">
              ⚠️ 请确保手机和电脑在同一局域网内
            </p>
          </div>

          {/* Stats */}
          <div className="w-full grid grid-cols-2 gap-4 mt-4">
            <div className="bg-black/40 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-cyan-400">{stats.connectedClients}</p>
              <p className="text-xs text-gray-500">已连接设备</p>
            </div>
            <div className="bg-black/40 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-green-400">{stats.adviceSent}</p>
              <p className="text-xs text-gray-500">已发送建议</p>
            </div>
            <div className="bg-black/40 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-fuchsia-400">{stats.framesReceived}</p>
              <p className="text-xs text-gray-500">已处理帧数</p>
            </div>
            <div className="bg-black/40 p-4 rounded-lg text-center">
              <p className="text-2xl font-bold text-yellow-400">{stats.avgLatencyMs.toFixed(0)}ms</p>
              <p className="text-xs text-gray-500">平均延迟</p>
            </div>
          </div>
        </section>

        {/* Logs section */}
        <section className="bg-black/80 rounded-2xl border border-gray-800 p-6 font-mono text-sm overflow-hidden flex flex-col h-[600px] shadow-inner shadow-black">
          <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
            <span className="text-fuchsia-500 font-bold">● 实时日志</span>
            <span className="text-gray-500 text-xs">
              {isLocal ? 'LOCAL_MODE' : `ws://${sessionId}`}
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-2 pr-2 scrollbar-thin scrollbar-thumb-gray-700">
            {logs.length === 0 && (
              <div className="text-gray-600 italic text-center mt-20">
                等待手机连接...
              </div>
            )}
            {logs.map((log, idx) => (
              <div key={idx} className={`border-l-2 ${
                log.type === 'advice' ? 'border-green-500' :
                log.type === 'frame' ? 'border-cyan-500' :
                log.type === 'error' ? 'border-red-500' :
                log.type === 'connection' ? 'border-yellow-500' :
                'border-gray-500'
              } pl-3 py-1`}>
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                  <span className={getLogColor(log.type)}>{log.type.toUpperCase()}</span>
                </div>
                <div className="text-gray-300 text-sm">{log.message}</div>
                {log.data && (
                  <div className="text-gray-500 text-xs mt-1 truncate">
                    {JSON.stringify(log.data).slice(0, 100)}...
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Instructions */}
      <div className="z-10 mt-8 text-center text-sm text-gray-500 max-w-2xl">
        <p className="mb-2">📋 使用说明：</p>
        <ol className="text-left list-decimal list-inside space-y-1">
          <li>用手机扫描上方二维码</li>
          <li>允许浏览器访问摄像头权限</li>
          <li>点击"开始分析"按钮开始拍摄</li>
          <li>系统会实时分析画面并在手机上显示拍摄建议</li>
        </ol>
      </div>
    </div>
  );
};

export default ShootingConsoleView;
