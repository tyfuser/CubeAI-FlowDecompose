# 前端集成指南 - 视频拆解分析功能

本文档用于帮助其他项目集成视频拆解分析功能，保持自己的UI风格同时接入完整的分析能力。

---

## 📋 目录

- [核心功能概述](#核心功能概述)
- [API接口规范](#api接口规范)
- [前端实现流程](#前端实现流程)
- [数据结构说明](#数据结构说明)
- [UI组件建议](#ui组件建议)
- [完整示例代码](#完整示例代码)

---

## 🎯 核心功能概述

### 主要功能
1. **视频上传** - 支持本地文件上传
2. **异步分析** - 提交任务后轮询状态
3. **实时进度** - 显示分析进度和阶段
4. **结果展示** - 时间轴方式展示镜头拆解结果
5. **详情查看** - 每个镜头的详细特征分析
6. **历史记录** - 查看和管理历史分析任务

### 工作流程
```
上传视频 → 创建Job → 轮询状态 → 获取结果 → 展示时间轴
```

---

## 🔌 API接口规范

### 基础配置
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### 1. 创建分析任务

**接口**: `POST /v1/video-analysis/jobs`

**请求体**:
```json
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
      "enabled_modules": [
        "camera_motion",
        "lighting",
        "color_grading"
      ]
    }
  }
}
```

**响应**:
```json
{
  "job_id": "job_abc123",
  "status": "queued",
  "status_url": "/v1/video-analysis/jobs/job_abc123"
}
```

### 2. 查询任务状态

**接口**: `GET /v1/video-analysis/jobs/{job_id}`

**响应（运行中）**:
```json
{
  "job_id": "job_abc123",
  "mode": "learn",
  "status": "running",
  "progress": {
    "stage": "场景检测",
    "percent": 35.0,
    "message": "正在检测场景..."
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

**响应（完成）**:
```json
{
  "job_id": "job_abc123",
  "status": "succeeded",
  "result": {
    "target": {
      "segments": [
        {
          "segment_id": "seg_0001",
          "start_ms": 0,
          "end_ms": 3500,
          "duration_ms": 3500,
          "features": [
            {
              "category": "camera_motion",
              "type": "close_up",
              "value": "特写",
              "confidence": 0.92,
              "detailed_description": {
                "summary": "使用特写镜头突出主体细节",
                "technical_terms": ["特写", "景别"],
                "purpose": "强调情感表达"
              }
            },
            {
              "category": "lighting",
              "type": "three_point",
              "value": "三点布光",
              "confidence": 0.88
            },
            {
              "category": "color_grading",
              "type": "warm_tones",
              "value": "暖色调",
              "confidence": 0.85
            }
          ]
        }
      ]
    }
  }
}
```

### 3. 获取历史记录

**接口**: `GET /v1/video-analysis/history?limit=50`

**响应**:
```json
[
  {
    "job_id": "job_abc123",
    "title": "产品宣传片分析",
    "status": "succeeded",
    "learning_points": [
      "使用了5个特写镜头增强情感",
      "采用三点布光突出主体",
      "暖色调营造温馨氛围"
    ],
    "segment_count": 8,
    "duration_sec": 45.5,
    "thumbnail_url": "/data/jobs/job_abc123/thumbnail.jpg",
    "created_at": "2025-01-02T10:30:00Z"
  }
]
```

### 4. 删除任务

**接口**: `DELETE /v1/video-analysis/jobs/{job_id}`

**响应**:
```json
{
  "success": true,
  "message": "Job job_abc123 已删除",
  "job_id": "job_abc123"
}
```

---

## 💻 前端实现流程

### 核心流程代码

```javascript
// ========== 状态管理 ==========
const state = {
    currentJobId: null,
    analysisResult: null,
    isPolling: false
};

// ========== 1. 创建分析任务 ==========
async function createAnalysisJob(videoFile, options = {}) {
    const requestBody = {
        mode: "learn",
        target_video: {
            source: {
                type: "file",
                path: videoFile.path || `/uploads/${videoFile.name}`
            }
        },
        options: {
            frame_extract: {
                fps: options.fps || 2.0,
                max_frames: options.maxFrames || 240
            },
            llm: {
                provider: "sophnet",
                enabled_modules: options.modules || [
                    "camera_motion",
                    "lighting", 
                    "color_grading"
                ]
            }
        }
    };
    
    const response = await fetch(`${API_BASE_URL}/v1/video-analysis/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    });
    
    const data = await response.json();
    state.currentJobId = data.job_id;
    
    return data.job_id;
}

// ========== 2. 轮询任务状态 ==========
async function pollJobStatus(jobId, onProgress, onComplete, onError) {
    const maxAttempts = 120; // 最多2分钟
    let attempts = 0;
    
    state.isPolling = true;
    
    while (attempts < maxAttempts && state.isPolling) {
        try {
            const response = await fetch(
                `${API_BASE_URL}/v1/video-analysis/jobs/${jobId}`
            );
            const data = await response.json();
            
            if (data.status === 'succeeded') {
                state.analysisResult = data.result;
                onComplete(data.result);
                break;
            } 
            else if (data.status === 'failed') {
                onError(data.error);
                break;
            } 
            else if (data.status === 'running') {
                // 更新进度
                if (data.progress) {
                    onProgress({
                        percent: data.progress.percent,
                        message: data.progress.message,
                        stage: data.progress.stage
                    });
                }
                
                // 如果有部分结果，可以实时显示
                if (data.partial_result) {
                    onProgress({
                        partialResult: data.partial_result
                    });
                }
            }
            
            await sleep(1000); // 等待1秒
            attempts++;
            
        } catch (error) {
            onError({ message: error.message });
            break;
        }
    }
    
    state.isPolling = false;
    
    if (attempts >= maxAttempts) {
        onError({ message: '分析超时' });
    }
}

// 停止轮询
function stopPolling() {
    state.isPolling = false;
}

// ========== 3. 完整分析流程 ==========
async function analyzeVideo(videoFile, options = {}) {
    try {
        // 显示加载界面
        showLoading();
        
        // 创建任务
        const jobId = await createAnalysisJob(videoFile, options);
        
        // 轮询状态
        await pollJobStatus(
            jobId,
            // 进度回调
            (progress) => {
                if (progress.percent !== undefined) {
                    updateProgress(progress.percent, progress.message);
                }
                if (progress.partialResult) {
                    // 可选：实时显示部分结果
                    updatePartialTimeline(progress.partialResult);
                }
            },
            // 完成回调
            (result) => {
                hideLoading();
                displayTimeline(result);
            },
            // 错误回调
            (error) => {
                hideLoading();
                showError(error.message);
            }
        );
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// ========== 工具函数 ==========
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
```

---

## 📊 数据结构说明

### Segment 结构
```typescript
interface Segment {
    segment_id: string;           // 片段ID
    start_ms: number;              // 开始时间（毫秒）
    end_ms: number;                // 结束时间（毫秒）
    duration_ms: number;           // 时长（毫秒）
    analyzing?: boolean;           // 是否正在分析
    features: Feature[];           // 特征列表
}
```

### Feature 结构
```typescript
interface Feature {
    category: string;              // 类别：camera_motion/lighting/color_grading
    type: string;                  // 类型：具体特征标识
    value: string;                 // 显示值：中文描述
    confidence: number;            // 置信度：0-1
    detailed_description?: {       // 详细描述（可选）
        summary: string;           // 总结
        technical_terms: string[]; // 专业术语
        purpose: string;           // 用途/目的
        parameters?: object;       // 技术参数
    };
}
```

### 特征类别说明

#### camera_motion（运镜）
常见类型：
- `close_up`: 特写
- `medium_shot`: 中景
- `wide_shot`: 全景
- `pan_left`/`pan_right`: 左/右摇
- `tilt_up`/`tilt_down`: 上/下摇
- `zoom_in`/`zoom_out`: 推/拉
- `dolly_in`/`dolly_out`: 移动推/拉
- `tracking_shot`: 跟镜

#### lighting（光线）
常见类型：
- `three_point`: 三点布光
- `key_light`: 主光
- `fill_light`: 补光
- `back_light`: 背光
- `low_key`: 低调光
- `high_key`: 高调光
- `natural_light`: 自然光

#### color_grading（调色）
常见类型：
- `warm_tones`: 暖色调
- `cool_tones`: 冷色调
- `high_contrast`: 高对比
- `low_contrast`: 低对比
- `desaturated`: 去饱和
- `vibrant`: 鲜艳

---

## 🎨 UI组件建议

### 1. 上传组件
```html
<!-- 视频上传区 -->
<div class="video-upload">
    <input type="file" accept="video/*" id="videoInput" />
    <div class="upload-area">
        <p>拖拽视频文件或点击上传</p>
        <p class="hint">支持 MP4, MOV, AVI 格式</p>
    </div>
</div>

<!-- 分析选项 -->
<div class="analysis-options">
    <label>
        抽帧率 (fps):
        <input type="number" value="2" min="0.5" max="10" step="0.5" />
    </label>
    <label>
        最大帧数:
        <input type="number" value="240" min="10" max="1000" />
    </label>
    
    <label>
        <input type="checkbox" checked /> 运镜分析
    </label>
    <label>
        <input type="checkbox" checked /> 光线分析
    </label>
    <label>
        <input type="checkbox" checked /> 调色分析
    </label>
</div>

<button onclick="startAnalysis()">开始分析</button>
```

### 2. 进度组件
```html
<!-- 加载状态 -->
<div class="loading-panel" id="loadingPanel" style="display:none;">
    <div class="spinner"></div>
    <h3>分析中...</h3>
    <p id="progressMessage">准备中...</p>
    <div class="progress-bar">
        <div class="progress-fill" id="progressFill" style="width:0%;"></div>
    </div>
    <p id="progressPercent">0%</p>
</div>
```

```javascript
function updateProgress(percent, message) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressPercent').textContent = 
        Math.round(percent) + '%';
    document.getElementById('progressMessage').textContent = message;
}
```

### 3. 时间轴组件（核心）

**HTML结构**:
```html
<div class="timeline-container">
    <!-- 时间标尺 -->
    <div class="timeline-ruler" id="timelineRuler"></div>
    
    <!-- 视频预览 -->
    <div class="video-preview">
        <video id="previewVideo" controls></video>
    </div>
    
    <!-- 片段轨道 -->
    <div class="track">
        <div class="track-header">
            <span>📹</span>
            <span>镜头片段</span>
        </div>
        <div class="track-content" id="segmentsTrack"></div>
    </div>
    
    <!-- 运镜轨道 -->
    <div class="track">
        <div class="track-header">
            <span>🎥</span>
            <span>运镜</span>
        </div>
        <div class="track-content" id="cameraTrack"></div>
    </div>
    
    <!-- 光线轨道 -->
    <div class="track">
        <div class="track-header">
            <span>💡</span>
            <span>光线</span>
        </div>
        <div class="track-content" id="lightingTrack"></div>
    </div>
    
    <!-- 调色轨道 -->
    <div class="track">
        <div class="track-header">
            <span>🎨</span>
            <span>调色</span>
        </div>
        <div class="track-content" id="colorTrack"></div>
    </div>
</div>
```

**时间轴渲染逻辑**:
```javascript
function displayTimeline(result) {
    const segments = result.target.segments;
    const totalDuration = segments[segments.length - 1].end_ms;
    
    // 渲染时间标尺
    renderTimeRuler(totalDuration);
    
    // 渲染各轨道
    renderSegmentsTrack(segments, totalDuration);
    renderFeatureTrack(segments, totalDuration, 'camera_motion', 
                       document.getElementById('cameraTrack'));
    renderFeatureTrack(segments, totalDuration, 'lighting', 
                       document.getElementById('lightingTrack'));
    renderFeatureTrack(segments, totalDuration, 'color_grading', 
                       document.getElementById('colorTrack'));
}

function renderSegmentsTrack(segments, totalDuration) {
    const container = document.getElementById('segmentsTrack');
    container.innerHTML = '';
    
    segments.forEach(segment => {
        const div = document.createElement('div');
        div.className = 'segment';
        
        // 计算位置和宽度（百分比）
        const left = (segment.start_ms / totalDuration) * 100;
        const width = (segment.duration_ms / totalDuration) * 100;
        
        div.style.left = left + '%';
        div.style.width = width + '%';
        
        div.innerHTML = `
            <div class="segment-label">${segment.segment_id}</div>
            <div class="segment-duration">
                ${(segment.duration_ms / 1000).toFixed(1)}s
            </div>
        `;
        
        // 点击显示详情
        div.onclick = () => showSegmentDetail(segment);
        
        container.appendChild(div);
    });
}

function renderFeatureTrack(segments, totalDuration, category, container) {
    container.innerHTML = '';
    
    segments.forEach(segment => {
        const features = segment.features.filter(f => f.category === category);
        
        features.forEach(feature => {
            const div = document.createElement('div');
            div.className = `segment feature-${category}`;
            
            const left = (segment.start_ms / totalDuration) * 100;
            const width = (segment.duration_ms / totalDuration) * 100;
            
            div.style.left = left + '%';
            div.style.width = width + '%';
            
            div.innerHTML = `
                <div class="feature-type">${feature.type}</div>
                <div class="feature-value">${feature.value}</div>
                <div class="feature-confidence">
                    ${Math.round(feature.confidence * 100)}%
                </div>
            `;
            
            div.onclick = () => showFeatureDetail(feature, segment);
            
            container.appendChild(div);
        });
    });
}

function renderTimeRuler(totalDuration) {
    const ruler = document.getElementById('timelineRuler');
    ruler.innerHTML = '';
    
    const intervals = 10;
    for (let i = 0; i <= intervals; i++) {
        const time = (totalDuration / intervals) * i;
        const mark = document.createElement('div');
        mark.className = 'time-mark';
        mark.style.left = (i / intervals) * 100 + '%';
        mark.textContent = formatTime(time);
        ruler.appendChild(mark);
    }
}

function formatTime(ms) {
    const seconds = ms / 1000;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds % 1) * 1000);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`;
}
```

### 4. 详情面板
```html
<div class="detail-panel" id="detailPanel">
    <div class="detail-header">
        <h3>镜头详细分析</h3>
        <button onclick="closeDetail()">×</button>
    </div>
    <div class="detail-content" id="detailContent">
        <!-- 动态内容 -->
    </div>
</div>
```

```javascript
function showSegmentDetail(segment) {
    const panel = document.getElementById('detailPanel');
    const content = document.getElementById('detailContent');
    
    let html = `
        <div class="detail-section">
            <h4>📹 镜头信息</h4>
            <p>片段ID: ${segment.segment_id}</p>
            <p>时间: ${formatTime(segment.start_ms)} - ${formatTime(segment.end_ms)}</p>
            <p>时长: ${(segment.duration_ms / 1000).toFixed(2)}秒</p>
        </div>
    `;
    
    // 按类别分组显示特征
    const categories = {
        'camera_motion': '运镜分析',
        'lighting': '光线分析',
        'color_grading': '调色分析'
    };
    
    for (const [category, title] of Object.entries(categories)) {
        const features = segment.features.filter(f => f.category === category);
        
        if (features.length > 0) {
            html += `<div class="detail-section"><h4>${title}</h4>`;
            
            features.forEach(feature => {
                html += `
                    <div class="feature-detail">
                        <div class="feature-badge">${feature.value}</div>
                        <div class="feature-confidence">
                            置信度: ${Math.round(feature.confidence * 100)}%
                        </div>
                        ${feature.detailed_description ? `
                            <p class="feature-summary">
                                ${feature.detailed_description.summary}
                            </p>
                            ${feature.detailed_description.purpose ? `
                                <p class="feature-purpose">
                                    <strong>用途:</strong> 
                                    ${feature.detailed_description.purpose}
                                </p>
                            ` : ''}
                        ` : ''}
                    </div>
                `;
            });
            
            html += `</div>`;
        }
    }
    
    content.innerHTML = html;
    panel.classList.add('open');
}

function closeDetail() {
    document.getElementById('detailPanel').classList.remove('open');
}
```

### 5. 历史记录列表
```javascript
async function loadHistory() {
    const response = await fetch(
        `${API_BASE_URL}/v1/video-analysis/history?limit=50`
    );
    const history = await response.json();
    
    const container = document.getElementById('historyList');
    container.innerHTML = '';
    
    history.forEach(item => {
        const card = document.createElement('div');
        card.className = 'history-card';
        
        card.innerHTML = `
            <div class="history-thumbnail">
                ${item.thumbnail_url ? 
                    `<img src="${item.thumbnail_url}" />` : 
                    '<div class="placeholder">🎬</div>'
                }
            </div>
            <div class="history-info">
                <h3>${item.title || '未命名任务'}</h3>
                <span class="status-badge status-${item.status}">
                    ${item.status}
                </span>
                <p>${item.segment_count || 0} 个镜头 · 
                   ${item.duration_sec?.toFixed(1) || 0}秒</p>
                <p>${formatDate(item.created_at)}</p>
                
                ${item.learning_points.length > 0 ? `
                    <div class="learning-points">
                        <strong>💡 学习要点:</strong>
                        <ul>
                            ${item.learning_points.map(p => 
                                `<li>${p}</li>`
                            ).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
            <div class="history-actions">
                <button onclick="loadHistoryJob('${item.job_id}')">
                    查看
                </button>
                <button onclick="deleteHistory('${item.job_id}')">
                    删除
                </button>
            </div>
        `;
        
        container.appendChild(card);
    });
}

async function loadHistoryJob(jobId) {
    const response = await fetch(
        `${API_BASE_URL}/v1/video-analysis/jobs/${jobId}`
    );
    const data = await response.json();
    
    if (data.status === 'succeeded' && data.result) {
        displayTimeline(data.result);
    }
}

async function deleteHistory(jobId) {
    if (!confirm('确定删除此记录？')) return;
    
    await fetch(`${API_BASE_URL}/v1/video-analysis/jobs/${jobId}`, {
        method: 'DELETE'
    });
    
    loadHistory(); // 刷新列表
}
```

---

## 🎯 完整示例代码

### HTML 完整示例
```html
<!DOCTYPE html>
<html>
<head>
    <title>视频分析工具</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- 导航 -->
    <nav>
        <h1>视频分析工具</h1>
        <button onclick="showTab('upload')">上传</button>
        <button onclick="showTab('history')">历史</button>
    </nav>
    
    <!-- 上传页面 -->
    <div id="uploadTab" class="tab-content">
        <div class="upload-section">
            <input type="file" id="videoInput" accept="video/*" />
            <button onclick="selectVideo()">选择视频</button>
            <div id="fileName"></div>
            
            <div class="options">
                <label>
                    抽帧率: <input type="number" id="fps" value="2" />
                </label>
                <label>
                    最大帧数: <input type="number" id="maxFrames" value="240" />
                </label>
            </div>
            
            <button onclick="startAnalysis()" id="analyzeBtn" disabled>
                开始分析
            </button>
        </div>
        
        <!-- 加载状态 -->
        <div id="loadingPanel" style="display:none;">
            <div class="spinner"></div>
            <p id="progressMessage">准备中...</p>
            <div class="progress-bar">
                <div id="progressFill"></div>
            </div>
            <p id="progressPercent">0%</p>
        </div>
        
        <!-- 时间轴 -->
        <div id="timelinePanel" style="display:none;">
            <div class="timeline-ruler" id="timelineRuler"></div>
            
            <video id="previewVideo" controls></video>
            
            <div class="track">
                <div class="track-header">镜头片段</div>
                <div class="track-content" id="segmentsTrack"></div>
            </div>
            
            <div class="track">
                <div class="track-header">运镜</div>
                <div class="track-content" id="cameraTrack"></div>
            </div>
            
            <div class="track">
                <div class="track-header">光线</div>
                <div class="track-content" id="lightingTrack"></div>
            </div>
            
            <div class="track">
                <div class="track-header">调色</div>
                <div class="track-content" id="colorTrack"></div>
            </div>
        </div>
    </div>
    
    <!-- 历史页面 -->
    <div id="historyTab" class="tab-content" style="display:none;">
        <h2>历史记录</h2>
        <button onclick="loadHistory()">刷新</button>
        <div id="historyList"></div>
    </div>
    
    <!-- 详情面板 -->
    <div id="detailPanel" class="detail-panel">
        <div class="detail-header">
            <h3>详细分析</h3>
            <button onclick="closeDetail()">×</button>
        </div>
        <div id="detailContent"></div>
    </div>
    
    <script src="app.js"></script>
</body>
</html>
```

### JavaScript 完整示例
参考前面的代码片段，组合成完整的 `app.js`

---

## 📝 样式建议

### 基础样式（可根据自己的UI风格调整）

```css
/* 时间轴容器 */
.timeline-container {
    padding: 20px;
}

/* 时间标尺 */
.timeline-ruler {
    height: 30px;
    background: #f5f5f5;
    position: relative;
    margin-bottom: 10px;
}

.time-mark {
    position: absolute;
    font-size: 12px;
    color: #666;
}

/* 轨道 */
.track {
    display: flex;
    margin-bottom: 15px;
    min-height: 60px;
}

.track-header {
    width: 120px;
    display: flex;
    align-items: center;
    padding: 10px;
    background: #f0f0f0;
    font-weight: bold;
}

.track-content {
    flex: 1;
    position: relative;
    background: #fafafa;
    border: 1px solid #e0e0e0;
}

/* 片段 */
.segment {
    position: absolute;
    height: 100%;
    border-radius: 4px;
    padding: 5px;
    cursor: pointer;
    transition: transform 0.2s;
    font-size: 12px;
}

.segment:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

/* 不同类型的片段颜色 */
.feature-camera_motion {
    background: linear-gradient(135deg, #42b983, #35495e);
    color: white;
}

.feature-lighting {
    background: linear-gradient(135deg, #f39c12, #e67e22);
    color: white;
}

.feature-color_grading {
    background: linear-gradient(135deg, #9b59b6, #8e44ad);
    color: white;
}

/* 详情面板 */
.detail-panel {
    position: fixed;
    right: 0;
    top: 0;
    width: 400px;
    height: 100%;
    background: white;
    box-shadow: -2px 0 10px rgba(0,0,0,0.1);
    transform: translateX(100%);
    transition: transform 0.3s;
}

.detail-panel.open {
    transform: translateX(0);
}

/* 历史记录卡片 */
.history-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    display: flex;
    gap: 15px;
}

.history-thumbnail {
    width: 120px;
    height: 80px;
    background: #f0f0f0;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
}
```

---

## 🔧 调试技巧

### 1. 查看API响应
```javascript
// 在浏览器控制台运行
fetch('http://localhost:8000/v1/video-analysis/jobs/job_abc123')
    .then(r => r.json())
    .then(console.log);
```

### 2. 模拟数据测试
```javascript
// 使用模拟数据测试UI
const mockResult = {
    target: {
        segments: [
            {
                segment_id: "seg_0001",
                start_ms: 0,
                end_ms: 3000,
                duration_ms: 3000,
                features: [
                    {
                        category: "camera_motion",
                        type: "close_up",
                        value: "特写",
                        confidence: 0.9
                    }
                ]
            }
        ]
    }
};

displayTimeline(mockResult);
```

### 3. 日志调试
```javascript
// 在关键位置添加日志
console.log('创建Job:', jobId);
console.log('进度更新:', progress);
console.log('结果:', result);
```

---

## 📚 参考资源

- **完整前端示例**: `/frontend/` 目录
- **API文档**: `API_GUIDE.md`
- **特征说明**: `SHOT_TERMINOLOGY.md`

---

## 💡 常见问题

### Q: 如何处理大视频文件？
A: 建议在后端处理文件上传，前端只传递文件路径。可以使用分片上传或流式上传。

### Q: 如何优化轮询性能？
A: 可以实现WebSocket实时推送，替代轮询机制。

### Q: 如何自定义特征类型？
A: 在后端配置中添加自定义特征类型，前端只需要按照数据结构渲染即可。

### Q: 如何适配移动端？
A: 使用响应式布局，轨道可以垂直堆叠，使用触摸事件代替鼠标事件。

---

## 📞 技术支持

如有问题，请参考：
- 项目README
- API文档
- 提交Issue

---

**祝集成顺利！** 🎉

