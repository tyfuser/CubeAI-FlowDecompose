# 🔌 API 兼容性说明

## 📊 后端 API 格式

前端已适配您的后端 API 格式！

---

## ✅ 支持的响应格式

前端响应拦截器现在支持**两种格式**：

### 格式 1：code 格式（您的后端）

```json
{
  "code": 0,           // 0 表示成功，非 0 表示失败
  "data": {            // 实际数据
    ...
  },
  "message": "成功"    // 可选的消息（失败时使用）
}
```

### 格式 2：success 格式（标准格式）

```json
{
  "success": true,
  "data": {
    ...
  },
  "error": {           // success: false 时存在
    "code": "ERROR_CODE",
    "message": "错误信息"
  }
}
```

**前端会自动识别并转换为统一格式！** ✨

---

## 🔄 视频分析完整流程

### 1. 创建分析任务

**请求**：
```http
POST /api/v1/analysis/create
Content-Type: application/json

{
  "url": "https://example.com/video.mp4",
  "platform": "auto"
}
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "id": "analysis_abc123",
    "analysisId": "analysis_abc123",  ← 前端轮询用这个
    "title": "视频标题",
    "viralFactors": [...],
    ...其他 VideoAnalysis 字段
  }
}
```

**前端处理**：
```typescript
const task = await createAnalysis({ url, platform: 'auto' });
// task.analysisId = "analysis_abc123"
```

---

### 2. 查询分析状态

**请求**：
```http
GET /api/v1/analysis/{analysisId}/status
```

**响应**（您的后端立即返回完成）：
```json
{
  "code": 0,
  "data": {
    "analysisId": "analysis_abc123",
    "status": "completed",    ← 立即完成！
    "progress": 100,
    "currentStep": "完成",
    "message": "分析完成"
  }
}
```

**前端处理**：
```typescript
const status = await getAnalysisStatus(analysisId);
if (status.status === 'completed') {
  // 立即获取结果
  const result = await getAnalysis(analysisId);
}
```

---

### 3. 获取分析结果

**请求**：
```http
GET /api/v1/analysis/{analysisId}
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "id": "analysis_abc123",
    "analysisId": "analysis_abc123",
    "title": "视频标题",
    "coverUrl": "https://...",
    "duration": 52,
    "viralFactors": [
      {
        "category": "视觉钩子",
        "description": "前3秒高饱和度画面切换",
        "intensity": 9
      }
    ],
    "rhythmData": [...],
    "radarData": [...],
    "hookScore": 85,
    "evaluationReport": {...},
    "hookDetails": {...},
    "editingStyle": {...},
    "audienceResponse": {...},
    "narrativeStructure": "AIDA"
  }
}
```

**前端处理**：
```typescript
const analysis = await getAnalysis(analysisId);
// analysis 是完整的 VideoAnalysis 对象
setAnalysis(analysis);
```

---

## 🎬 文件上传流程

### 1. 上传视频文件

**请求**：
```http
POST /api/v1/analysis/upload
Content-Type: multipart/form-data

file: <video_file>
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "filePath": "/uploads/videos/abc123.mp4",
    "fileName": "my_video.mp4",
    "fileSize": 45678900
  }
}
```

**前端处理**：
```typescript
const uploadResult = await uploadVideo(file);
// uploadResult.filePath = "/uploads/videos/abc123.mp4"

// 然后使用 filePath 创建分析
const task = await createAnalysis({
  url: uploadResult.filePath,  // 使用服务器路径
  platform: 'auto'
});
```

---

## 📋 Dashboard API

### 获取统计数据

**请求**：
```http
GET /api/v1/dashboard/stats
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "stats": [
      {
        "label": "总分析数",
        "value": "1,234",
        "icon": "BarChart3",
        "color": "text-indigo-400",
        "bg": "bg-indigo-500/10"
      },
      ...
    ]
  }
}
```

### 获取项目列表

**请求**：
```http
GET /api/v1/dashboard/projects?page=1&limit=10
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "projects": [
      {
        "id": "proj_001",
        "title": "项目名称",
        "thumbnail": "https://...",
        "timestamp": "2025-01-02T10:30:00Z",
        "type": "analysis",
        "score": 85,
        "status": "completed",
        "tags": ["爆款", "抖音"]
      },
      ...
    ],
    "total": 100,
    "page": 1,
    "limit": 10
  }
}
```

### 获取日程数据

**请求**：
```http
GET /api/v1/dashboard/schedule
```

**响应**：
```json
{
  "code": 0,
  "data": {
    "schedule": [
      { "day": "Mon", "intensity": 8 },
      { "day": "Tue", "intensity": 6 },
      ...
    ],
    "tasks": [
      { "label": "视频分析", "active": true, "color": "#6366f1" },
      ...
    ]
  }
}
```

---

## 🎭 镜头拆解 API（新功能）

这些 API 使用独立的基础 URL：`http://localhost:8000`

### 创建分析任务

**请求**：
```http
POST /v1/video-analysis/jobs
Content-Type: application/json

{
  "mode": "learn",
  "target_video": {
    "source": {
      "type": "file",
      "path": "/path/to/video.mp4"
    }
  },
  "options": {
    "frame_extract": {
      "fps": 2.0,
      "max_frames": 240
    },
    "llm": {
      "provider": "sophnet",
      "enabled_modules": ["camera_motion", "lighting", "color_grading"]
    }
  }
}
```

