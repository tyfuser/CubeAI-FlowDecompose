# 📹 视频上传分析功能使用指南

> 支持本地视频文件上传和在线视频链接两种方式

---

## 🎯 功能说明

前端现在支持两种视频分析方式：

### 1️⃣ 本地视频上传（推荐）✨
- **优势**: 更稳定、更快速、无需视频链接
- **支持格式**: MP4, MOV, AVI, MKV, WEBM
- **大小限制**: 500MB
- **流程**: 上传 → 分析 → 结果

### 2️⃣ 在线视频链接
- **优势**: 无需下载视频
- **支持平台**: 抖音、小红书、B站等
- **流程**: 输入链接 → 分析 → 结果

---

## 🚀 前端使用方法

### 用户操作流程

1. **进入 Dashboard**

2. **选择输入模式**
   - 点击 **"链接输入"** 或 **"本地上传"** 切换

3. **本地上传方式**:
   - 点击文件选择区域
   - 选择视频文件（MP4/MOV/AVI/MKV/WEBM）
   - 确认文件信息（文件名、大小）
   - 点击 **"立即开始"**

4. **等待分析**:
   - 显示上传进度（如果是文件上传）
   - 显示分析进度和当前步骤
   - 完成后自动跳转到分析结果页

---

## 🔧 后端需要实现的接口

### 接口 1: 上传视频文件

**端点**: `POST /api/v1/analysis/upload`

**请求格式**: `multipart/form-data`

**请求参数**:
```typescript
{
  file: File  // 表单字段名为 "file"
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "filePath": "/uploads/videos/1234567890_video.mp4",
    "fileName": "my_video.mp4",
    "fileSize": 52428800
  },
  "timestamp": 1704268800000
}
```

**实现建议**:
```javascript
// Express.js 示例
const multer = require('multer');
const path = require('path');

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/videos/');
  },
  filename: (req, file, cb) => {
    const uniqueName = Date.now() + '_' + file.originalname;
    cb(null, uniqueName);
  }
});

const upload = multer({ 
  storage,
  limits: { fileSize: 500 * 1024 * 1024 }, // 500MB
  fileFilter: (req, file, cb) => {
    const validTypes = ['video/mp4', 'video/mov', 'video/avi', 'video/x-matroska', 'video/webm'];
    if (validTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('UNSUPPORTED_FORMAT'));
    }
  }
});

app.post('/api/v1/analysis/upload', upload.single('file'), (req, res) => {
  res.json({
    success: true,
    data: {
      filePath: req.file.path,
      fileName: req.file.originalname,
      fileSize: req.file.size
    }
  });
});
```

### 接口 2: 创建分析任务（已有）

**端点**: `POST /api/v1/analysis/create`

**请求格式**: `application/json`

**请求体**:
```json
{
  "url": "/uploads/videos/1234567890_video.mp4",  // 使用上传返回的 filePath
  "platform": "auto"
}
```

**说明**:
- `url` 参数现在可以接收：
  1. 上传接口返回的文件路径
  2. 服务器本地文件绝对路径
  3. 在线视频链接（抖音、小红书等）

---

## 📊 完整流程示意

```
用户操作
  │
  ├─ 选择 "本地上传"
  │   │
  │   ├─ 选择视频文件
  │   │
  │   ├─ 点击 "立即开始"
  │   │
  │   └─ 前端调用
  │       │
  │       ├─ POST /analysis/upload (上传文件)
  │       │   └─ 返回: { filePath: "..." }
  │       │
  │       ├─ POST /analysis/create (创建分析)
  │       │   └─ 请求: { url: filePath }
  │       │
  │       └─ 轮询 GET /analysis/{id}/status
  │           └─ 完成后获取结果
  │
  └─ 选择 "链接输入"
      │
      ├─ 输入视频链接
      │
      ├─ 点击 "立即开始"
      │
      └─ 前端调用
          │
          ├─ POST /analysis/create (直接创建)
          │   └─ 请求: { url: "https://..." }
          │
          └─ 轮询获取结果
```

---

## 🎨 UI 特性

