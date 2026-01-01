# 🔧 故障排查指南

## 问题：文件上传后提示"请提供有效的文件路径"

### 原因分析

这个错误通常出现在以下情况：

1. **后端上传接口未实现** ⚠️
   - 前端调用 `POST /api/v1/analysis/upload`
   - 后端返回 404 或其他错误
   - 或者返回的数据格式不正确

2. **返回的 filePath 格式不对**
   - 后端返回了相对路径（如 `uploads/video.mp4`）
   - 但是后端期望绝对路径（如 `/uploads/videos/video.mp4`）

### 解决方案

#### 方案 1: 使用"本地路径"模式（临时方案）✨

如果后端上传接口还没准备好，可以：

1. **将视频文件复制到服务器**
   ```bash
   # 将视频复制到后端服务器的某个目录
   scp video.mp4 user@server:/path/to/videos/
   ```

2. **在前端选择"本地路径"模式**
   - 点击 **"本地路径"** 按钮
   - 输入服务器上的绝对路径：`/path/to/videos/video.mp4`
   - 点击 **"立即开始"**

3. **后端直接使用这个路径进行分析**

#### 方案 2: 实现后端上传接口（推荐）

后端需要实现上传接口，返回正确格式的数据：

```javascript
// Express.js 示例
const multer = require('multer');
const path = require('path');

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/videos/');  // 确保这个目录存在
  },
  filename: (req, file, cb) => {
    const uniqueName = Date.now() + '_' + file.originalname;
    cb(null, uniqueName);
  }
});

const upload = multer({ 
  storage,
  limits: { fileSize: 500 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/webm'];
    if (validTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('UNSUPPORTED_FORMAT'));
    }
  }
});

app.post('/api/v1/analysis/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({
      success: false,
      error: {
        code: 'NO_FILE',
        message: '未上传文件'
      }
    });
  }

  // ⚠️ 重要：返回绝对路径
  const absolutePath = path.resolve(req.file.path);

  res.json({
    success: true,
    data: {
      filePath: absolutePath,  // 绝对路径，如 /Users/xxx/uploads/videos/123_video.mp4
      fileName: req.file.originalname,
      fileSize: req.file.size
    }
  });
});
```

**关键点**:
- ✅ `filePath` 必须是**绝对路径**（以 `/` 开头）
- ✅ 使用 `path.resolve()` 确保返回绝对路径
- ✅ 或者返回相对于项目根目录的完整路径

---

## 调试步骤

### 1. 查看浏览器控制台

打开浏览器开发者工具（F12），查看：

**Console 标签页**:
```
开始上传文件: video.mp4 大小: 50.23 MB
✅ 视频上传成功，返回结果: {...}
返回的 filePath: /path/to/video.mp4
开始创建分析任务，使用路径: /path/to/video.mp4
```

如果看到：
- ❌ 上传失败或返回错误 → 检查后端上传接口
- ❌ filePath 不是以 `/` 开头 → 修改后端返回绝对路径
- ❌ filePath 为空 → 后端未正确返回数据

**Network 标签页**:
1. 找到 `analysis/upload` 请求
2. 查看 Response：
   ```json
   {
     "success": true,
     "data": {
       "filePath": "/absolute/path/to/video.mp4",  // 必须是绝对路径
       "fileName": "video.mp4",
       "fileSize": 52428800
     }
   }
   ```

### 2. 测试上传接口

使用 curl 测试：

```bash
curl -X POST http://localhost:3000/api/v1/analysis/upload \
  -F "file=@/path/to/local/video.mp4" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

期望响应：
```json
{
  "success": true,
  "data": {
    "filePath": "/absolute/path/on/server/video.mp4",
    "fileName": "video.mp4",
    "fileSize": 52428800
  }
}
```

如果返回 404：
- 后端上传接口未实现
- 使用"本地路径"模式作为临时方案

如果返回其他错误：
- 检查文件格式是否支持
- 检查文件大小是否超限
- 检查后端日志

### 3. 验证文件路径

如果使用"本地路径"模式，确保：

```bash
# 在服务器上检查文件是否存在
ls -lh /path/to/video.mp4

# 检查文件权限
chmod 644 /path/to/video.mp4
```

---

## 三种输入模式对比

| 模式 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **在线链接** | 分析在线视频 | 无需下载视频 | 需要视频平台支持 |
| **文件上传** | 分析本地视频 | 方便快捷 | 需要后端上传接口 |
| **本地路径** | 临时开发测试 | 无需上传功能 | 需要手动复制文件到服务器 |

---

## 常见错误及解决

### 错误 1: "请提供有效的文件路径（以/开头）"

**原因**: 
- 后端返回的是相对路径，如 `uploads/video.mp4`
- 而不是绝对路径 `/path/to/uploads/video.mp4`

**解决**:
```javascript
// 后端修改
const absolutePath = path.resolve(req.file.path);
// 或
const absolutePath = path.join(process.cwd(), req.file.path);
```

### 错误 2: "上传接口未返回 filePath"

**原因**: 后端响应数据格式不正确

**检查后端返回**:
```json
// ❌ 错误格式
{
  "file": "/path/to/video.mp4"
}

// ✅ 正确格式
{
  "success": true,
  "data": {
    "filePath": "/path/to/video.mp4",
    "fileName": "video.mp4",
    "fileSize": 52428800
  }
}
```

### 错误 3: "Network Error"

**原因**: 
- 后端未启动
- CORS 配置问题
- .env 配置错误

**解决**:
1. 确认后端正在运行
2. 检查 `.env` 中的 `VITE_API_BASE_URL`
3. 确认后端 CORS 配置

### 错误 4: "文件过大" / "不支持的格式"

**原因**: 前端验证通过，但后端限制更严格

**解决**:
- 检查后端的文件大小限制
- 检查后端支持的文件格式
- 调整 multer 配置

---

## 推荐开发流程

### 阶段 1: 使用"本地路径"模式
```
1. 将测试视频复制到服务器
2. 使用"本地路径"模式输入绝对路径
3. 验证分析功能是否正常
```

### 阶段 2: 实现上传接口
```
1. 实现 POST /api/v1/analysis/upload
2. 确保返回绝对路径
3. 测试上传和分析流程
```

### 阶段 3: 完整测试
```
1. 测试三种输入模式
2. 测试各种错误情况
3. 优化用户体验
```

---

## 快速检查清单

- [ ] `.env` 文件已创建，`VITE_API_BASE_URL` 配置正确
- [ ] 后端服务正在运行
- [ ] 上传接口已实现（或使用"本地路径"模式）
- [ ] 上传接口返回绝对路径（以 `/` 开头）
- [ ] 服务器上的视频文件有正确的读取权限
- [ ] 浏览器控制台无错误
- [ ] Network 请求返回正确的数据格式

---

## 获取帮助

如果问题仍未解决：

1. **查看浏览器控制台**
   - 复制完整的错误信息
   - 查看 Network 请求和响应

2. **查看后端日志**
   - 检查上传接口是否被调用
   - 检查返回的数据格式

3. **参考文档**
   - `VIDEO_UPLOAD_GUIDE.md` - 上传功能详细指南
   - `API_DOCUMENTATION.md` - API 接口文档
   - `START_HERE.md` - 快速开始指南

---

**更新日期**: 2025-01-02  
**状态**: 已添加"本地路径"模式作为临时方案