**响应**：
```json
{
  "job_id": "job_abc123",
  "status": "queued",
  "status_url": "/v1/video-analysis/jobs/job_abc123"
}
```

### 查询任务状态（轮询）

**请求**：
```http
GET /v1/video-analysis/jobs/{job_id}
```

**响应（运行中）**：
```json
{
  "job_id": "job_abc123",
  "status": "running",
  "progress": {
    "stage": "特征分析",
    "percent": 45.0,
    "message": "正在分析镜头 3/5..."
  },
  "partial_result": {
    "target": {
      "segments": [
        {
          "segment_id": "seg_0001",
          "start_ms": 0,
          "end_ms": 3500,
          "duration_ms": 3500,
          "analyzing": false,
          "features": [
            {
              "category": "camera_motion",
              "type": "close_up",
              "value": "特写",
              "confidence": 0.92
            }
          ]
        }
      ]
    }
  }
}
```

**响应（完成）**：
```json
{
  "job_id": "job_abc123",
  "status": "succeeded",
  "result": {
    "target": {
      "segments": [...]
    }
  }
}
```

---

## 🔧 响应拦截器工作原理

```typescript
// services/api.ts
apiClient.interceptors.response.use(
  (response) => {
    const responseData = response.data;
    
    // 检查 code 格式（您的后端）
    if ('code' in responseData) {
      if (responseData.code === 0) {
        // 成功：转换为标准格式
        return {
          success: true,
          data: responseData.data,
          timestamp: Date.now()
        };
      } else {
        // 失败：抛出错误
        throw new ApiError(
          responseData.message || '请求失败',
          responseData.code.toString()
        );
      }
    }
    
    // 检查 success 格式（标准格式）
    if ('success' in responseData) {
      if (!responseData.success) {
        throw new ApiError(
          responseData.error.message,
          responseData.error.code
        );
      }
      return responseData;
    }
    
    // 其他格式：直接返回
    return {
      success: true,
      data: responseData,
      timestamp: Date.now()
    };
  }
);
```

---

## 📝 数据类型映射

### VideoAnalysis 类型

```typescript
interface VideoAnalysis {
  id: string;                    // 分析ID
  analysisId?: string;           // 可选的 analysisId 字段
  title: string;                 // 视频标题
  coverUrl: string;              // 封面URL
  duration: number;              // 时长（秒）
  viralFactors: ViralFactor[];   // 爆款因素
  rhythmData: RhythmPoint[];     // 节奏数据
  radarData: RadarData[];        // 雷达图数据
  narrativeStructure: string;    // 叙事结构
  hookScore: number;             // 钩子分数
  evaluationReport: {            // 评估报告
    starRating: number;
    coreStrengths: string[];
    reusablePoints: string[];
  };
  hookDetails: {                 // 钩子详情
    visual: string;
    audio: string;
    text: string;
  };
  editingStyle: {                // 剪辑风格
    pacing: string;
    transitionType: string;
    colorPalette: string;
  };
  audienceResponse: {            // 观众反应
    sentiment: string;
    keyTriggers: string[];
  };
}
```

---

## ✅ 测试检查清单

### 视频分析流程
- [x] `POST /api/v1/analysis/create` 返回 `analysisId`
- [x] `GET /api/v1/analysis/{id}/status` 返回 `completed`
- [x] `GET /api/v1/analysis/{id}` 返回完整 `VideoAnalysis`
- [x] 前端正确处理 `code: 0` 格式
- [x] 错误处理（`code !== 0` 时）

### Dashboard 功能
- [ ] `GET /api/v1/dashboard/stats` 返回统计数据
- [ ] `GET /api/v1/dashboard/projects` 返回项目列表
- [ ] `GET /api/v1/dashboard/schedule` 返回日程数据

### 文件上传
- [ ] `POST /api/v1/analysis/upload` 上传成功返回 `filePath`
- [ ] 使用 `filePath` 创建分析任务

### 镜头拆解（新功能）
- [ ] `POST /v1/video-analysis/jobs` 创建任务
- [ ] `GET /v1/video-analysis/jobs/{id}` 轮询状态
- [ ] 流式输出 `partial_result`

---

## 🐛 错误处理

### 后端返回错误

```json
{
  "code": 1001,
  "message": "视频链接无效",
  "data": null
}
```

**前端处理**：
```typescript
try {
  const result = await createAnalysis({ url, platform });
} catch (error) {
  if (isApiError(error)) {
    console.error('错误代码:', error.code);    // "1001"
    console.error('错误信息:', error.message); // "视频链接无效"
    
    // 显示给用户
    setErrorToast({ 
      message: error.message, 
      type: 'error' 
    });
  }
}
```

---

## 📚 相关文档

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - 完整 API 规范
- **[ENV_CONFIG.md](ENV_CONFIG.md)** - 环境配置
- **[BACKEND_SETUP_REQUIRED.md](BACKEND_SETUP_REQUIRED.md)** - 后端配置指南

---

## 🎉 总结

✅ **前端已完全适配您的后端 API 格式！**

- ✅ 自动识别 `code: 0` 格式
- ✅ 自动转换为统一内部格式
- ✅ 支持两种响应格式
- ✅ 完整的错误处理
- ✅ 类型安全保证

**现在 create → status → get 的完整流程已经打通了！** 🎉

---

**开始测试完整的分析流程吧！** 🚀

