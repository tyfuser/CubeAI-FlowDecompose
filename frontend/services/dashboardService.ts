/**
 * 仪表板相关 API 服务
 */

import apiClient, { ApiResponse } from './api';
import { ProjectSummary } from '../types';

// ===== 统计数据 =====

export interface DashboardStat {
  label: string;
  value: string;
  icon: string;
  color: string;
  bg: string;
}

export interface DashboardStatsResponse {
  stats: DashboardStat[];
}

/**
 * 获取仪表板统计数据
 */
export async function getDashboardStats(): Promise<DashboardStat[]> {
  const response = await apiClient.get<ApiResponse<DashboardStatsResponse>>('/dashboard/stats');
  return response.data.stats;
}

// ===== 项目列表 =====

export interface GetProjectsParams {
  page?: number;
  limit?: number;
  status?: string;
  sortBy?: 'timestamp' | 'score';
}

export interface ProjectsResponse {
  projects: ProjectSummary[];
  total: number;
  page: number;
  limit: number;
}

/**
 * 获取项目列表
 */
export async function getProjects(params?: GetProjectsParams): Promise<ProjectsResponse> {
  const response = await apiClient.get<ApiResponse<ProjectsResponse>>('/dashboard/projects', {
    params: {
      page: params?.page || 1,
      limit: params?.limit || 10,
      ...(params?.status && { status: params.status }),
      ...(params?.sortBy && { sortBy: params.sortBy }),
    }
  });
  return response.data;
}

// ===== 日程热力图 =====

export interface ScheduleDay {
  day: 'Mon' | 'Tue' | 'Wed' | 'Thu' | 'Fri' | 'Sat' | 'Sun';
  intensity: number;
}

export interface ScheduleTask {
  label: string;
  active: boolean;
  color: string;
}

export interface ScheduleResponse {
  schedule: ScheduleDay[];
  tasks: ScheduleTask[];
}

/**
 * 获取日程热力图数据
 */
export async function getSchedule(): Promise<ScheduleResponse> {
  const response = await apiClient.get<ApiResponse<ScheduleResponse>>('/dashboard/schedule');
  return response.data;
}

