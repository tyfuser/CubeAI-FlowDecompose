/**
 * API 客户端配置
 * 统一管理所有 API 请求
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.rubik-ai.com/v1';
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