### 文件上传区域
- ✅ 拖拽上传支持（可扩展）
- ✅ 文件类型验证
- ✅ 文件大小验证（500MB）
- ✅ 文件名和大小显示
- ✅ 支持的格式提示

### 上传进度
- ✅ 上传阶段提示："正在上传视频文件..."
- ✅ 分析阶段显示进度条和当前步骤
- ✅ 完整的错误处理

### 错误提示
- **文件过大**: "文件过大，请上传小于 500MB 的视频"
- **格式错误**: "不支持的视频格式，请上传 MP4、MOV、AVI、MKV 或 WEBM 格式的视频"
- **上传失败**: "上传失败，请稍后重试"
- **网络错误**: "网络连接失败，请检查网络"

---

## 🧪 测试方法

### 1. 测试文件上传

```bash
# 使用 curl 测试上传接口
curl -X POST http://localhost:3000/api/v1/analysis/upload \
  -F "file=@/path/to/your/video.mp4" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 期望响应
{
  "success": true,
  "data": {
    "filePath": "/uploads/videos/1234567890_video.mp4",
    "fileName": "video.mp4",
    "fileSize": 52428800
  }
}
```

### 2. 测试创建分析

```bash
# 使用上传返回的 filePath
curl -X POST http://localhost:3000/api/v1/analysis/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "/uploads/videos/1234567890_video.mp4",
    "platform": "auto"
  }'

# 期望响应
{
  "success": true,
  "data": {
    "analysisId": "job_xxx",
    "status": "queued",
    "estimatedTime": 120
  }
}
```

---

## 📝 前端代码说明

### 关键文件

1. **services/analysisService.ts**
   - `uploadVideo(file)` - 上传视频文件
   - `createAnalysis(data)` - 创建分析任务
   - `pollAnalysisResult(id)` - 轮询分析结果

2. **components/Dashboard.tsx**
   - 输入模式切换（链接/文件）
   - 文件选择和验证
   - 文件信息显示

3. **App.tsx**
   - `handleStartAnalysis(url)` - 处理链接分析
   - `handleStartFileAnalysis(file)` - 处理文件上传分析
   - `startAnalysis(url)` - 统一的分析流程

---

## 🔐 安全建议

### 后端实现

1. **文件验证**
   - 验证文件类型（MIME type）
   - 验证文件大小
   - 验证文件内容（魔数检查）

2. **存储安全**
   - 使用随机文件名
   - 限制上传目录访问权限
   - 定期清理过期文件

3. **权限控制**
   - 验证用户 Token
   - 检查用户配额
   - 记录上传日志

4. **错误处理**
   ```javascript
   // 示例错误响应
   {
     "success": false,
     "error": {
       "code": "FILE_TOO_LARGE",
       "message": "文件大小超过 500MB 限制",
       "details": {
         "maxSize": 524288000,
         "actualSize": 600000000
       }
     }
   }
   ```

---

## 💡 扩展建议

### 可选功能

1. **拖拽上传**
   - 支持拖拽文件到上传区域

2. **上传进度条**
   - 显示文件上传百分比
   - 显示上传速度

3. **多文件上传**
   - 批量上传多个视频
   - 批量分析队列

4. **云存储集成**
   - 上传到 OSS/S3
   - 支持断点续传

5. **视频预处理**
   - 压缩过大视频
   - 提取视频信息（时长、分辨率等）

---

## ❓ 常见问题

### Q: 支持哪些视频格式？
**A**: MP4, MOV, AVI, MKV, WEBM

### Q: 最大文件大小？
**A**: 500MB（可在后端配置中调整）

### Q: 上传失败怎么办？
**A**: 检查：
1. 文件格式是否支持
2. 文件大小是否超限
3. 网络连接是否正常
4. 后端上传接口是否正常

### Q: 可以同时上传多个视频吗？
**A**: 当前版本不支持，需要等待当前分析完成后再上传下一个

---

## 📞 技术支持

- **API 文档**: `API_DOCUMENTATION.md`
- **集成状态**: `API_INTEGRATION_STATUS.md`
- **快速开始**: `START_HERE.md`

---

**功能状态**: ✅ 已完成并可用  
**更新日期**: 2025-01-02

