# 🔧 修复 API 连接错误

## 错误信息

```
ApiError: 网络连接失败，请检查网络
```

## 原因

前端没有 `.env` 文件，导致使用了默认的生产环境 API 地址 `https://api.rubik-ai.com/v1`，而实际需要连接到本地后端服务。

## 解决方案

### 步骤 1: 创建 .env 文件

在 `frontend/` 目录下创建 `.env` 文件：

```bash
cd frontend
cp env.example.txt .env
```

### 步骤 2: 配置 API 地址

编辑 `.env` 文件，确保配置如下：

```env
# API 基础地址（本地开发环境）
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 镜头拆解分析 API
VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000
```

**重要**: 
- 将 `VITE_API_BASE_URL` 从 `http://localhost:3000/api/v1` 改为 `http://localhost:8000/api/v1`
- 添加 `VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000`

### 步骤 3: 重启前端服务

修改 `.env` 文件后，**必须重启前端开发服务器**才能生效：

```bash
# 停止当前运行的前端服务（Ctrl+C）
# 然后重新启动
cd frontend
npm run dev
```

## 完整 .env 配置示例

```env
# ========================================
# API 配置
# ========================================

# API 基础地址（本地开发环境）
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 镜头拆解分析 API
VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000

# API 超时时间（毫秒）
VITE_API_TIMEOUT=30000

# ========================================
# 功能开关
# ========================================

# 是否启用 Mock 数据
VITE_ENABLE_MOCK=false

# 是否启用 API 日志
VITE_ENABLE_API_LOG=true
```

## 验证

1. **检查后端服务是否运行**：
   ```bash
   curl http://localhost:8000/docs
   ```
   应该能看到 HTML 响应

2. **检查前端配置**：
   - 打开浏览器开发者工具（F12）
   - 查看 Console，应该能看到正确的 API 地址
   - 查看 Network 标签，API 请求应该发送到 `http://localhost:8000/api/v1/...`

## 常见问题

### Q: 修改 .env 后仍然报错？

A: 确保：
1. 已重启前端开发服务器
2. `.env` 文件在 `frontend/` 目录下（不是项目根目录）
3. 环境变量名称以 `VITE_` 开头
4. 没有拼写错误

### Q: 后端服务没有运行？

A: 启动主后端服务：
```bash
cd Backend/video_ai_demo
./start.sh
```

### Q: 端口冲突？

A: 
- 主后端默认端口：8000
- Phone AI 后端默认端口：8001
- 前端默认端口：3000

如果端口被占用，可以修改：
- 后端端口：修改 `start.sh` 或使用 `--port` 参数
- 前端端口：修改 `vite.config.ts` 中的 `port`

## 相关文档

- [环境配置指南](./ENV_CONFIG.md)
- [快速开始指南](./QUICK_START.md)
- [故障排查指南](./TROUBLESHOOTING.md)

