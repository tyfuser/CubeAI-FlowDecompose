/**
 * 视频分析相关 API 服务
 */

import apiClient, { ApiResponse } from './api';
import { VideoAnalysis } from '../types';

// ===== 上传视频文件 =====

export interface UploadVideoResponse {
  filePath: string;
  fileName: string;
  fileSize: number;
}

/**
 * 上传视频文件
 */
export async function uploadVideo(file: File): Promise<UploadVideoResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<ApiResponse<UploadVideoResponse>>(
    '/analysis/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

// ===== 发起视频分析 =====

export interface CreateAnalysisRequest {
  url: string;
  platform?: 'douyin' | 'red' | 'bilibili' | 'auto';
}

export interface CreateAnalysisResponse {
  analysisId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  estimatedTime: number;
}

/**
 * 发起视频分析
 */
export async function createAnalysis(data: CreateAnalysisRequest): Promise<CreateAnalysisResponse> {
  const response = await apiClient.post<ApiResponse<CreateAnalysisResponse>>(
    '/analysis/create',
    data
  );
  return response.data;
}

// ===== 获取分析结果 =====

export interface GetAnalysisResponse {
  analysis: VideoAnalysis;
}

/**
 * 获取分析结果
 */
export async function getAnalysis(analysisId: string): Promise<VideoAnalysis> {
  const response = await apiClient.get<ApiResponse<VideoAnalysis>>(
    `/analysis/${analysisId}`
  );
  // 后端直接返回 VideoAnalysis 数据在 data 字段中
  return response.data;
}

// ===== 获取分析状态 =====

export interface AnalysisStatusResponse {
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  message: string;
}

/**
 * 获取分析任务状态（用于轮询）
 */
export async function getAnalysisStatus(analysisId: string): Promise<AnalysisStatusResponse> {
  const response = await apiClient.get<ApiResponse<AnalysisStatusResponse>>(
    `/analysis/${analysisId}/status`
  );
  return response.data;
}

// ===== 轮询分析结果 =====

/**
 * 轮询分析结果直到完成
 * @param analysisId 分析任务 ID
 * @param onProgress 进度回调
 * @param maxAttempts 最大尝试次数
 * @param interval 轮询间隔（毫秒）
 */
export async function pollAnalysisResult(
  analysisId: string,
  onProgress?: (status: AnalysisStatusResponse) => void,
  maxAttempts: number = 60,
  interval: number = 2000
): Promise<VideoAnalysis> {
  let attempts = 0;

  const poll = async (): Promise<VideoAnalysis> => {
    if (attempts >= maxAttempts) {
      throw new Error('分析超时，请稍后再试');
    }

    attempts++;
    const status = await getAnalysisStatus(analysisId);

    if (onProgress) {
      onProgress(status);
    }

    if (status.status === 'completed') {
      return await getAnalysis(analysisId);
    }

    if (status.status === 'failed') {
      throw new Error(status.message || '分析失败');
    }

    // 继续轮询
    await new Promise(resolve => setTimeout(resolve, interval));
    return poll();
  };

  return poll();
}

