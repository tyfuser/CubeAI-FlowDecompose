/**
 * ShootingConsoleView Component
 * 
 * Console view for realtime shooting advisor - displays QR code for mobile to scan.
 * Refactored to match Dashboard UI style.
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

  if (loading || !sessionId) {
    return (
      <div className="h-full overflow-y-auto bg-[#0b0f1a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-6">
          <div className="w-16 h-16 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
          <p className="text-indigo-400 font-black uppercase tracking-widest text-xs animate-pulse">Initializing Neural Link...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-[#0b0f1a] scrollbar-thin">
      <div className="p-8 lg:p-12 max-w-[1600px] mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700 w-full">

        {/* Header */}
        <header className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-8">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <h2 className="text-4xl font-black tracking-tighter text-white italic">
                Shooting Assistant <span className="text-indigo-500">.</span>
              </h2>
              <div className="px-3 py-1 bg-indigo-600/10 border border-indigo-500/20 rounded-full flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full ${sessionId ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'} `} />
                <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">
                  {sessionId ? `Session: ${sessionId}` : 'Initializing...'}
                </span>
              </div>

              {sessionId && (
                <div className={`px-3 py-1 rounded-full border flex items-center gap-2 ${isLocal ? 'bg-orange-500/10 border-orange-500/20' : 'bg-indigo-500/10 border-indigo-500/20'}`}>
                  <span className={`text-[10px] font-black uppercase tracking-widest ${isLocal ? 'text-orange-400' : 'text-indigo-400'}`}>
                    {isLocal ? 'LOCAL MODE' : 'REMOTE MODE'}
                  </span>
                </div>
              )}
            </div>
            <p className="text-gray-400 font-medium text-sm">实时连接手机摄像头，获取 AI 辅助拍摄建议。请确保设备在同一网络环境下。</p>
          </div>
        </header>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">

          {/* Left Column (QR Code & Status) - 4 cols */}
          <div className="xl:col-span-4 space-y-10">
            <section className="bg-gradient-to-br from-indigo-600/10 via-[#111827] to-[#0d111d] border border-indigo-500/20 p-10 rounded-[3rem] shadow-2xl flex flex-col items-center text-center relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 opacity-20 group-hover:opacity-40 transition-opacity">
                <div className="w-32 h-32 bg-indigo-500/30 blur-3xl rounded-full" />
              </div>

              <h3 className="text-2xl font-black text-white mb-6 tracking-tight">扫码连接设备</h3>

              <div className="p-4 bg-white rounded-3xl shadow-xl shadow-indigo-500/20 mb-6 group-hover:scale-105 transition-transform duration-500">
                {joinUrl ? <QRCode data={joinUrl} size={220} /> : <div className="w-[220px] h-[220px] bg-gray-100 animate-pulse rounded-xl" />}
              </div>

              <div className="space-y-4 w-full">
                <div className="bg-[#0b0f1a]/50 p-4 rounded-2xl border border-white/5 backdrop-blur-sm">
                  <p className="text-xs text-gray-400 font-medium mb-2">连接地址</p>
                  <a
                    href={joinUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] font-mono text-indigo-400 break-all hover:text-indigo-300 transition-colors block"
                  >
                    {joinUrl || 'Generating...'}
                  </a>
                </div>

                <p className="text-[10px] text-yellow-500/80 font-bold bg-yellow-500/5 px-4 py-2 rounded-xl border border-yellow-500/10">
                  ⚠️ 提示：请允许浏览器访问摄像头权限
                </p>
              </div>
            </section>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-900/40 border border-gray-800/50 p-5 rounded-[2rem] flex flex-col gap-2 shadow-xl">
                <div className="p-2 rounded-xl w-fit bg-blue-400/10 text-blue-400">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                </div>
                <div>
                  <span className="text-2xl font-black text-white">{stats.connectedClients}</span>
                  <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-1">在线设备</p>
                </div>
              </div>
              <div className="bg-gray-900/40 border border-gray-800/50 p-5 rounded-[2rem] flex flex-col gap-2 shadow-xl">
                <div className="p-2 rounded-xl w-fit bg-green-400/10 text-green-400">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
                <div>
                  <span className="text-2xl font-black text-white">{stats.adviceSent}</span>
                  <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-1">已发建议</p>
                </div>
              </div>
              <div className="bg-gray-900/40 border border-gray-800/50 p-5 rounded-[2rem] flex flex-col gap-2 shadow-xl">
                <div className="p-2 rounded-xl w-fit bg-purple-400/10 text-purple-400">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                </div>
                <div>
                  <span className="text-2xl font-black text-white">{stats.framesReceived}</span>
                  <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-1">处理帧数</p>
                </div>
              </div>
              <div className="bg-gray-900/40 border border-gray-800/50 p-5 rounded-[2rem] flex flex-col gap-2 shadow-xl">
                <div className="p-2 rounded-xl w-fit bg-yellow-400/10 text-yellow-400">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                </div>
                <div>
                  <span className="text-2xl font-black text-white">{stats.avgLatencyMs.toFixed(0)}<span className="text-xs">ms</span></span>
                  <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-1">平均延迟</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (Logs) - 8 cols */}
          <div className="xl:col-span-8 h-[600px] xl:h-auto">
            <section className="bg-gray-950 p-8 rounded-[3.5rem] border border-gray-800/50 shadow-2xl h-full flex flex-col relative overflow-hidden">
              <div className="flex items-center justify-between mb-6 relative z-10">
                <h3 className="font-black text-sm uppercase tracking-[0.2em] flex items-center gap-3 text-white">
                  <span className="flex h-3 w-3 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                  </span>
                  System Live Logs
                </h3>
                <div className="flex gap-2">
                  <span className="text-[10px] font-mono text-gray-600 bg-gray-900 px-2 py-1 rounded-lg border border-gray-800">{logs.length} entries</span>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto pr-2 space-y-3 font-mono text-xs relative z-10 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                {logs.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-gray-600 space-y-4">
                    <div className="w-12 h-12 border-4 border-gray-800 border-t-indigo-500 rounded-full animate-spin" />
                    <p className="font-medium">Waiting for connection stream...</p>
                  </div>
                )}
                {logs.map((log, idx) => (
                  <div key={idx} className={`p-4 rounded-2xl border transition-all hover:bg-white/[0.02] ${log.type === 'advice' ? 'bg-green-500/5 border-green-500/10' :
                      log.type === 'frame' ? 'bg-blue-500/5 border-blue-500/10' :
                        log.type === 'error' ? 'bg-red-500/5 border-red-500/10' :
                          log.type === 'connection' ? 'bg-yellow-500/5 border-yellow-500/10' :
                            'bg-gray-900/50 border-gray-800'
                    }`}>
                    <div className="flex justify-between items-start mb-1">
                      <span className={`font-black uppercase tracking-wider text-[9px] px-2 py-0.5 rounded-md ${log.type === 'advice' ? 'bg-green-500/20 text-green-400' :
                          log.type === 'frame' ? 'bg-blue-500/20 text-blue-400' :
                            log.type === 'error' ? 'bg-red-500/20 text-red-400' :
                              log.type === 'connection' ? 'bg-yellow-500/20 text-yellow-400' :
                                'bg-gray-800 text-gray-400'
                        }`}>
                        {log.type}
                      </span>
                      <span className="text-gray-600">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-gray-300 font-medium pl-1">{log.message}</p>
                    {log.data && (
                      <pre className="mt-2 text-[10px] text-gray-500 overflow-x-auto bg-black/20 p-2 rounded-lg border border-white/5">
                        {JSON.stringify(log.data, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </section>
          </div>

        </div>
      </div>
    </div>
  );
};

export default ShootingConsoleView;
