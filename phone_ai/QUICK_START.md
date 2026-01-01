# ⚡ 快速启动指南

## 最简启动（1步）

`phone_ai` 是集成项目，前端和后端代理都在 `story-galaxy-controller` 目录中。

```bash
cd /mnt/data/CubeAI/phone_ai/story-galaxy-controller

# HTTPS模式（推荐，支持摄像头访问）
USE_HTTPS=true ./start.sh

# 或HTTP模式（摄像头可能无法访问）
./start.sh
```

这会自动启动：
- ✅ Node.js 后端服务器（端口 8080）
- ✅ 前端开发服务器（端口 3000）

## 可选：启动 Python 后端（如果需要 AI 功能）

如果需要在 Node.js 代理中使用 Python 后端的 AI 功能：

```bash
# 新终端窗口
cd /mnt/data/CubeAI/phone_ai

# 使用 uv 安装依赖
uv sync

# 启动 Python 后端
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

**注意**：Python 后端是可选的，Node.js 服务器可以独立运行（使用 Mock 数据）。

## 🎯 访问地址

- **前端界面**: http://localhost:3000 (HTTP) 或 https://localhost:3000 (HTTPS)
- **Node.js 后端**: http://localhost:8080 (WebSocket)
- **Python 后端** (可选): http://localhost:8000
- **Python API文档** (可选): http://localhost:8000/docs

## ⚙️ 环境变量（可选）

如果需要自定义配置，创建 `.env` 文件：

```bash
# 多模态LLM API密钥（用于环境判读）
MM_LLM_API_KEY=your_api_key_here
```

**注意**：
- 如果不配置 `MM_LLM_API_KEY`，环境判读功能会使用兜底任务
- Redis配置存在但**当前未使用**，会话管理使用内存存储

## 🔍 验证

1. 打开浏览器访问 http://localhost:8000/docs
2. 打开前端界面 http://localhost:5173
3. 创建会话，连接移动端
4. 开始拍摄，查看HUD界面是否显示

## ⚠️ 重要提示

1. **摄像头访问需要 HTTPS**：使用 `USE_HTTPS=true ./start.sh` 启动
2. **Python 后端是可选的**：Node.js 服务器可以独立运行（使用 Mock 数据）
3. **项目结构**：`phone_ai` 是集成项目，前端在 `story-galaxy-controller` 目录

详细架构说明请查看 [ARCHITECTURE.md](./ARCHITECTURE.md)

## 📖 详细文档

完整启动指南请查看 [STARTUP_GUIDE.md](./STARTUP_GUIDE.md)

