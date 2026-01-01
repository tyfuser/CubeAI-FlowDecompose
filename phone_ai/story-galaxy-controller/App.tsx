import React, { useState, useEffect } from 'react';
import { ConsoleView } from './components/ConsoleView';
import { MobileView } from './components/MobileView';
import { CameraDebug } from './components/CameraDebug';
import { ShootingAdvisorView } from './components/ShootingAdvisorView';
import { ShootingConsoleView } from './components/ShootingConsoleView';

// Simple state-based view manager to avoid "Location.assign" errors in sandboxed environments
type ViewState = 'landing' | 'console' | 'mobile' | 'debug' | 'shooting-console' | 'shooting-mobile';

const Landing: React.FC<{ onStartShooting: () => void }> = ({ onStartShooting }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 flex flex-col items-center justify-center relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-fuchsia-500/20 rounded-full blur-3xl"></div>
      </div>
      
      <div className="z-10 text-center space-y-10 p-8 max-w-xl">
        {/* 标题区 */}
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/5 rounded-full border border-white/10 text-sm text-gray-400">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            AI 实时辅导
          </div>
          <h1 className="text-5xl font-bold text-white tracking-tight">
            拍摄助手
          </h1>
          <p className="text-lg text-gray-400 max-w-md mx-auto leading-relaxed">
            用手机扫码，AI 将实时分析拍摄环境，<br/>
            <span className="text-cyan-400">引导你完成专业的运镜拍摄</span>
          </p>
        </div>

        {/* 核心按钮 */}
        <div className="space-y-4">
          <button 
            onClick={onStartShooting}
            className="group relative px-16 py-6 bg-gradient-to-r from-cyan-500 to-fuchsia-500 text-white font-semibold text-xl rounded-2xl transition-all duration-300 shadow-2xl shadow-cyan-500/30 hover:shadow-fuchsia-500/30 hover:scale-105 active:scale-100"
          >
            <span className="flex items-center gap-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
              </svg>
              开始体验
            </span>
          </button>
          <p className="text-gray-500 text-sm">点击后会生成二维码，用手机扫码即可开始</p>
        </div>

        {/* 功能说明 */}
        <div className="grid grid-cols-3 gap-6 pt-8 border-t border-white/10">
          <div className="text-center space-y-2">
            <div className="text-2xl">🎯</div>
            <p className="text-xs text-gray-500">环境识别</p>
          </div>
          <div className="text-center space-y-2">
            <div className="text-2xl">🎬</div>
            <p className="text-xs text-gray-500">运镜引导</p>
          </div>
          <div className="text-center space-y-2">
            <div className="text-2xl">✨</div>
            <p className="text-xs text-gray-500">实时反馈</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const App: React.FC = () => {
  const [view, setView] = useState<ViewState>('landing');
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Create shooting session and show console with QR code
  const startShooting = async () => {
    try {
      const hostname = window.location.hostname;
      const port = '8000';  // Python 后端端口
      const res = await fetch(`http://${hostname}:${port}/api/realtime/session`, {
        method: 'POST',
      });
      
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        setView('shooting-console');
        window.location.hash = `#/shooting-console/${data.session_id}`;
      } else {
        // Fallback: create local session ID
        const localSessionId = Math.random().toString(36).substring(2, 8).toUpperCase();
        setSessionId(localSessionId);
        setView('shooting-console');
        window.location.hash = `#/shooting-console/${localSessionId}`;
      }
    } catch (error) {
      console.warn('Backend unreachable, using local session');
      const localSessionId = Math.random().toString(36).substring(2, 8).toUpperCase();
      setSessionId(localSessionId);
      setView('shooting-console');
      window.location.hash = `#/shooting-console/${localSessionId}`;
    }
  };

  useEffect(() => {
    // Check for Deep Links (Hash Routing manual implementation)
    const hash = window.location.hash;
    
    // Shooting advisor route (for mobile)
    if (hash.startsWith('#/shooting-advisor/')) {
      const id = hash.split('/')[2];
      if (id) {
        setSessionId(id);
        setView('shooting-mobile');
      }
    } else if (hash.startsWith('#/shooting-mobile/')) {
      const id = hash.split('/')[2];
      if (id) {
        setSessionId(id);
        setView('shooting-mobile');
      }
    } else if (hash.startsWith('#/mobile/')) {
      const id = hash.split('/')[2];
      if (id) {
        setSessionId(id);
        setView('mobile');
      }
    } else if (hash.startsWith('#/console/')) {
      const id = hash.split('/')[2];
      if (id && id !== 'new') {
        setSessionId(id);
        setView('console');
      }
    } else if (hash.startsWith('#/shooting-console/')) {
      const id = hash.split('/')[2];
      if (id) {
        setSessionId(id);
        setView('shooting-console');
      }
    } else if (hash === '#/debug') {
      setView('debug');
    }
  }, []);

  return (
    <>
      {view === 'landing' && (
        <Landing onStartShooting={startShooting} />
      )}
      
      {view === 'console' && (
        <ConsoleView 
          initialSessionId={sessionId} 
        />
      )}
      
      {view === 'mobile' && sessionId && (
        <MobileView sessionId={sessionId} />
      )}
      
      {view === 'shooting-console' && sessionId && (
        <ShootingConsoleView initialSessionId={sessionId} />
      )}
      
      {view === 'shooting-mobile' && sessionId && (
        <ShootingAdvisorView sessionId={sessionId} />
      )}
      
      {view === 'debug' && (
        <CameraDebug />
      )}
    </>
  );
};

export default App;