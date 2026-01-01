# 🔧 环境变量配置说明

## 📋 配置文件位置

`.env` 文件位于项目根目录

---

## 🔑 必需配置

### API 地址配置

项目中有两套独立的后端服务：

#### 1. 原有功能后端（Dashboard、视频深度拆解等）

```env
VITE_API_BASE_URL=http://localhost:3000/api/v1
```

**使用此 API 的功能：**
- ✅ 总览面板（Dashboard）
- ✅ 视频深度拆解（Analysis）
- ✅ 视频转幻灯片（VideoSlideshow）
- ✅ 知识库（KnowledgeBase）

**接口示例：**
- `GET /dashboard/stats` - 获取统计数据
- `POST /analysis/create` - 创建视频分析任务
- `GET /analysis/:id` - 查询分析结果

---

#### 2. 镜头拆解分析功能后端（新增）

```env
VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000
```

**使用此 API 的功能：**
- ✅ 镜头拆解分析（ShotAnalysis）

**接口示例：**
- `POST /v1/video-analysis/jobs` - 创建分析任务
- `GET /v1/video-analysis/jobs/{job_id}` - 查询任务状态
- `GET /v1/video-analysis/history` - 获取历史记录

---

## 🚀 完整配置示例

```env
# ============ API 配置 ============

# 原有功能的后端服务地址（Dashboard、视频深度拆解等）
VITE_API_BASE_URL=http://localhost:3000/api/v1

# 新增：镜头拆解分析功能的后端服务地址
VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000

# API 超时时间（毫秒）
VITE_API_TIMEOUT=30000

# ============ 功能开关 ============

# 是否启用 Mock 数据（开发时可以设为 true）
VITE_ENABLE_MOCK=false

# 是否启用 API 日志
VITE_ENABLE_API_LOG=true

# ============ 业务配置 ============

# 每日免费配额
VITE_FREE_DAILY_QUOTA=5

# 最大文件大小（MB）
VITE_MAX_FILE_SIZE=100

# 支持的视频格式
VITE_SUPPORTED_VIDEO_FORMATS=mp4,mov,avi,mkv

# 轮询间隔（毫秒）
VITE_POLL_INTERVAL=2000

# 最大轮询次数
VITE_MAX_POLL_ATTEMPTS=60
```

---

## 🎯 不同环境配置

### 开发环境（本地）

```env
VITE_API_BASE_URL=http://localhost:3000/api/v1
VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000
VITE_ENABLE_MOCK=false
VITE_ENABLE_API_LOG=true
```

### 测试环境

```env
VITE_API_BASE_URL=https://test-api.rubik-ai.com/v1
VITE_SHOT_ANALYSIS_BASE_URL=https://test-shot-api.rubik-ai.com
VITE_ENABLE_MOCK=false
VITE_ENABLE_API_LOG=true
```

### 生产环境

```env
VITE_API_BASE_URL=https://api.rubik-ai.com/v1
VITE_SHOT_ANALYSIS_BASE_URL=https://shot-api.rubik-ai.com
VITE_ENABLE_MOCK=false
VITE_ENABLE_API_LOG=false
```

---

## ⚠️ 重要提示

### 1. 环境变量生效

修改 `.env` 文件后，**必须重启开发服务器**才能生效：

```bash
# 停止当前服务（Ctrl + C）
# 然后重新启动
npm run dev
```

### 2. 前缀要求

Vite 要求所有环境变量必须以 `VITE_` 开头才能在客户端代码中访问。

**正确：**
```env
VITE_API_BASE_URL=http://localhost:3000/api/v1
```

**错误：**
```env
API_BASE_URL=http://localhost:3000/api/v1  # 无法访问
```

### 3. 安全提示

⚠️ **不要在 `.env` 中存储敏感信息！**

- `.env` 文件中的内容会被打包到前端代码中
- 任何人都可以在浏览器中查看
- 敏感信息（如 API Key）应该只在后端使用

---

## 🔍 故障排查

### 问题：无法连接后端

**检查清单：**

1. **确认后端服务已启动**
   ```bash
   # 检查端口 3000
   lsof -i :3000
   
   # 检查端口 8000
   lsof -i :8000
   ```

2. **确认 `.env` 配置正确**
   ```bash
   cat .env
   ```

3. **确认已重启开发服务器**
   - 修改 `.env` 后必须重启

4. **查看浏览器控制台**
   - 打开开发者工具 → Console
   - 查看具体的错误信息

5. **查看网络请求**
   - 打开开发者工具 → Network
   - 查看请求的目标地址是否正确

### 问题：环境变量未生效

**解决方案：**

1. 检查变量名是否以 `VITE_` 开头
2. 重启开发服务器（`npm run dev`）
3. 清除浏览器缓存后刷新页面

### 问题：CORS 错误

**解决方案：**

后端需要配置 CORS，允许前端域名访问：

```javascript
// Node.js 示例
app.use(cors({
  origin: 'http://localhost:5173',
  credentials: true
}));
```

---

## 📝 配置验证

### 在代码中访问环境变量

```typescript
// 访问原有功能的 API 地址
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
console.log('API Base URL:', apiBaseUrl);

// 访问镜头拆解功能的 API 地址
const shotAnalysisUrl = import.meta.env.VITE_SHOT_ANALYSIS_BASE_URL;
console.log('Shot Analysis URL:', shotAnalysisUrl);
```

### 运行时检查

在浏览器控制台运行：

```javascript
// 检查配置
console.log('环境变量:', import.meta.env);
```

---

## 🆘 需要帮助？

如果配置后仍然有问题，请：

1. 查看 **[故障排查文档](TROUBLESHOOTING.md)**
2. 检查后端服务日志
3. 在浏览器开发者工具中查看详细错误信息

---

**配置完成后记得重启开发服务器！** 🔄

