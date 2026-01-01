import React, { useEffect, useState, useRef } from 'react';
import { QRCode } from './QRCode';
import { SessionService } from '../services/mockService';
import { ActionPayload } from '../types';

interface ConsoleViewProps {
  initialSessionId: string | null;
}

export const ConsoleView: React.FC<ConsoleViewProps> = ({ initialSessionId }) => {
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId);
  const [joinUrl, setJoinUrl] = useState<string>('');
  const [logs, setLogs] = useState<ActionPayload[]>([]);
  const [isLocal, setIsLocal] = useState(false);
  const [loading, setLoading] = useState(false);

  const serviceRef = useRef<SessionService | null>(null);

  // 1. Create/Init Session
  useEffect(() => {
    const init = async () => {
      // If we already have an ID (e.g. from deep link or previous state), just reconstruct URL
      if (sessionId) {
        // Simple manual URL reconstruction for display
        let href = window.location.href;
        const hashIndex = href.indexOf('#');
        let baseUrl = hashIndex !== -1 ? href.substring(0, hashIndex) : href;
        
        // 强制使用 HTTPS（摄像头访问需要）
        if (baseUrl.startsWith('http://') && window.location.port === '3000') {
          baseUrl = baseUrl.replace('http://', 'https://');
          console.log('🔄 自动将二维码 URL 转换为 HTTPS:', baseUrl);
        }
        
        setJoinUrl(`${baseUrl}#/mobile/${sessionId}`);
        return;
      }

      // Otherwise create a new session
      setLoading(true);
      const session = await SessionService.createSession();
      setSessionId(session.sessionId);
      setJoinUrl(session.joinUrl);
      setIsLocal(session.isLocal);
      setLoading(false);
      
      // Note: We DO NOT update the URL bar here to avoid "Location.assign" sandbox errors.
      // The session exists in React state only.
    };
    init();
  }, [sessionId]);

  // 2. Connect/Host Session
  useEffect(() => {
    if (!sessionId) return;

    const service = new SessionService(sessionId);
    serviceRef.current = service;

    if (isLocal) {
      service.startLocalBroadcasting();
    }

    service.connect((action) => {
      setLogs(prev => [action, ...prev].slice(0, 10));
    });

    return () => {
      service.disconnect();
    };
  }, [sessionId, isLocal]);

  if (loading || !sessionId) {
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center text-galaxy-light">
        <div className="animate-pulse font-mono">ESTABLISHING UPLINK...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-space-900 text-gray-200 p-8 flex flex-col items-center relative overflow-hidden">
      <div className="absolute inset-0 star-bg pointer-events-none"></div>
      
      <header className="z-10 text-center mb-12">
        <h1 className="text-4xl font-serif text-transparent bg-clip-text bg-gradient-to-r from-galaxy-light to-galaxy-accent mb-2">
          Story Galaxy Console
        </h1>
        <div className="flex items-center justify-center gap-4 text-xs font-mono tracking-widest uppercase">
          <span className="text-galaxy-light/60">ID: {sessionId}</span>
          <span className={`px-2 py-1 rounded ${isLocal ? 'bg-orange-500/20 text-orange-300' : 'bg-green-500/20 text-green-300'}`}>
            {isLocal ? 'LOCAL_HOST' : 'REMOTE_SERVER'}
          </span>
        </div>
      </header>

      <main className="z-10 w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-12">
        <section className="flex flex-col items-center justify-center space-y-6 bg-space-800/50 p-8 rounded-2xl border border-galaxy-light/10 backdrop-blur-sm">
          <h2 className="text-xl font-mono text-galaxy-gold mb-4">Scan to Join</h2>
          {joinUrl && <QRCode data={joinUrl} size={250} />}
          
          <div className="text-center space-y-2 max-w-sm">
            <p className="text-sm text-gray-400">Join URL:</p>
            <a 
              href={joinUrl} 
              target="_blank" 
              rel="noreferrer"
              className="block p-3 bg-space-700 rounded text-xs font-mono text-galaxy-light break-all hover:bg-space-700/80 transition-colors"
            >
              {joinUrl}
            </a>
            {joinUrl.startsWith('blob:') && (
               <p className="text-xs text-orange-400 mt-2">
                 Note: You are running in a sandbox. External devices cannot join this exact URL. Open the link in a new tab to simulate a mobile device.
               </p>
            )}
          </div>
        </section>

        <section className="bg-black/80 rounded-2xl border border-gray-800 p-6 font-mono text-sm overflow-hidden flex flex-col h-[500px] shadow-inner shadow-black">
          <div className="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
            <span className="text-green-500 font-bold">● LIVE STREAM</span>
            <span className="text-gray-500 text-xs">
              {isLocal ? 'INTERNAL_BROADCAST' : `ws://${sessionId}`}
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-gray-700">
            {logs.length === 0 && (
              <div className="text-gray-600 italic text-center mt-20">Waiting for stream...</div>
            )}
            {logs.map((log, idx) => (
              <div key={idx} className="border-l-2 border-galaxy-accent pl-3 py-1 animate-pulse-slow">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                  <span className="text-galaxy-light">{log.action}</span>
                </div>
                <div className="text-gray-300">{JSON.stringify(log)}</div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};