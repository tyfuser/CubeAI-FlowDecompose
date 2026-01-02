import React, { useEffect, useState } from 'react';

export const CameraDebug: React.FC = () => {
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [testResult, setTestResult] = useState<string>('');

  useEffect(() => {
    const collectDebugInfo = async () => {
      const info: any = {
        // 浏览器信息
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        vendor: navigator.vendor,
        language: navigator.language,
        languages: navigator.languages,
        
        // URL 信息
        protocol: window.location.protocol,
        hostname: window.location.hostname,
        port: window.location.port,
        href: window.location.href,
        
        // 安全上下文
        isSecureContext: window.isSecureContext,
        isLocalhost: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
        
        // MediaDevices API
        hasMediaDevices: !!navigator.mediaDevices,
        hasGetUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
        hasEnumerateDevices: !!(navigator.mediaDevices && navigator.mediaDevices.enumerateDevices),
        
        // 传统 API（兼容性检查）
        hasLegacyGetUserMedia: !!((navigator as any).getUserMedia || (navigator as any).webkitGetUserMedia || (navigator as any).mozGetUserMedia),
        
        // 权限 API
        hasPermissions: !!(navigator.permissions && navigator.permissions.query),
        
        // 设备信息
        deviceMemory: (navigator as any).deviceMemory,
        hardwareConcurrency: navigator.hardwareConcurrency,
      };

      // 尝试枚举设备
      if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          info.devices = devices.map(d => ({
            kind: d.kind,
            label: d.label || '(需要权限)',
            deviceId: d.deviceId,
          }));
        } catch (e: any) {
          info.deviceEnumError = e.message;
        }
      }

      // 检查权限状态
      if (navigator.permissions && navigator.permissions.query) {
        try {
          const cameraPermission = await navigator.permissions.query({ name: 'camera' as PermissionName });
          info.cameraPermission = cameraPermission.state;
        } catch (e: any) {
          info.permissionCheckError = e.message;
        }
      }

      setDebugInfo(info);
    };

    collectDebugInfo();
  }, []);

  const testCamera = async () => {
    setTestResult('测试中...');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: false
      });
      setTestResult('✅ 摄像头访问成功！');
      stream.getTracks().forEach(track => track.stop());
    } catch (err: any) {
      setTestResult(`❌ 失败: ${err.name} - ${err.message}`);
    }
  };

  if (!debugInfo) {
    return <div className="p-4 text-white">加载调试信息...</div>;
  }

  return (
    <div className="p-4 bg-black text-white min-h-screen font-mono text-xs overflow-auto">
      <h1 className="text-xl font-bold mb-4">🔍 摄像头访问调试信息</h1>
      
      <div className="mb-4">
        <button
          onClick={testCamera}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded mb-2"
        >
          测试摄像头访问
        </button>
        {testResult && (
          <div className={`mt-2 p-2 rounded ${testResult.includes('✅') ? 'bg-green-900' : 'bg-red-900'}`}>
            {testResult}
          </div>
        )}
      </div>

      <div className="space-y-4">
        <section className="bg-gray-800 p-4 rounded">
          <h2 className="font-bold mb-2">🌐 浏览器信息</h2>
          <pre className="whitespace-pre-wrap break-all">
{JSON.stringify({
  userAgent: debugInfo.userAgent,
  platform: debugInfo.platform,
  vendor: debugInfo.vendor,
  language: debugInfo.language,
}, null, 2)}
          </pre>
        </section>

        <section className="bg-gray-800 p-4 rounded">
          <h2 className="font-bold mb-2">🔗 URL 信息</h2>
          <pre className="whitespace-pre-wrap break-all">
{JSON.stringify({
  protocol: debugInfo.protocol,
  hostname: debugInfo.hostname,
  port: debugInfo.port,
  href: debugInfo.href,
}, null, 2)}
          </pre>
        </section>

        <section className="bg-gray-800 p-4 rounded">
          <h2 className="font-bold mb-2">🔒 安全上下文</h2>
          <pre className="whitespace-pre-wrap">
{JSON.stringify({
  isSecureContext: debugInfo.isSecureContext,
  isLocalhost: debugInfo.isLocalhost,
  protocol: debugInfo.protocol,
}, null, 2)}
          </pre>
          {!debugInfo.isSecureContext && (
            <div className="mt-2 p-2 bg-red-900 rounded">
              ⚠️ 非安全上下文！摄像头访问需要 HTTPS 或 localhost
            </div>
          )}
        </section>

        <section className="bg-gray-800 p-4 rounded">
          <h2 className="font-bold mb-2">📹 MediaDevices API</h2>
          <pre className="whitespace-pre-wrap">
{JSON.stringify({
  hasMediaDevices: debugInfo.hasMediaDevices,
  hasGetUserMedia: debugInfo.hasGetUserMedia,
  hasEnumerateDevices: debugInfo.hasEnumerateDevices,
  hasLegacyGetUserMedia: debugInfo.hasLegacyGetUserMedia,
}, null, 2)}
          </pre>
          {!debugInfo.hasMediaDevices && (
            <div className="mt-2 p-2 bg-red-900 rounded">
              ❌ navigator.mediaDevices 不存在！
            </div>
          )}
          {debugInfo.hasMediaDevices && !debugInfo.hasGetUserMedia && (
            <div className="mt-2 p-2 bg-red-900 rounded">
              ❌ getUserMedia 不可用！
            </div>
          )}
        </section>

        {debugInfo.devices && (
          <section className="bg-gray-800 p-4 rounded">
            <h2 className="font-bold mb-2">📷 可用设备</h2>
            <pre className="whitespace-pre-wrap">
{JSON.stringify(debugInfo.devices, null, 2)}
            </pre>
          </section>
        )}

        {debugInfo.cameraPermission && (
          <section className="bg-gray-800 p-4 rounded">
            <h2 className="font-bold mb-2">🔐 权限状态</h2>
            <pre className="whitespace-pre-wrap">
{JSON.stringify({
  cameraPermission: debugInfo.cameraPermission,
}, null, 2)}
            </pre>
          </section>
        )}

        <section className="bg-gray-800 p-4 rounded">
          <h2 className="font-bold mb-2">💻 设备信息</h2>
          <pre className="whitespace-pre-wrap">
{JSON.stringify({
  deviceMemory: debugInfo.deviceMemory,
  hardwareConcurrency: debugInfo.hardwareConcurrency,
}, null, 2)}
          </pre>
        </section>

        <section className="bg-blue-900 p-4 rounded">
          <h2 className="font-bold mb-2">💡 建议</h2>
          <ul className="list-disc list-inside space-y-1">
            {!debugInfo.isSecureContext && (
              <li>使用 HTTPS 访问（运行: USE_HTTPS=true ./start.sh）</li>
            )}
            {!debugInfo.hasMediaDevices && (
              <li>浏览器可能不支持 MediaDevices API，尝试更新浏览器或使用 Chrome</li>
            )}
            {debugInfo.hasMediaDevices && !debugInfo.hasGetUserMedia && (
              <li>getUserMedia 不可用，可能需要 HTTPS 或更新浏览器</li>
            )}
            {debugInfo.cameraPermission === 'denied' && (
              <li>摄像头权限被拒绝，请在浏览器设置中允许</li>
            )}
            {debugInfo.cameraPermission === 'prompt' && (
              <li>点击"测试摄像头访问"按钮来请求权限</li>
            )}
          </ul>
        </section>
      </div>
    </div>
  );
};

