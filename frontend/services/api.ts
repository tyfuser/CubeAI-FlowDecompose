/**
 * API 客户端配置
 * 统一管理所有 API 请求
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// API 基础配置
// 注意：如果环境变量明确设置了URL，使用环境变量的协议（不强制转换）
// 这样可以避免HTTPS前端访问HTTP后端时的混合内容问题
// 最佳实践：配置后端也支持HTTPS，或使用反向代理
const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  
  // 调试日志
  if (typeof window !== 'undefined') {
    console.log('[API Config] VITE_API_BASE_URL:', envUrl);
    console.log('[API Config] Current location:', window.location.href);
  }
  
  if (envUrl) {
    // 如果环境变量设置了URL，直接使用（保持原有协议）
    // 如果后端不支持HTTPS，保持HTTP；如果支持HTTPS，使用HTTPS
    console.log('[API Config] Using env URL:', envUrl);
    return envUrl;
  }
  
  // 如果没有设置环境变量，默认使用当前hostname + HTTP（因为后端通常不支持HTTPS）
  // 这样可以避免HTTPS前端尝试访问不存在的HTTPS后端
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const defaultUrl = `http://${hostname}:8000/api/v1`;
    console.warn('[API Config] No VITE_API_BASE_URL set, using default:', defaultUrl);
    console.warn('[API Config] Please create .env file with: VITE_API_BASE_URL=http://YOUR_IP:8000/api/v1');
    return defaultUrl;
  }
  
  return 'https://api.rubik-ai.com/v1';
};

const API_BASE_URL = getApiBaseUrl();
console.log('[API Config] Final API_BASE_URL:', API_BASE_URL);
const API_VERSION = 'v1';
const REQUEST_TIMEOUT = 30000; // 30秒

// 通用响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  message?: string;
  timestamp: number;
}

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Version': API_VERSION,
  },
});

// 请求拦截器：添加认证 Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('rubik_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：统一处理响应和错误
apiClient.interceptors.response.use(
  (response) => {
    const responseData = response.data;
    
    // 兼容两种后端格式：
    // 格式1: { success: true, data: {...} }
    // 格式2: { code: 0, data: {...} }
    
    // 检查是否是 code 格式（用户的后端）
    if ('code' in responseData) {
      if (responseData.code === 0) {
        // 成功：返回标准格式
        return {
          success: true,
          data: responseData.data,
          timestamp: Date.now()
        };
      } else {
        // 失败：抛出错误
        return Promise.reject(new ApiError(
          responseData.message || responseData.msg || '请求失败',
          responseData.code?.toString() || 'UNKNOWN_ERROR',
          response.status,
          responseData.data
        ));
      }
    }
    
    // 检查是否是 success 格式（标准格式）
    if ('success' in responseData) {
      if (!responseData.success && responseData.error) {
        return Promise.reject(new ApiError(
          responseData.error.message,
          responseData.error.code,
          response.status,
          responseData.error.details
        ));
      }
      return responseData;
    }
    
    // 其他格式：直接返回
    return {
      success: true,
      data: responseData,
      timestamp: Date.now()
    };
  },
  (error: AxiosError<ApiResponse>) => {
    // 处理网络错误或其他错误
    if (error.response) {
      // 服务器返回了错误响应
      const status = error.response.status;
      const apiError = error.response.data?.error;
      
      // 401 未授权 - 跳转到登录
      if (status === 401) {
        localStorage.removeItem('rubik_token');
        localStorage.removeItem('rubik_auth');
        window.location.href = '/login';
        return Promise.reject(new ApiError('未授权，请重新登录', 'UNAUTHORIZED', status));
      }
      
      // 429 请求过于频繁
      if (status === 429) {
        return Promise.reject(new ApiError(
          apiError?.message || 'API 请求过于频繁，请稍后再试',
          'RATE_LIMIT_EXCEEDED',
          status
        ));
      }
      
      // 其他错误
      return Promise.reject(new ApiError(
        apiError?.message || '请求失败',
        apiError?.code || 'UNKNOWN_ERROR',
        status,
        apiError?.details
      ));
    } else if (error.request) {
      // 请求已发送但没有收到响应
      // 检查是否是混合内容错误（HTTPS前端访问HTTP后端）
      const isHTTPS = window.location.protocol === 'https:';
      const requestUrl = error.config?.url || '';
      const baseURL = error.config?.baseURL || '';
      const fullUrl = baseURL + requestUrl;
      
      if (isHTTPS && fullUrl.startsWith('http://')) {
        console.error('[API Error] 混合内容错误：HTTPS前端无法访问HTTP后端');
        console.error('[API Error] 请求URL:', fullUrl);
        console.error('[API Error] 解决方案：');
        console.error('[API Error] 1. 使用 HTTP 模式启动前端: FORCE_HTTP=true npm run dev');
        console.error('[API Error] 2. 或配置后端支持 HTTPS');
        console.error('[API Error] 3. 或访问 http://' + window.location.hostname + ':3000');
        
        return Promise.reject(new ApiError(
          '混合内容错误：HTTPS页面无法访问HTTP后端。请使用 HTTP 模式启动前端（FORCE_HTTP=true npm run dev）或访问 http://' + window.location.hostname + ':3000',
          'MIXED_CONTENT_ERROR',
          0
        ));
      }
      
      return Promise.reject(new ApiError(
        '网络连接失败，请检查网络',
        'NETWORK_ERROR',
        0
      ));
    } else {
      // 其他错误
      return Promise.reject(new ApiError(
        error.message || '请求配置错误',
        'REQUEST_ERROR',
        0
      ));
    }
  }
);

// 自定义错误类
export class ApiError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(message: string, code: string, status: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

// 导出 API 客户端
export default apiClient;

// 工具函数：处理 API 响应
export function unwrapApiResponse<T>(response: ApiResponse<T>): T {
  if (response.success && response.data !== undefined) {
    return response.data;
  }
  throw new Error(response.error?.message || '未知错误');
}

// 工具函数：判断是否为 API 错误
export function isApiError(error: any): error is ApiError {
  return error instanceof ApiError;
}

