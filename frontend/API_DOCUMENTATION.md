# 魔方 AI - 前端 API 接口文档

> **版本**: v1.0.0  
> **最后更新**: 2025-01-02  


---

## 📋 目录

1. [认证相关](#1-认证相关)
2. [仪表板数据](#2-仪表板数据)
3. [视频分析](#3-视频分析)
4. [案例探索](#4-案例探索)
5. [知识库](#5-知识库)
6. [脚本生成](#6-脚本生成)
7. [视频转幻灯片](#7-视频转幻灯片)
8. [用户管理](#8-用户管理)

---

## 通用说明

### 请求头 (Headers)

```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer {access_token}",
  "X-API-Version": "v1"
}
```

### 通用响应格式

**成功响应**:
```typescript
{
  "success": true,
  "data": any,          // 实际数据
  "message": string,    // 提示信息（可选）
  "timestamp": number   // 时间戳
}
```

**错误响应**:
```typescript
{
  "success": false,
  "error": {
    "code": string,      // 错误码，如 "INVALID_URL"
    "message": string,   // 错误描述
    "details": any       // 详细信息（可选）
  },
  "timestamp": number
}
```

### HTTP 状态码

- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未授权
- `403` - 权限不足
- `404` - 资源不存在
- `429` - 请求过于频繁
- `500` - 服务器错误

---

## 1. 认证相关

### 1.1 用户登录

**接口**: `POST /auth/login`

**请求体**:
```typescript
{
  "email": string,      // 邮箱
  "password": string    // 密码
}
```

**响应数据**:
```typescript
{
  "user": {
    "id": string,
    "email": string,
    "name": string,
    "avatar": string,
    "subscription": "free" | "pro" | "enterprise"
  },
  "token": string,        // JWT Token
  "expiresIn": number     // 过期时间（秒）
}
```





---

## 2. 仪表板数据

### 2.1 获取统计数据

**接口**: `GET /dashboard/stats`

**响应数据**:
```typescript
{
  "stats": [
    {
      "label": string,        // "已分析视频"
      "value": string,        // "128"
      "icon": string,         // 图标名称
      "color": string,        // 颜色类名
      "bg": string            // 背景类名
    }
  ]
}
```

**示例**:
```json
{
  "success": true,
  "data": {
    "stats": [
      {
        "label": "已分析视频",
        "value": "128",
        "icon": "FileVideo",
        "color": "text-blue-400",
        "bg": "bg-blue-400/10"
      },
      {
        "label": "爆款基因库",
        "value": "2,450",
        "icon": "Zap",
        "color": "text-yellow-400",
        "bg": "bg-yellow-400/10"
      },
      {
        "label": "节省创作时长",
        "value": "340h",
        "icon": "Timer",
        "color": "text-green-400",
        "bg": "bg-green-400/10"
      },
      {
        "label": "平均爆款分",
        "value": "88.5",
        "icon": "TrendingUp",
        "color": "text-purple-400",
        "bg": "bg-purple-400/10"
      }
    ]
  }
}
```

### 2.2 获取项目列表

**接口**: `GET /dashboard/projects`

**查询参数**:
```typescript
{
  page?: number,          // 页码，默认 1
  limit?: number,         // 每页数量，默认 10
  status?: ProjectStatus, // 筛选状态
  sortBy?: "timestamp" | "score" // 排序方式
}
```

**响应数据**:
```typescript
{
  "projects": ProjectSummary[],
  "total": number,
  "page": number,
  "limit": number
}
```

**ProjectSummary 类型定义**:
```typescript
interface ProjectSummary {
  id: string,
  title: string,
  thumbnail: string,        // 封面图 URL
  timestamp: string,        // "10分钟前" 或 ISO 时间
  type: string,            // "穿搭复刻"
  score: number,           // 0-100
  status: "analyzing" | "completed" | "draft" | "failed",
  tags: string[],          // ["穿搭", "夏季"]
  radarData?: {
    subject: string,
    value: number,
    fullMark: number
  }[]
}
```

**示例**:
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "1",
        "title": "2024夏季穿搭爆款拆解",
        "thumbnail": "https://cdn.rubik-ai.com/thumbnails/xxx.jpg",
        "timestamp": "10分钟前",
        "type": "穿搭复刻",
        "score": 94,
        "status": "completed",
        "tags": ["穿搭", "夏季"]
      }
    ],
    "total": 128,
    "page": 1,
    "limit": 10
  }
}






### 2.5 获取日程热力图

**接口**: `GET /dashboard/schedule`

**响应数据**:
```typescript
{
  "schedule": [
    {
      "day": "Mon" | "Tue" | "Wed" | "Thu" | "Fri" | "Sat" | "Sun",
      "intensity": number       // 0-100
    }
  ],
  "tasks": [
    {
      "label": string,          // "待解析: 3个数码类视频"
      "active": boolean,
      "color": string           // "bg-indigo-500"
    }
  ]
}
```

---

## 3. 视频分析

### 3.1 上传视频文件（推荐）

**接口**: `POST /analysis/upload`

**请求体**: `multipart/form-data`
```typescript
{
  "file": File              // 视频文件
}
```

**支持的视频格式**:
- MP4, MOV, AVI, MKV, WEBM
- 最大文件大小: 500MB

**响应数据**:
```typescript
{
  "filePath": string,       // 服务器上的文件路径
  "fileName": string,       // 原始文件名
  "fileSize": number        // 文件大小（字节）
}
```

**示例**:
```json
{
  "success": true,
  "data": {
    "filePath": "/uploads/videos/1234567890_video.mp4",
    "fileName": "my_video.mp4",
    "fileSize": 52428800
  }
}
```

### 3.2 发起视频分析

**接口**: `POST /analysis/create`

**请求体**:
```typescript
{
  "url": string,              // 视频链接或上传后的文件路径
  "platform": "douyin" | "red" | "bilibili" | "auto" // 平台，auto 自动识别
}
```

**说明**:
- 如果使用上传功能，`url` 参数应该传入上传接口返回的 `filePath`
- 也可以直接传入视频平台链接（抖音、小红书等）
- 或者传入服务器本地文件的绝对路径

**响应数据**:
```typescript
{
  "analysisId": string,       // 分析任务 ID
  "status": "queued" | "processing" | "completed" | "failed",
  "estimatedTime": number     // 预计完成时间（秒）
}
```

### 3.3 获取分析结果

**接口**: `GET /analysis/{analysisId}`

**响应数据**: `VideoAnalysis`

```typescript
interface VideoAnalysis {
  id: string,
  title: string,
  coverUrl: string,
  duration: number,           // 视频时长（秒）
  
  // 爆款因素分析
  viralFactors: ViralFactor[],
  
  // 节奏数据（用于图表）
  rhythmData: RhythmPoint[],
  
  // 六维雷达数据
  radarData: {
    subject: string,          // "钩子强度"
    value: number,            // 85
    fullMark: number          // 100
  }[],
  
  // 叙事结构描述
  narrativeStructure: string, // "经典的 AIDA 营销结构"
  
  // 钩子分数
  hookScore: number,          // 0-100
  
  // 评估报告
  evaluationReport: {
    starRating: number,       // 1-5
    coreStrengths: string[],  // 核心优势
    reusablePoints: string[]  // 可复用点
  },
  
  // 钩子详情
  hookDetails: {
    visual: string,           // 视觉钩子描述
    audio: string,            // 音频钩子描述
    text: string              // 文案钩子描述
  },
  
  // 剪辑风格
  editingStyle: {
    pacing: string,           // "极速" | "舒缓" | "适中"
    transitionType: string,   // "硬切" | "叠化" | "遮罩转场"
    colorPalette: string      // "赛博朋克" | "复古温暖" 等
  },
  
  // 受众反馈
  audienceResponse: {
    sentiment: string,        // "极度兴奋" | "平静" | "好奇"
    keyTriggers: string[]     // ["猎奇", "认同"]
  }
}
```

**ViralFactor 类型**:
```typescript
interface ViralFactor {
  category: string,           // "视觉钩子"
  description: string,        // 详细描述
  intensity: number           // 强度 1-10
}
```

**RhythmPoint 类型**:
```typescript
interface RhythmPoint {
  time: number,               // 时间点（秒）
  intensity: number,          // 强度 0-100
  label?: string              // 标签（可选）
}
```

**完整示例**:
```json
{
  "success": true,
  "data": {
    "id": "76681",
    "title": "2024夏季穿搭爆款拆解",
    "coverUrl": "https://cdn.rubik-ai.com/covers/xxx.jpg",
    "duration": 45,
    "viralFactors": [
      {
        "category": "视觉钩子",
        "description": "前3秒高饱和度画面切换，建立强烈视觉冲击",
        "intensity": 9
      },
      {
        "category": "音频卡点",
        "description": "节奏感极强的BGM配合画面转场",
        "intensity": 8
      }
    ],
    "rhythmData": [
      { "time": 0, "intensity": 95, "label": "Hook" },
      { "time": 3, "intensity": 70 },
      { "time": 6, "intensity": 60 }
    ],
    "radarData": [
      { "subject": "钩子强度", "value": 85, "fullMark": 100 },
      { "subject": "情绪张力", "value": 70, "fullMark": 100 },
      { "subject": "视觉冲击", "value": 90, "fullMark": 100 },
      { "subject": "叙事逻辑", "value": 65, "fullMark": 100 },
      { "subject": "转化潜力", "value": 80, "fullMark": 100 },
      { "subject": "创新指数", "value": 75, "fullMark": 100 }
    ],
    "narrativeStructure": "经典的 AIDA 营销结构",
    "hookScore": 94,
    "evaluationReport": {
      "starRating": 5,
      "coreStrengths": ["节奏感强", "视觉冲击力大", "叙事逻辑清晰"],
      "reusablePoints": ["3秒黄金钩子", "结尾反转话术", "音乐卡点技巧"]
    },
    "hookDetails": {
      "visual": "黑白变彩色的瞬间转换，搭配近景人物表情特写",
      "audio": "心跳音效叠加低音炮，配合节奏点",
      "text": "你绝对想不到最后的反转..."
    },
    "editingStyle": {
      "pacing": "极速",
      "transitionType": "遮罩转场",
      "colorPalette": "赛博朋克（高饱和度蓝紫色调）"
    },
    "audienceResponse": {
      "sentiment": "极度兴奋",
      "keyTriggers": ["猎奇", "认同", "震惊"]
    }
  }
}
```

### 3.4 获取分析任务状态

**接口**: `GET /analysis/{analysisId}/status`

**响应数据**:
```typescript
{
  "status": "queued" | "processing" | "completed" | "failed",
  "progress": number,         // 0-100
  "currentStep": string,      // "提取关键帧素材"
  "message": string           // 状态描述
}
```


## 5. 知识库（其实就是根据历史项目数据总结的）

### 5.1 获取知识库条目

**接口**: `GET /knowledge/items`

**查询参数**:
```typescript
{
  category?: "hooks" | "narrative" | "style" | "bgm" | "fingerprints",
  search?: string,            // 搜索关键词
  page?: number,
  limit?: number
}
```

**响应数据**:
```typescript
{
  "items": KBItem[],
  "total": number,
  "page": number,
  "limit": number
}
```

**KBItem 类型**:
```typescript
interface KBItem {
  id: string,
  category: "hooks" | "narrative" | "style" | "bgm" | "fingerprints",
  title: string,
  description: string,
  tags: string[],
  usageCount: number,         // 使用次数
  rating: number,             // 评分 0-5
  previewColor?: string,      // 预览卡片渐变色
  content?: string,           // 详细内容（可选）
  examples?: string[]         // 示例列表（可选）
}
```

**示例**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "1",
        "category": "hooks",
        "title": "视觉反差钩子",
        "description": "前0.5秒展示极端对比画面，迅速建立视觉张力。",
        "tags": ["高点击", "强反转", "生活"],
        "usageCount": 1240,
        "rating": 4.9,
        "previewColor": "from-orange-500 to-red-500"
      }
    ],
    "total": 45,
    "page": 1,
    "limit": 15
  }
}
```

### 5.2 获取单个知识库条目详情

**接口**: `GET /knowledge/items/{itemId}`

### 5.3 添加到收藏

**接口**: `POST /knowledge/items/{itemId}/bookmark`

---


## 8. 用户管理

### 8.1 获取用户信息

**接口**: `GET /user/profile`

**响应数据**:
```typescript
{
  "id": string,
  "email": string,
  "name": string,
  "avatar": string,
  "subscription": {
    "plan": "free" | "pro" | "enterprise",
    "expiresAt": string,      // ISO 时间
    "features": string[]
  },
  "usage": {
    "videosAnalyzed": number,
    "scriptsGenerated": number,
    "quota": {
      "daily": number,
      "remaining": number
    }
  },
  "createdAt": string,
  "lastLoginAt": string
}
```

### 8.2 更新用户信息

**接口**: `PATCH /user/profile`

**请求体**:
```typescript
{
  "name": string,
  "avatar": string
}
```

### 8.3 获取用户配额信息

**接口**: `GET /user/quota`

**响应数据**:
```typescript
{
  "plan": string,
  "quota": {
    "daily": number,
    "used": number,
    "remaining": number,
    "resetAt": string         // ISO 时间
  },
  "features": {
    "videoAnalysis": boolean,
    "scriptGeneration": boolean,
    "slideshow": boolean,
    "aiChat": boolean
  }
}
```

---

## 附录

### A. 枚举类型定义

```typescript
// 项目状态
type ProjectStatus = "analyzing" | "completed" | "draft" | "failed";

