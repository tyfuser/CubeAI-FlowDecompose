/**
 * URL 工具函数
 * 智能处理 HTTP/HTTPS 协议选择，解决混合内容问题
 */

/**
 * 根据当前页面协议自动选择协议
 * 如果当前页面是 HTTPS，则使用 HTTPS；否则使用 HTTP
 */
export function getProtocol(): 'http:' | 'https:' {
  return window.location.protocol as 'http:' | 'https:';
}

/**
 * 智能修复 URL 协议
 * 策略：
 * 1. 如果环境变量明确设置了URL，使用环境变量的协议（不强制转换）
 * 2. 如果当前页面是HTTPS，但后端可能不支持HTTPS，允许回退到HTTP（通过环境变量控制）
 * 3. 默认情况下，如果当前页面是HTTPS，尝试使用HTTPS
 * 
 * @param url 原始 URL
 * @param forceProtocol 强制使用的协议（可选）
 * @returns 修复后的 URL
 */
export function fixUrlProtocol(url: string, forceProtocol?: 'http:' | 'https:'): string {
  // 如果强制指定了协议，使用强制协议
  if (forceProtocol) {
    return url.replace(/^https?:\/\//, `${forceProtocol}//`);
  }
  
  // 如果URL已经包含协议，检查是否需要转换
  if (url.startsWith('http://') || url.startsWith('https://')) {
    const isHTTPS = window.location.protocol === 'https:';
    const urlProtocol = url.startsWith('https://') ? 'https:' : 'http:';
    
    // 如果当前页面是HTTPS，但URL是HTTP，检查是否允许混合内容
    // 注意：浏览器默认会阻止HTTPS页面加载HTTP资源
    // 如果后端不支持HTTPS，我们需要保持HTTP（但会有混合内容警告）
    // 最佳实践：配置后端也支持HTTPS
    
    // 如果URL已经是HTTPS，保持HTTPS
    if (urlProtocol === 'https:') {
      return url;
    }
    
    // 如果当前页面是HTTPS但URL是HTTP，尝试转换为HTTPS
    // 但如果后端不支持HTTPS，这会导致连接失败
    // 所以这里保持原样，让浏览器处理（会显示混合内容警告）
    // 更好的方案是配置后端也支持HTTPS
    return url;
  }
  
  // 如果URL没有协议，添加当前页面协议
  const protocol = getProtocol();
  return `${protocol}//${url}`;
}

/**
 * 根据当前页面协议构建 URL
 * @param hostname 主机名（如 'localhost' 或 '192.168.1.100'）
 * @param port 端口号（如 '8000'）
 * @param path 路径（如 '/api/v1'）
 * @param useHTTPS 是否强制使用HTTPS（可选，默认根据当前页面协议）
 * @returns 完整的 URL
 */
export function buildUrl(hostname: string, port: string, path: string = '', useHTTPS?: boolean): string {
  // 如果明确指定了协议，使用指定协议
  // 否则根据当前页面协议选择
  const protocol = useHTTPS !== undefined 
    ? (useHTTPS ? 'https:' : 'http:')
    : getProtocol();
  const url = `${protocol}//${hostname}:${port}${path}`;
  return url;
}

/**
 * 获取 WebSocket 协议（ws:// 或 wss://）
 */
export function getWebSocketProtocol(): 'ws:' | 'wss:' {
  return window.location.protocol === 'https:' ? 'wss:' : 'ws:';
}

/**
 * 构建 WebSocket URL
 * @param hostname 主机名
 * @param port 端口号
 * @param path 路径
 * @returns WebSocket URL
 */
export function buildWebSocketUrl(hostname: string, port: string, path: string): string {
  const protocol = getWebSocketProtocol();
  return `${protocol}//${hostname}:${port}${path}`;
}

