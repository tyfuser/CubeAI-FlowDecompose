/**
 * 知识库相关 API 服务
 */

import apiClient, { ApiResponse } from './api';

// ===== 知识库条目 =====

export type KBCategory = 'hooks' | 'narrative' | 'style' | 'bgm' | 'fingerprints';

export interface KBItem {
  id: string;
  category: KBCategory;
  title: string;
  description: string;
  tags: string[];
  usageCount: number;
  rating: number;
  previewColor?: string;
  content?: string;
  examples?: string[];
}

export interface GetKBItemsParams {
  category?: KBCategory;
  search?: string;
  page?: number;
  limit?: number;
}

export interface KBItemsResponse {
  items: KBItem[];
  total: number;
  page: number;
  limit: number;
}

/**
 * 获取知识库条目列表
 */
export async function getKBItems(params?: GetKBItemsParams): Promise<KBItemsResponse> {
  const response = await apiClient.get<ApiResponse<KBItemsResponse>>('/knowledge/items', {
    params: {
      page: params?.page || 1,
      limit: params?.limit || 15,
      ...(params?.category && { category: params.category }),
      ...(params?.search && { search: params.search }),
    }
  });
  return response.data;
}

/**
 * 获取单个知识库条目详情
 */
export async function getKBItem(itemId: string): Promise<KBItem> {
  const response = await apiClient.get<ApiResponse<{ item: KBItem }>>(`/knowledge/items/${itemId}`);
  return response.data.item;
}

/**
 * 添加到收藏
 */
export async function bookmarkKBItem(itemId: string): Promise<void> {
  await apiClient.post(`/knowledge/items/${itemId}/bookmark`);
}

/**
 * 取消收藏
 */
export async function unbookmarkKBItem(itemId: string): Promise<void> {
  await apiClient.delete(`/knowledge/items/${itemId}/bookmark`);
}