// 创作策略
type CreationStrategy = "remake" | "explainer" | "review" | "collection" | "mashup";

// 目标平台
type TargetPlatform = "douyin" | "red" | "bilibili";

// 知识库分类
type KBCategory = "hooks" | "narrative" | "style" | "bgm" | "fingerprints";

// 幻灯片布局类型
type SlideLayoutType = "title" | "chapter" | "content";
```

### B. 错误码列表

| 错误码 | 描述 |
|--------|------|
| `INVALID_URL` | 视频链接格式不正确 |
| `UNSUPPORTED_PLATFORM` | 不支持的平台 |
| `ANALYSIS_FAILED` | 分析失败 |
| `QUOTA_EXCEEDED` | 配额已用完 |
| `INVALID_TOKEN` | Token 无效或过期 |
| `RESOURCE_NOT_FOUND` | 资源不存在 |
| `GENERATION_FAILED` | 生成失败 |
| `FILE_TOO_LARGE` | 文件过大（超过 500MB） |
| `UNSUPPORTED_FORMAT` | 不支持的文件格式（仅支持 MP4/MOV/AVI/MKV/WEBM） |
| `UPLOAD_FAILED` | 文件上传失败 |

### C. Webhook 事件（可选）

如果后端支持 Webhook，可用于异步通知：

**事件类型**:
- `analysis.completed` - 分析完成
- `analysis.failed` - 分析失败
- `script.generated` - 脚本生成完成
- `slideshow.completed` - 幻灯片生成完成

**Payload 格式**:
```typescript
{
  "event": string,            // 事件类型
  "timestamp": number,
  "data": {
    "id": string,             // 资源 ID
    "status": string,
    // ... 其他数据
  }
}
```

---

## 开发指南

### 前端调用示例

#### 使用 Fetch API

```typescript
// 示例：获取仪表板统计数据
async function getDashboardStats() {
  const response = await fetch('https://api.rubik-ai.com/v1/dashboard/stats', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'X-API-Version': 'v1'
    }
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  
  const result = await response.json();
  
  if (!result.success) {
    throw new Error(result.error.message);
  }
  
  return result.data;
}
```

#### 使用 Axios

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.rubik-ai.com/v1',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Version': 'v1'
  }
});

// 请求拦截器：添加 Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理错误
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 跳转到登录页
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 使用示例
const stats = await api.get('/dashboard/stats');
```

### 建议的 API Service 结构

建议在前端创建以下服务文件：

```
/services
  ├── api.ts          # API 客户端配置
  ├── auth.ts         # 认证相关 API
  ├── dashboard.ts    # 仪表板 API
  ├── analysis.ts     # 视频分析 API
  ├── discovery.ts    # 案例探索 API
  ├── knowledge.ts    # 知识库 API
  ├── script.ts       # 脚本生成 API
  ├── slideshow.ts    # 幻灯片 API
  └── user.ts         # 用户管理 API
```

---

## 更新日志

### v1.0.0 (2025-01-02)
- 初始版本
- 定义所有核心接口
- 完整的数据模型定义

---

**文档维护**: 前端团队  
**联系方式**: dev@rubik-ai.com  
**问题反馈**: https://github.com/rubik-ai/frontend/issues

