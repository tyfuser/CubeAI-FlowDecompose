import React, { useEffect, useState, useRef } from 'react';
import { SessionService } from '../../services/mockService';
import { ActionPayload } from '../../types';

interface MobileViewProps {
  sessionId: string;
}

export const MobileView: React.FC<MobileViewProps> = ({ sessionId }) => {
  const [currentAction, setCurrentAction] = useState<ActionPayload | null>(null);
  const [connected, setConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [matchScore, setMatchScore] = useState<number>(92);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [cameraError, setCameraError] = useState<string | null>(null);
  const [cameraAvailable, setCameraAvailable] = useState<boolean>(true);

  // 初始化摄像头
  useEffect(() => {
    const initCamera = async () => {
      // 详细的浏览器信息收集
      const browserInfo = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        vendor: navigator.vendor,
        hasMediaDevices: !!navigator.mediaDevices,
        hasGetUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
        hasLegacyGetUserMedia: !!((navigator as any).getUserMedia || (navigator as any).webkitGetUserMedia || (navigator as any).mozGetUserMedia),
        protocol: window.location.protocol,
        hostname: window.location.hostname,
        isSecureContext: window.isSecureContext,
        isLocalhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
      };

      console.group('🔍 摄像头访问调试信息');
      console.log('浏览器信息:', browserInfo);
      console.log('User Agent:', navigator.userAgent);
      console.log('协议:', window.location.protocol);
      console.log('主机名:', window.location.hostname);
      console.log('完整 URL:', window.location.href);
      console.log('isSecureContext:', window.isSecureContext);
      console.log('navigator.mediaDevices:', navigator.mediaDevices);
      console.log('navigator.mediaDevices?.getUserMedia:', navigator.mediaDevices?.getUserMedia);

      // 检查浏览器支持
      if (!navigator.mediaDevices) {
        console.error('❌ navigator.mediaDevices 不存在');
        const errorMsg = `您的浏览器不支持摄像头访问 API。\n\n调试信息:\n- User Agent: ${browserInfo.userAgent}\n- 协议: ${browserInfo.protocol}\n- 主机名: ${browserInfo.hostname}\n- isSecureContext: ${browserInfo.isSecureContext}\n\n请尝试:\n1. 使用 Chrome 浏览器（推荐）\n2. 使用 Firefox 浏览器\n3. 确保使用 HTTPS 访问`;
        setCameraError(errorMsg);
        setCameraAvailable(false);
        console.groupEnd();
        return;
      }

      if (!navigator.mediaDevices.getUserMedia) {
        console.error('❌ navigator.mediaDevices.getUserMedia 不存在');
        const errorMsg = `getUserMedia API 不可用。\n\n调试信息:\n- User Agent: ${browserInfo.userAgent}\n- 协议: ${browserInfo.protocol}\n- 主机名: ${browserInfo.hostname}\n- isSecureContext: ${browserInfo.isSecureContext}\n\n可能原因:\n1. 浏览器版本过旧\n2. 需要 HTTPS 连接\n3. 浏览器不支持此 API`;
        setCameraError(errorMsg);
        setCameraAvailable(false);
        console.groupEnd();
        return;
      }

      // 检查是否为 HTTPS 或 localhost
      const isSecureContext = window.isSecureContext ||
        window.location.protocol === 'https:' ||
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1';

      console.log('安全上下文检查:', {
        isSecureContext,
        protocol: window.location.protocol,
        hostname: window.location.hostname,
        windowIsSecureContext: window.isSecureContext,
      });

      if (!isSecureContext) {
        console.error('❌ 非安全上下文，无法访问摄像头');
        const errorMsg = `摄像头访问需要 HTTPS 连接。\n\n当前协议: ${window.location.protocol}\n当前主机名: ${window.location.hostname}\nisSecureContext: ${window.isSecureContext}\n\n解决方案:\n1. 使用 HTTPS 访问（推荐）\n   - 运行: USE_HTTPS=true ./start.sh\n   - 或运行: ./setup-https.sh 然后 ./start-https.sh\n2. Edge 浏览器特殊设置:\n   - 在地址栏输入: edge://flags/#unsafely-treat-insecure-origin-as-secure\n   - 添加您的 IP 地址: ${window.location.hostname}:3000\n   - 设置为 Enabled，重启浏览器`;
        setCameraError(errorMsg);
        setCameraAvailable(false);
        console.groupEnd();
        return;
      }

      console.log('✅ 浏览器和环境检查通过，尝试访问摄像头...');

      try {
        console.log('📹 请求摄像头权限...');
        console.log('请求配置:', {
          video: {
            facingMode: "environment",
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
          audio: false
        });

        // 先尝试列出可用的设备（如果支持）
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          console.log('📷 可用设备:', devices.filter(d => d.kind === 'videoinput'));
        } catch (e) {
          console.warn('无法枚举设备（可能需要权限）:', e);
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "environment",
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
          audio: false
        });

        console.log('✅ 摄像头访问成功！', {
          tracks: stream.getTracks().map(t => ({
            kind: t.kind,
            label: t.label,
            enabled: t.enabled,
            readyState: t.readyState,
          }))
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          streamRef.current = stream;
          setCameraError(null);
          setCameraAvailable(true);
          console.log('✅ 视频元素已设置');
        }
        console.groupEnd();
      } catch (err: any) {
        console.error("❌ 无法访问摄像头:", err);
        console.error("错误详情:", {
          name: err.name,
          message: err.message,
          constraint: err.constraint,
          stack: err.stack,
        });

        let errorMsg = "无法访问摄像头。\n\n";
        errorMsg += `错误类型: ${err.name || 'Unknown'}\n`;
        errorMsg += `错误信息: ${err.message || err}\n\n`;
        errorMsg += `调试信息:\n`;
        errorMsg += `- User Agent: ${navigator.userAgent}\n`;
        errorMsg += `- 协议: ${window.location.protocol}\n`;
        errorMsg += `- 主机名: ${window.location.hostname}\n`;
        errorMsg += `- isSecureContext: ${window.isSecureContext}\n\n`;

        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          errorMsg += "🔒 权限被拒绝\n\n";
          errorMsg += "请允许浏览器访问摄像头权限：\n";
          errorMsg += "1. 点击地址栏左侧的锁图标\n";
          errorMsg += "2. 允许摄像头权限\n";
          errorMsg += "3. 刷新页面\n\n";
          errorMsg += "如果仍然不行，请检查：\n";
          errorMsg += "- 浏览器设置中的网站权限\n";
          errorMsg += "- 系统设置中的应用权限";
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          errorMsg += "📷 未找到摄像头设备\n\n";
          errorMsg += "请检查：\n";
          errorMsg += "1. 设备是否连接了摄像头\n";
          errorMsg += "2. 摄像头是否被其他应用占用\n";
          errorMsg += "3. 系统设置中是否禁用了摄像头";
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
          errorMsg += "📹 摄像头无法读取\n\n";
          errorMsg += "可能原因：\n";
          errorMsg += "1. 摄像头被其他应用占用\n";
          errorMsg += "2. 摄像头硬件故障\n";
          errorMsg += "3. 驱动程序问题\n\n";
          errorMsg += "请关闭其他使用摄像头的应用后重试";
        } else if (err.name === 'OverconstrainedError' || err.name === 'ConstraintNotSatisfiedError') {
          errorMsg += "⚙️ 摄像头不支持请求的配置\n\n";
          errorMsg += "尝试使用默认设置...\n";
          // 尝试使用更简单的配置
          try {
            console.log('🔄 尝试使用默认配置...');
            const simpleStream = await navigator.mediaDevices.getUserMedia({
              video: true,
              audio: false
            });
            if (videoRef.current) {
              videoRef.current.srcObject = simpleStream;
              streamRef.current = simpleStream;
              setCameraError(null);
              setCameraAvailable(true);
              console.log('✅ 使用默认配置成功');
              console.groupEnd();
              return;
            }
          } catch (retryErr: any) {
            console.error('❌ 默认配置也失败:', retryErr);
            errorMsg += `\n默认配置也失败: ${retryErr.message}`;
          }
        } else {
          errorMsg += "💡 提示：\n";
          errorMsg += "1. 确保使用 HTTPS 访问（localhost 除外）\n";
          errorMsg += "2. 检查浏览器版本是否支持\n";
          errorMsg += "3. 尝试使用 Chrome 浏览器\n";
          if (window.location.protocol === 'http:') {
            errorMsg += "\n⚠️ 当前使用 HTTP，请切换到 HTTPS！";
          }
        }

        setCameraError(errorMsg);
        setCameraAvailable(false);
        console.groupEnd();
      }
    };

    initCamera();

    return () => {
      // 清理摄像头流
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // 根据 action 更新 UI
  const updateUIFromAction = (action: ActionPayload) => {
    // 根据不同的 action 类型更新匹配度和运镜指导
    switch (action.action) {
      case "INIT_SYSTEM":
        setMatchScore(85);
        break;
      case "SCAN_SECTOR":
        setMatchScore(88);
        break;
      case "ENCOUNTER_GLITCH":
        setMatchScore(92);
        break;
      case "REQUEST_INPUT":
        setMatchScore(95);
        break;
      case "RESTORE_FRAGMENT":
        setMatchScore(98);
        break;
      default:
        setMatchScore(92);
    }
  };

  // WebSocket 连接
  useEffect(() => {
    if (!sessionId) return;

    const service = new SessionService(sessionId);

    service.connect((action) => {
      setConnected(true);
      setCurrentAction(action);

      // 根据 action 更新 UI
      updateUIFromAction(action);
    });

    return () => {
      service.disconnect();
    };
  }, [sessionId]);

  // 开始拍摄
  const startRecording = () => {
    setIsRecording(true);

    // 模拟拍摄过程
    setTimeout(() => {
      setIsRecording(false);
      alert("拍摄完成！\nAI 正在对比你的运镜轨迹...");

      // 模拟匹配度变化
      const newScore = Math.min(100, matchScore + Math.floor(Math.random() * 5));
      setMatchScore(newScore);
    }, 5000);
  };

  // 获取运镜指导文本（根据 action）
  const getMotionGuide = () => {
    if (!currentAction) return "📷 AI指令：向右平移 (Truck Right)";

    const guideMap: Record<string, string> = {
      "INIT_SYSTEM": "📷 AI指令：初始化拍摄位置",
      "SCAN_SECTOR": "📷 AI指令：扫描区域，保持稳定",
      "ENCOUNTER_GLITCH": "📷 AI指令：缓慢推进 (Dolly In)",
      "REQUEST_INPUT": "📷 AI指令：向右平移 (Truck Right)",
      "RESTORE_FRAGMENT": "📷 AI指令：完成拍摄，保持静止"
    };

    return guideMap[currentAction.action] || "📷 AI指令：向右平移 (Truck Right)";
  };

  // 获取构图框标签（根据 action）
  const getCompositionLabel = () => {
    if (!currentAction) return "🎯 目标主体：将人物放入框内";

    const labelMap: Record<string, string> = {
      "INIT_SYSTEM": "🎯 系统初始化：准备拍摄",
      "SCAN_SECTOR": "🎯 扫描模式：检测目标区域",
      "ENCOUNTER_GLITCH": "🎯 聚焦主体：保持构图稳定",
      "REQUEST_INPUT": "🎯 目标主体：将人物放入框内",
      "RESTORE_FRAGMENT": "🎯 完成构图：保持当前位置"
    };

    return labelMap[currentAction.action] || "🎯 目标主体：将人物放入框内";
  };

  // 获取顶部标题（根据 action）
  const getHeaderTitle = () => {
    if (!currentAction) return "拆解模式: 赛博朋克运镜";

    const titleMap: Record<string, string> = {
      "INIT_SYSTEM": "拆解模式: 系统初始化",
      "SCAN_SECTOR": "拆解模式: 区域扫描",
      "ENCOUNTER_GLITCH": "拆解模式: 赛博朋克运镜",
      "REQUEST_INPUT": "拆解模式: 交互拍摄",
      "RESTORE_FRAGMENT": "拆解模式: 完成拍摄"
    };

    return titleMap[currentAction.action] || "拆解模式: 赛博朋克运镜";
  };

  if (!connected) {
    return (
      <div className="h-screen w-screen bg-black flex flex-col items-center justify-center text-white">
        <div className="w-12 h-12 border-4 border-t-cyan-500 border-r-transparent border-b-cyan-500 border-l-transparent rounded-full animate-spin mb-4"></div>
        <p className="font-mono text-sm tracking-widest">连接中... {sessionId}</p>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-black overflow-hidden relative">
      {/* 视频层：全屏显示摄像头 */}
      {cameraAvailable && (
        <video
          ref={videoRef}
          id="camera-feed"
          autoPlay
          playsInline
          className="fixed top-0 left-0 w-full h-full object-cover z-[1] scale-x-[-1]"
        />
      )}

      {/* 摄像头错误提示 */}
      {cameraError && (
        <div className="fixed inset-0 bg-black/90 z-[10] flex items-center justify-center p-6">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full border border-red-500/50">
            <h3 className="text-red-400 font-bold text-lg mb-4">⚠️ 摄像头访问失败</h3>
            <div className="text-white text-sm whitespace-pre-line mb-4 leading-relaxed">
              {cameraError}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setCameraError(null);
                  window.location.reload();
                }}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
              >
                刷新页面
              </button>
              <button
                onClick={() => setCameraError(null)}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded transition-colors"
              >
                继续（无摄像头）
              </button>
            </div>
          </div>
        </div>
      )}

      {/* UI层：覆盖在视频之上 */}
      <div className="fixed top-0 left-0 w-full h-full z-[2] pointer-events-none">
        {/* 构图框 */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[60%] h-[40%] border-2 border-dashed border-cyan-500/80 rounded-xl shadow-[0_0_15px_rgba(0,255,255,0.3)]">
          <div className="absolute -top-8 left-0 text-cyan-500 font-bold text-sm drop-shadow-[0_2px_4px_rgba(0,0,0,1)] whitespace-nowrap">
            {getCompositionLabel()}
          </div>
          {/* 三分线 */}
          <div className="absolute left-[33%] top-0 bottom-0 border-l border-white/20"></div>
          <div className="absolute left-[66%] top-0 bottom-0 border-l border-white/20"></div>
        </div>

        {/* 运镜指导 */}
        <div className="absolute top-[80%] left-1/2 transform -translate-x-1/2 flex items-center gap-2.5 bg-black/60 px-5 py-2.5 rounded-[30px] backdrop-blur-sm">
          <span className="text-white text-sm whitespace-nowrap">{getMotionGuide()}</span>
          <div className="text-2xl text-fuchsia-500 arrow-animation">➤➤</div>
        </div>
      </div>

      {/* 顶部提示 */}
      <div className="fixed top-5 w-full text-center z-[3] text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] px-4">
        <h2 className="text-lg font-semibold mb-1">{getHeaderTitle()}</h2>
        <span className="bg-[#ff0055] px-2 py-1 rounded text-xs inline-block">
          Match: {matchScore}%
        </span>
        {currentAction && (
          <div className="mt-2 text-xs text-gray-300 max-w-[90%] mx-auto line-clamp-2">
            {currentAction.dialogue}
          </div>
        )}
      </div>

      {/* 底部控制栏 */}
      <div className="fixed bottom-8 w-full text-center z-[3]">
        <button
          onClick={startRecording}
          disabled={isRecording}
          className={`px-10 py-4 rounded-[50px] text-white text-lg font-bold shadow-[0_4px_15px_rgba(0,0,0,0.5)] cursor-pointer transition-all ${isRecording
              ? 'bg-red-600'
              : 'bg-gradient-to-r from-fuchsia-500 to-cyan-500'
            } active:scale-95 disabled:opacity-70`}
        >
          {isRecording ? '拍摄中...保持移动' : '开始模仿拍摄'}
        </button>
      </div>

      {/* 样式定义 */}
      <style>{`
        @keyframes moveRight {
          0% { transform: translateX(-5px); opacity: 0.2; }
          100% { transform: translateX(5px); opacity: 1; }
        }
        .arrow-animation {
          animation: moveRight 1s infinite;
        }
      `}</style>
    </div>
  );
};
