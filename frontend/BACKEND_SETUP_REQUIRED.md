# ⚠️ 后端服务配置说明

## 🔍 当前问题

前端正在尝试连接到 `http://localhost:8000`，但收到 `ERR_CONNECTION_REFUSED` 错误。

这说明：
- ✅ 前端配置正确
- ❌ **后端服务未启动或未提供所需的 API**

---

## 🎯 解决方案选择

### 方案 1：启动后端服务（推荐）

如果您有后端项目：

```bash
# 进入后端项目目录
cd /path/to/your/backend

# 启动后端服务（具体命令取决于您的后端技术栈）
# Node.js 示例:
npm run dev

# Python 示例:
python main.py

# Go 示例:
go run main.go
```

**确保后端运行在 8000 端口并提供以下 API：**

#### 原有功能需要的 API：
- `GET /api/v1/dashboard/stats` - Dashboard 统计数据
- `GET /api/v1/dashboard/projects` - 项目列表
- `GET /api/v1/dashboard/schedule` - 日程数据
- `POST /api/v1/analysis/create` - 创建视频分析
- `POST /api/v1/analysis/upload` - 上传视频文件
- `GET /api/v1/analysis/:id` - 获取分析结果
- `GET /api/v1/analysis/:id/status` - 获取分析状态

#### 镜头拆解功能需要的 API（新）：
- `POST /v1/video-analysis/jobs` - 创建分析任务
- `GET /v1/video-analysis/jobs/:id` - 查询任务状态
- `GET /v1/video-analysis/history` - 获取历史记录
- `DELETE /v1/video-analysis/jobs/:id` - 删除任务

---

### 方案 2：使用 Mock 数据（临时开发）

如果您暂时没有后端，可以启用 Mock 模式：

#### 步骤 1：修改 `.env`

```env
# 启用 Mock 数据
VITE_ENABLE_MOCK=true
```

#### 步骤 2：重启前端

```bash
npm run dev
```

**注意**：Mock 模式下，数据是模拟的，不会真正调用 AI 分析。

---

### 方案 3：连接到远程后端

如果后端部署在其他地方：

#### 修改 `.env`

```env
# 连接到远程后端
VITE_API_BASE_URL=https://your-backend.com/api/v1
VITE_SHOT_ANALYSIS_BASE_URL=https://your-shot-backend.com
```

---

## 📋 后端实现检查清单

如果您正在实现后端，请确保：

### ✅ 基础配置
- [ ] 后端服务运行在 8000 端口
- [ ] 配置了 CORS，允许 `http://localhost:3000` 访问
- [ ] API 路径正确（`/api/v1/...` 和 `/v1/video-analysis/...`）

### ✅ Dashboard API
- [ ] `GET /api/v1/dashboard/stats` 返回统计数据
- [ ] `GET /api/v1/dashboard/projects` 返回项目列表
- [ ] `GET /api/v1/dashboard/schedule` 返回日程数据

### ✅ 视频分析 API
- [ ] `POST /api/v1/analysis/upload` 接收视频文件
- [ ] `POST /api/v1/analysis/create` 创建分析任务
- [ ] `GET /api/v1/analysis/:id` 返回分析结果
- [ ] `GET /api/v1/analysis/:id/status` 返回任务状态

### ✅ 镜头拆解 API（可选，新功能）
- [ ] `POST /v1/video-analysis/jobs` 创建任务
- [ ] `GET /v1/video-analysis/jobs/:id` 查询状态
- [ ] `GET /v1/video-analysis/history` 历史记录
- [ ] `DELETE /v1/video-analysis/jobs/:id` 删除任务

---

## 🔧 CORS 配置示例

### Node.js (Express)

```javascript
const cors = require('cors');

app.use(cors({
  origin: 'http://localhost:3000',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Version']
}));
```

### Python (FastAPI)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Go (Gin)

```go
import "github.com/gin-contrib/cors"

func main() {
    r := gin.Default()
    
    r.Use(cors.New(cors.Config{
        AllowOrigins:     []string{"http://localhost:3000"},
        AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        AllowHeaders:     []string{"Content-Type", "Authorization", "X-API-Version"},
        AllowCredentials: true,
    }))
    
    r.Run(":8000")
}
```

---

## 📊 API 数据格式参考

详细的 API 接口规范请查看：
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - 原有功能 API 规范
- **[FRONTEND_INTEGRATION_GUIDE.md](FRONTEND_INTEGRATION_GUIDE.md)** - 镜头拆解功能 API 规范

---

## 🧪 测试后端连接

### 方法 1：使用 curl

```bash
# 测试 Dashboard API
curl http://localhost:8000/api/v1/dashboard/stats

# 测试视频分析 API
curl -X POST http://localhost:8000/api/v1/analysis/create \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video.mp4", "platform": "auto"}'

# 测试镜头拆解 API
curl -X POST http://localhost:8000/v1/video-analysis/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "learn",
    "target_video": {
      "source": {
        "type": "file",
        "path": "/path/to/video.mp4"
      }
    }
  }'
```

### 方法 2：使用浏览器

打开浏览器访问：
- http://localhost:8000/api/v1/dashboard/stats
- 如果能看到 JSON 数据，说明后端正常运行

---

## 🔍 故障排查

### 1. 检查端口占用

```bash
# 检查 8000 端口
lsof -i :8000

# 如果没有输出，说明后端未运行
```

### 2. 检查后端日志

启动后端时查看控制台输出，确认：
- 服务监听的端口
- 是否有错误信息
- CORS 配置是否生效

### 3. 检查防火墙

确保防火墙没有阻止 8000 端口：

```bash
# macOS
sudo lsof -i :8000

# Linux
sudo netstat -tlnp | grep 8000
```

---

## 💡 推荐开发流程

### 如果您还没有后端：

1. **先使用 Mock 模式**开发前端 UI
   ```env
   VITE_ENABLE_MOCK=true
   ```

2. **并行开发后端**，参考 API 文档实现接口

3. **逐步迁移**到真实 API
   ```env
   VITE_ENABLE_MOCK=false
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

### 如果您已有后端：

1. **确认后端运行**在 8000 端口
2. **配置 CORS** 允许前端访问
3. **实现必需的 API** 端点
4. **测试连接**是否正常

---

## 📚 相关文档

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - 完整 API 文档
- **[ENV_CONFIG.md](ENV_CONFIG.md)** - 环境配置说明
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - 故障排查指南

---

## 🆘 需要帮助？

如果按照以上步骤仍然无法解决：

1. 检查后端控制台是否有错误日志
2. 检查浏览器 Network 标签，查看请求详情
3. 确认后端 API 路径与前端配置一致
4. 检查后端是否正确返回 JSON 格式数据

---

**选择适合您的方案，然后重启前端开发服务器！** 🚀

