import { ActionPayload, MOCK_ACTIONS } from '../types';

// 动态获取 API 地址：根据当前页面的 hostname 和端口
function getApiBase(): string {
  const hostname = window.location.hostname;
  const port = '8080';
  const protocol = window.location.protocol;
  return `${protocol}//${hostname}:${port}`;
}

function getWsBase(): string {
  const hostname = window.location.hostname;
  const port = '8080';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${hostname}:${port}`;
}

const API_BASE = getApiBase();
const WS_BASE = getWsBase();

export class SessionService {
  private ws: WebSocket | null = null;
  private bc: BroadcastChannel | null = null;
  private interval: number | null = null;
  private isLocallyHosting = false;

  constructor(private sessionId: string) { }

  private static getBaseUrl() {
    // Robust way to get the base URL before the hash, working for http, file, and blob
    let href = window.location.href;
    const hashIndex = href.indexOf('#');
    let baseUrl = hashIndex !== -1 ? href.substring(0, hashIndex) : href;

    // 如果当前是 HTTP，但需要 HTTPS（摄像头访问），强制转换为 HTTPS
    // 检查是否是开发服务器的端口（3000）
    if (baseUrl.startsWith('http://') && window.location.port === '3000') {
      baseUrl = baseUrl.replace('http://', 'https://');
      console.log('🔄 自动将 URL 转换为 HTTPS:', baseUrl);
    }

    // 重要：将 localhost 替换为实际 IP 地址，以便手机访问
    // 手机无法访问 localhost（手机上的 localhost 是手机自己）
    if (baseUrl.includes('localhost') || baseUrl.includes('127.0.0.1')) {
      // 尝试从当前 URL 获取 IP，或使用 hostname
      const hostname = window.location.hostname;
      if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
        baseUrl = baseUrl.replace(/localhost|127\.0\.0\.1/g, hostname);
        console.log('🔄 将 localhost 替换为 IP 地址:', baseUrl);
      } else {
        // 如果无法获取 IP，尝试从网络接口获取
        // 注意：浏览器无法直接获取本机 IP，需要从服务器获取
        console.warn('⚠️  无法自动获取 IP 地址，二维码可能无法在手机上使用');
      }
    }

    return baseUrl;
  }

  /**
   * Creates a session. 
   * Strategy: Try to POST to backend. If fails, create local session.
   */
  static async createSession(): Promise<{ sessionId: string; joinUrl: string; isLocal: boolean }> {
    try {
      // Short timeout to detect backend
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1000);

      const res = await fetch(`${API_BASE}/session`, {
        method: 'POST',
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        // Construct joinUrl client-side to ensure it points to THIS frontend instance
        // rather than relying on what the server thinks the origin is.
        // 使用 getBaseUrl() 确保使用正确的协议（HTTPS）
        const joinUrl = `${SessionService.getBaseUrl()}#/mobile/${data.session_id}`;
        console.log('📱 生成的加入 URL:', joinUrl);
        return { sessionId: data.session_id, joinUrl, isLocal: false };
      }
    } catch (e) {
      console.warn('Backend unreachable. Using Local Demo Mode.');
    }

    // Fallback: Local Mode
    const sessionId = Math.random().toString(36).substring(2, 8).toUpperCase();
    const joinUrl = `${SessionService.getBaseUrl()}#/mobile/${sessionId}`;
    return { sessionId, joinUrl, isLocal: true };
  }

  /**
   * Starts broadcasting mock actions (Only used if isLocal = true)
   * This simulates the server "pumping" actions.
   */
  startLocalBroadcasting() {
    this.isLocallyHosting = true;
    this.bc = new BroadcastChannel(`session_${this.sessionId}`);
    let idx = 0;

    // Immediate first message
    this.broadcastLocal(idx++);

    this.interval = window.setInterval(() => {
      this.broadcastLocal(idx++);
    }, 1000);
  }

  private broadcastLocal(index: number) {
    if (!this.bc) return;
    const template = MOCK_ACTIONS[index % MOCK_ACTIONS.length];
    const payload = { ...template, timestamp: Date.now() };
    this.bc.postMessage(payload);
  }

  /**
   * Connects to a session stream (Server or Local)
   */
  connect(onAction: (a: ActionPayload) => void) {
    // Strategy: Try WS. If error, fall back to BroadcastChannel.
    try {
      console.log(`Attempting WS connection to ${WS_BASE}`);
      this.ws = new WebSocket(`${WS_BASE}/session/${this.sessionId}/stream`);

      this.ws.onopen = () => console.log('WS Connected');

      this.ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          onAction(data);
        } catch (e) { console.error('Parse error', e); }
      };

      this.ws.onerror = () => {
        console.warn('WS Failed. Switching to Local BroadcastChannel.');
        this.fallbackToLocal(onAction);
      };

      this.ws.onclose = () => {
        // If closed unexpectedly, we might want fallback? 
        // For now, if it closes, it stays closed.
      };

    } catch (e) {
      this.fallbackToLocal(onAction);
    }
  }

  private fallbackToLocal(onAction: (a: ActionPayload) => void) {
    // If we already fell back, don't do it again
    if (this.bc && !this.isLocallyHosting) return;

    console.log('Using Local BroadcastChannel');
    this.bc = new BroadcastChannel(`session_${this.sessionId}`);
    this.bc.onmessage = (ev) => onAction(ev.data);
  }

  disconnect() {
    if (this.interval) clearInterval(this.interval);
    if (this.ws) { this.ws.close(); this.ws = null; }
    if (this.bc) { this.bc.close(); this.bc = null; }
  }
}