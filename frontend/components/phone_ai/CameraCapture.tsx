/**
 * CameraCapture Component
 * 
 * Captures frames from camera for realtime analysis.
 * Implements frame buffer capture (5-10 frames), JPEG compression,
 * Base64 encoding, and sliding window with overlap.
 * 
 * Requirements: 1.1, 1.2
 */
import React, { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from 'react';

export interface CameraCaptureConfig {
  /** Number of frames per buffer (5-10 per Requirement 1.2) */
  bufferSize: number;
  /** Capture interval in milliseconds (500-1000ms per Requirement 1.1) */
  captureIntervalMs: number;
  /** JPEG compression quality (0-1) */
  jpegQuality: number;
  /** Target resolution width */
  targetWidth: number;
  /** Target resolution height */
  targetHeight: number;
  /** Overlap ratio for sliding window (0-1) */
  overlapRatio: number;
}

export interface FrameBuffer {
  frames: string[];  // Base64-encoded JPEG images
  fps: number;
  timestamp: number;
}

export interface CameraCaptureRef {
  startCapture: () => Promise<void>;
  stopCapture: () => void;
  isCapturing: boolean;
  getStream: () => MediaStream | null;
}

interface CameraCaptureProps {
  config?: Partial<CameraCaptureConfig>;
  onFrameBuffer?: (buffer: FrameBuffer) => void;
  onError?: (error: string) => void;
  onCameraReady?: () => void;
  onDebug?: (message: string) => void;
  className?: string;
  mirror?: boolean;
}

const DEFAULT_CONFIG: CameraCaptureConfig = {
  bufferSize: 8,           // 8 frames per buffer
  captureIntervalMs: 500,  // Capture every 500ms (2 buffers/second)
  jpegQuality: 0.75,       // 75% JPEG quality
  targetWidth: 320,        // Low-res for speed
  targetHeight: 240,
  overlapRatio: 0.3,       // 30% overlap with previous buffer
};

export const CameraCapture = forwardRef<CameraCaptureRef, CameraCaptureProps>(({
  config: userConfig,
  onFrameBuffer,
  onError,
  onCameraReady,
  onDebug,
  className = '',
  mirror = true,
}, ref) => {
  const config = { ...DEFAULT_CONFIG, ...userConfig };
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameBufferRef = useRef<string[]>([]);
  const captureIntervalRef = useRef<number | null>(null);
  const lastCaptureTimeRef = useRef<number>(0);
  const cameraReadyRef = useRef<boolean>(false);
  const isCapturingRef = useRef<boolean>(false);
  const captureFrameRef = useRef<(() => string | null) | null>(null);
  
  const [isCapturing, setIsCapturing] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [captureCount, setCaptureCount] = useState(0);
  const [lastDebug, setLastDebug] = useState('');
  const [startCount, setStartCount] = useState(0);
  const [debugLogs, setDebugLogs] = useState<string[]>([]);
  
  // Add debug log with timestamp
  const addDebug = useCallback((module: string, message: string) => {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    const log = `[${timestamp}][${module}] ${message}`;
    console.log(log);
    setDebugLogs(prev => [...prev.slice(-9), log]);
    setLastDebug(message);
  }, []);
  
  // Keep refs in sync with state
  useEffect(() => {
    cameraReadyRef.current = cameraReady;
    console.log('[CameraCapture] cameraReady state changed to:', cameraReady);
  }, [cameraReady]);
  
  useEffect(() => {
    isCapturingRef.current = isCapturing;
    console.log('[CameraCapture] isCapturing state changed to:', isCapturing);
  }, [isCapturing]);

  // Initialize camera - called on demand, not on mount
  const initCamera = useCallback(async () => {
    console.group('🔍 [CameraCapture] initCamera 开始');
    console.log('[INIT] 检查状态:', {
      cameraReady: cameraReadyRef.current,
      hasStream: !!streamRef.current,
      videoRef: !!videoRef.current
    });
    
    if (cameraReadyRef.current || streamRef.current) {
      addDebug('INIT', '摄像头已初始化，跳过');
      console.log('[INIT] ✓ 摄像头已就绪，跳过初始化');
      console.groupEnd();
      return true;
    }
    
    addDebug('INIT', '开始初始化摄像头...');
    console.log('[INIT] 开始初始化摄像头...');
    
    // 详细的浏览器环境检查
    const browserInfo = {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      hasMediaDevices: !!navigator.mediaDevices,
      hasGetUserMedia: !!(navigator.mediaDevices?.getUserMedia),
      protocol: window.location.protocol,
      hostname: window.location.hostname,
      href: window.location.href,
      isSecureContext: window.isSecureContext,
      isLocalhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    };
    
    console.log('[INIT] 浏览器环境信息:', browserInfo);
    addDebug('INIT', `浏览器: ${browserInfo.userAgent.substring(0, 50)}...`);
    addDebug('INIT', `协议: ${browserInfo.protocol}, 主机: ${browserInfo.hostname}`);
    
    // Check browser support
    if (!navigator.mediaDevices) {
      const errorMsg = '您的浏览器不支持摄像头访问 API (navigator.mediaDevices 不存在)';
      console.error('[INIT] ❌', errorMsg);
      console.error('[INIT] 浏览器信息:', browserInfo);
      addDebug('INIT', `错误: ${errorMsg}`);
      setCameraError(errorMsg);
      onError?.(errorMsg);
      console.groupEnd();
      return false;
    }
    
    if (!navigator.mediaDevices.getUserMedia) {
      const errorMsg = '您的浏览器不支持摄像头访问 API (getUserMedia 不存在)';
      console.error('[INIT] ❌', errorMsg);
      console.error('[INIT] navigator.mediaDevices:', navigator.mediaDevices);
      addDebug('INIT', `错误: ${errorMsg}`);
      setCameraError(errorMsg);
      onError?.(errorMsg);
      console.groupEnd();
      return false;
    }
    
    console.log('[INIT] ✓ getUserMedia API 可用');
    addDebug('INIT', 'getUserMedia API 可用');

    // Check secure context
    const isSecureContext = window.isSecureContext || 
                            window.location.protocol === 'https:' || 
                            window.location.hostname === 'localhost' ||
                            window.location.hostname === '127.0.0.1';
    
    console.log('[INIT] 安全上下文检查:', {
      isSecureContext,
      windowIsSecureContext: window.isSecureContext,
      protocol: window.location.protocol,
      hostname: window.location.hostname,
      calculated: isSecureContext
    });
    addDebug('INIT', `安全上下文: ${isSecureContext}, 协议: ${window.location.protocol}`);
    
    if (!isSecureContext) {
      const errorMsg = `摄像头访问需要 HTTPS 连接。当前协议: ${window.location.protocol}, isSecureContext: ${window.isSecureContext}`;
      console.error('[INIT] ❌ 非安全上下文:', errorMsg);
      console.error('[INIT] 详细信息:', browserInfo);
      addDebug('INIT', `错误: ${errorMsg}`);
      setCameraError(errorMsg);
      onError?.(errorMsg);
      console.groupEnd();
      return false;
    }
    
    console.log('[INIT] ✓ 安全上下文检查通过');

    try {
      console.log('[INIT] 📹 准备请求摄像头权限...');
      addDebug('INIT', '请求摄像头权限...');
      
      const constraints = {
        video: {
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      };
      
      console.log('[INIT] 请求约束:', JSON.stringify(constraints, null, 2));
      console.log('[INIT] 等待用户授权...');
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      
      console.log('[INIT] ✅ 摄像头权限已授予！');
      console.log('[INIT] Stream 信息:', {
        id: stream.id,
        active: stream.active,
        tracks: stream.getTracks().map(t => ({
          kind: t.kind,
          label: t.label,
          enabled: t.enabled,
          readyState: t.readyState,
          settings: t.getSettings()
        }))
      });
      
      // Log stream info
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        const settings = videoTrack.getSettings();
        console.log('[INIT] 视频轨道详情:', {
          label: videoTrack.label,
          settings: settings,
          capabilities: videoTrack.getCapabilities()
        });
        addDebug('STREAM', `视频轨道: ${videoTrack.label}`);
        addDebug('STREAM', `分辨率: ${settings.width}x${settings.height}`);
        addDebug('STREAM', `帧率: ${settings.frameRate}`);
      } else {
        console.warn('[INIT] ⚠️  未找到视频轨道');
      }
      
      streamRef.current = stream;
      console.log('[INIT] Stream 已保存到 streamRef');
      
      if (videoRef.current) {
        console.log('[INIT] 设置 video.srcObject...');
        addDebug('VIDEO', '设置 video.srcObject...');
        videoRef.current.srcObject = stream;
        console.log('[INIT] video.srcObject 已设置');
        
        // Try to play immediately (user gesture context)
        console.log('[INIT] 尝试播放视频...');
        addDebug('VIDEO', '尝试播放视频...');
        try {
          await videoRef.current.play();
          console.log('[INIT] ✅ 视频播放成功!');
          console.log('[INIT] 视频尺寸:', {
            videoWidth: videoRef.current.videoWidth,
            videoHeight: videoRef.current.videoHeight,
            readyState: videoRef.current.readyState,
            paused: videoRef.current.paused,
            muted: videoRef.current.muted
          });
          addDebug('VIDEO', '视频播放成功!');
          addDebug('VIDEO', `videoWidth: ${videoRef.current.videoWidth}, videoHeight: ${videoRef.current.videoHeight}`);
          
          cameraReadyRef.current = true;
          setCameraReady(true);
          setCameraError(null);
          console.log('[INIT] ✅ 摄像头初始化完成！');
          console.groupEnd();
          onCameraReady?.();
          return true;
        } catch (playError: any) {
          console.warn('[INIT] ⚠️  立即播放失败:', playError);
          console.log('[INIT] 错误详情:', {
            name: playError.name,
            message: playError.message,
            stack: playError.stack
          });
          addDebug('VIDEO', `播放失败: ${playError.message}`);
          
          // Wait for loadedmetadata event
          console.log('[INIT] 等待 loadedmetadata 事件...');
          addDebug('VIDEO', '等待 loadedmetadata 事件...');
          return new Promise<boolean>((resolve) => {
            const video = videoRef.current!;
            
            const onLoaded = () => {
              console.log('[INIT] ✅ loadedmetadata 事件触发');
              addDebug('VIDEO', 'loadedmetadata 触发');
              video.play().then(() => {
                console.log('[INIT] ✅ 延迟播放成功');
                addDebug('VIDEO', '延迟播放成功');
                cameraReadyRef.current = true;
                setCameraReady(true);
                setCameraError(null);
                console.log('[INIT] ✅ 摄像头初始化完成（延迟播放）');
                console.groupEnd();
                onCameraReady?.();
                resolve(true);
              }).catch((e) => {
                console.error('[INIT] ❌ 延迟播放失败:', e);
                addDebug('VIDEO', `延迟播放失败: ${e.message}`);
                console.groupEnd();
                resolve(false);
              });
            };
            
            video.addEventListener('loadedmetadata', onLoaded, { once: true });
            console.log('[INIT] 已注册 loadedmetadata 监听器');
            
            // Timeout after 5 seconds
            setTimeout(() => {
              video.removeEventListener('loadedmetadata', onLoaded);
              console.warn('[INIT] ⚠️  loadedmetadata 超时');
              addDebug('VIDEO', 'loadedmetadata 超时');
              console.groupEnd();
              resolve(false);
            }, 5000);
          });
        }
      } else {
        addDebug('VIDEO', '错误: videoRef.current 为空');
        return false;
      }
    } catch (err: any) {
      console.error('[INIT] ❌ 摄像头初始化失败:', err);
      console.error('[INIT] 错误详情:', {
        name: err.name,
        message: err.message,
        constraint: err.constraint,
        stack: err.stack
      });
      addDebug('INIT', `摄像头错误: ${err.name} - ${err.message}`);
      let errorMsg = '无法访问摄像头';
      
      if (err.name === 'NotAllowedError') {
        errorMsg = '摄像头权限被拒绝，请允许浏览器访问摄像头';
        console.error('[INIT] ❌ 用户拒绝了摄像头权限');
      } else if (err.name === 'NotFoundError') {
        errorMsg = '未找到摄像头设备';
        console.error('[INIT] ❌ 未找到摄像头设备');
      } else if (err.name === 'NotReadableError') {
        errorMsg = '摄像头被其他应用占用';
        console.error('[INIT] ❌ 摄像头被占用');
      } else if (err.name === 'OverconstrainedError') {
        console.warn('[INIT] ⚠️  约束过严，尝试简化约束...');
        addDebug('INIT', '尝试简化约束...');
        try {
          console.log('[INIT] 使用简化约束重新请求...');
          const simpleStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false,
          });
          console.log('[INIT] ✅ 简化约束成功');
          streamRef.current = simpleStream;
          if (videoRef.current) {
            videoRef.current.srcObject = simpleStream;
            await videoRef.current.play();
            cameraReadyRef.current = true;
            setCameraReady(true);
            setCameraError(null);
            console.log('[INIT] ✅ 摄像头初始化完成（简化约束）');
            console.groupEnd();
            onCameraReady?.();
            return true;
          }
        } catch (retryErr: any) {
          console.error('[INIT] ❌ 简化约束也失败:', retryErr);
          errorMsg = '摄像头不支持请求的配置';
        }
      }
      
      console.error('[INIT] ❌ 最终错误:', errorMsg);
      setCameraError(errorMsg);
      onError?.(errorMsg);
      console.groupEnd();
      return false;
    }
  }, [onError, onCameraReady, addDebug]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (captureIntervalRef.current) {
        clearInterval(captureIntervalRef.current);
      }
    };
  }, []);

  // Capture a single frame as Base64 JPEG - stored in ref for interval access
  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    setLastDebug(`captureFrame called`);
    
    if (!video) {
      setLastDebug('错误: video ref 为空');
      return null;
    }
    
    if (!canvas) {
      setLastDebug('错误: canvas ref 为空');
      return null;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setLastDebug('错误: 无法获取 canvas context');
      return null;
    }

    // Set canvas size to target resolution
    canvas.width = config.targetWidth;
    canvas.height = config.targetHeight;

    try {
      // Draw video frame to canvas (scaled down)
      ctx.drawImage(video, 0, 0, config.targetWidth, config.targetHeight);

      // Convert to JPEG Base64
      const dataUrl = canvas.toDataURL('image/jpeg', config.jpegQuality);
      
      setLastDebug(`帧捕获成功 ${dataUrl.length} bytes`);
      
      // Remove data URL prefix to get pure Base64
      return dataUrl.replace(/^data:image\/jpeg;base64,/, '');
    } catch (err) {
      setLastDebug(`错误: drawImage 失败 ${err}`);
      return null;
    }
  }, [config.targetWidth, config.targetHeight, config.jpegQuality]);
  
  // Keep ref updated
  useEffect(() => {
    captureFrameRef.current = captureFrame;
  }, [captureFrame]);

  // Start capturing frames - use refs to avoid stale closure
  const startCapture = useCallback(async () => {
    setStartCount(prev => prev + 1);
    addDebug('CAPTURE', `startCapture 调用 #${startCount + 1}`);
    
    if (isCapturingRef.current) {
      addDebug('CAPTURE', '已在录制中，跳过');
      return;
    }
    
    // Initialize camera if not ready (user gesture context)
    if (!cameraReadyRef.current) {
      addDebug('CAPTURE', '摄像头未就绪，开始初始化...');
      const success = await initCamera();
      if (!success) {
        addDebug('CAPTURE', '摄像头初始化失败');
        return;
      }
    }
    
    addDebug('CAPTURE', `状态: capturing=${isCapturingRef.current}, ready=${cameraReadyRef.current}`);
    
    // Check video element state
    const video = videoRef.current;
    if (video) {
      addDebug('CAPTURE', `video.readyState: ${video.readyState}`);
      addDebug('CAPTURE', `video.paused: ${video.paused}`);
      addDebug('CAPTURE', `video.videoWidth: ${video.videoWidth}`);
      addDebug('CAPTURE', `video.videoHeight: ${video.videoHeight}`);
    }

    const frameIntervalMs = config.captureIntervalMs / config.bufferSize;
    addDebug('CAPTURE', `帧间隔: ${frameIntervalMs}ms, 缓冲区大小: ${config.bufferSize}`);
    
    isCapturingRef.current = true;
    setIsCapturing(true);
    frameBufferRef.current = [];
    lastCaptureTimeRef.current = Date.now();

    let intervalCallCount = 0;
    
    // Start interval with inline capture logic
    captureIntervalRef.current = window.setInterval(() => {
      intervalCallCount++;
      
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      if (!video) {
        addDebug('INTERVAL', `#${intervalCallCount} video 为空`);
        return;
      }
      
      if (!canvas) {
        addDebug('INTERVAL', `#${intervalCallCount} canvas 为空`);
        return;
      }
      
      // Log video state periodically
      if (intervalCallCount <= 3 || intervalCallCount % 10 === 0) {
        addDebug('INTERVAL', `#${intervalCallCount} video.readyState=${video.readyState}, paused=${video.paused}`);
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        addDebug('INTERVAL', `#${intervalCallCount} 无法获取 context`);
        return;
      }

      canvas.width = config.targetWidth;
      canvas.height = config.targetHeight;

      try {
        ctx.drawImage(video, 0, 0, config.targetWidth, config.targetHeight);
        const dataUrl = canvas.toDataURL('image/jpeg', config.jpegQuality);
        const frame = dataUrl.replace(/^data:image\/jpeg;base64,/, '');
        
        const frameSize = Math.round(frame.length / 1024);
        
        frameBufferRef.current.push(frame);
        setCaptureCount(prev => prev + 1);
        
        if (intervalCallCount <= 3) {
          addDebug('FRAME', `#${intervalCallCount} 捕获成功, 大小: ${frameSize}KB`);
        }
        
        // When buffer is full, emit and slide
        if (frameBufferRef.current.length >= config.bufferSize) {
          const now = Date.now();
          const timeDelta = now - lastCaptureTimeRef.current;
          const fps = lastCaptureTimeRef.current > 0 
            ? (config.bufferSize * 1000) / timeDelta 
            : 30;
          
          const buffer: FrameBuffer = {
            frames: [...frameBufferRef.current],
            fps: Math.round(fps * 10) / 10,
            timestamp: now,
          };
          
          const totalSize = Math.round(buffer.frames.reduce((sum, f) => sum + f.length, 0) / 1024);
          addDebug('SEND', `发送 ${buffer.frames.length} 帧, 总大小: ${totalSize}KB, FPS: ${buffer.fps}`);
          
          onFrameBuffer?.(buffer);
          
          // Slide window
          const overlapFrames = Math.floor(config.bufferSize * config.overlapRatio);
          frameBufferRef.current = frameBufferRef.current.slice(-overlapFrames);
          lastCaptureTimeRef.current = now;
        }
      } catch (err) {
        addDebug('INTERVAL', `#${intervalCallCount} 错误: ${err}`);
      }
    }, frameIntervalMs);
    
    addDebug('CAPTURE', `定时器已启动: ID=${captureIntervalRef.current}`);
  }, [config, onFrameBuffer, addDebug, startCount, initCamera]);

  // Stop capturing frames
  const stopCapture = useCallback(() => {
    setLastDebug('停止录制');
    
    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
      captureIntervalRef.current = null;
    }
    isCapturingRef.current = false;
    setIsCapturing(false);
    frameBufferRef.current = [];
  }, []);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    startCapture,
    stopCapture,
    isCapturing,
    getStream: () => streamRef.current,
  }), [startCapture, stopCapture, isCapturing]);

  return (
    <div className={`relative ${className}`}>
      {/* Video element */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`w-full h-full object-cover ${mirror ? 'scale-x-[-1]' : ''}`}
      />
      
      {/* Hidden canvas for frame capture */}
      <canvas
        ref={canvasRef}
        className="hidden"
      />
      
      {/* Camera error overlay */}
      {cameraError && (
        <div className="absolute inset-0 bg-black/90 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-lg p-4 max-w-sm border border-red-500/50">
            <h3 className="text-red-400 font-bold text-sm mb-2">⚠️ 摄像头访问失败</h3>
            <p className="text-white text-xs whitespace-pre-line">{cameraError}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-3 w-full bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-sm"
            >
              刷新页面
            </button>
          </div>
        </div>
      )}
      
      {/* Capture indicator */}
      {isCapturing && (
        <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/50 px-2 py-1 rounded-full">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <span className="text-white text-xs">REC</span>
        </div>
      )}
      
      {/* Internal debug display */}
      <div className="absolute bottom-2 left-2 right-2 bg-black/80 px-2 py-1 rounded text-xs text-white font-mono max-h-[150px] overflow-y-auto">
        <div className="flex justify-between mb-1">
          <span>ready: {cameraReady ? '✓' : '✗'} | cap: {isCapturing ? '✓' : '✗'}</span>
          <span>frames: {captureCount} | starts: {startCount}</span>
        </div>
        <div className="text-yellow-300 font-bold mb-1">
          {isCapturing ? `🔴 定时器已启动 #${startCount}` : '⏸️ 未启动'}
        </div>
        <div className="space-y-0.5 text-[10px]">
          {debugLogs.map((log, i) => (
            <div key={i} className="text-gray-300 truncate">{log}</div>
          ))}
        </div>
      </div>
    </div>
  );
});

CameraCapture.displayName = 'CameraCapture';

export default CameraCapture;
