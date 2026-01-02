# Video Shooting Assistant

智能视频拍摄辅助系统 - 多Agent协同的流水线架构

## Overview

本系统是一个智能视频拍摄辅助系统，针对视频拍摄过程中的镜头运动与构图优化，采用多 Agent 协同的流水线架构。系统能够自动分析拍摄素材特征，并生成分层的拍摄指令卡，帮助摄影师优化拍摄技巧。

## Features

### 核心功能
- 视频上传和预处理
- 特征提取（光流、主体检测、音频节拍）
- 启发式分析
- 元数据合成（LLM辅助）
- 拍摄指令卡生成
- 参考样片检索

### 新增实时拍摄指导功能 ⭐
- **环境判读**：使用多模态VLM分析拍摄环境，评估可拍性
- **智能任务推荐**：根据环境自动推荐低风险拍摄任务（静止锁定、缓慢移动、轻柔推进等）
- **实时HUD界面**：
  - 顶部教练胶囊：显示当前任务和目标
  - 方向指示器：边缘chevrons（>>>）指示移动方向
  - 平衡水平仪：底部实时显示运动平滑度
- **任务状态管理**：完整的任务生命周期（扫描→选择→执行→纠错→完成）
- **实时反馈**：基于CV指标的运动分析和纠错建议

## Installation

### 使用 uv（推荐）

```bash
# 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

### 使用 pip（传统方式）

```bash
# Install dependencies
pip install -e ".[dev]"

# Or using pip with requirements
pip install -r requirements.txt
```

## Quick Start

### 前置要求

- Python 3.10+
- Node.js 18+
- Redis (可选，当前版本未使用，会话管理使用内存存储)
- PostgreSQL (可选)

### 快速启动

1. **配置环境变量**

   在项目根目录创建 `.env` 文件：

   ```bash
   # 多模态LLM配置（必需 - 用于环境判读）
   MM_LLM_API_KEY=your_api_key_here
   MM_LLM_BASE_URL=https://www.sophnet.com/api/open-apis/v1
   MM_LLM_MODEL=Qwen2.5-VL-7B-Instruct

   # Redis配置（必需）
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

2. **启动Redis**

   ```bash
   redis-server
   # 或使用Docker
   docker run -d --name redis -p 6379:6379 redis:latest
   ```

3. **启动项目**

   ```bash
   cd story-galaxy-controller
   
   # HTTPS模式（推荐，支持摄像头访问）
   USE_HTTPS=true ./start.sh
   
   # 或HTTP模式
   ./start.sh
   ```

   这会启动：
   - Node.js 后端服务器（端口 8080）
   - 前端开发服务器（端口 3000）

4. **可选：启动 Python 后端（如果需要 AI 功能）**

   ```bash
   # 新终端窗口
   cd /mnt/data/CubeAI/phone_ai
   uv sync
   uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

   **注意**：Python 后端是可选的，Node.js 服务器可以独立运行。

**详细启动指南请查看 [STARTUP_GUIDE.md](./STARTUP_GUIDE.md)**

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run property-based tests
pytest tests/ -k "property"

# Format code
black src tests
isort src tests

# Type checking
mypy src
```

## Project Structure

```
├── src/
│   ├── agents/          # Agent implementations
│   ├── api/             # FastAPI routes
│   ├── models/          # Data models and enums
│   ├── schemas/         # JSON schemas
│   ├── services/        # Business logic services
│   └── tasks/           # Celery tasks
├── tests/               # Test files
├── configs/             # Configuration files
└── pyproject.toml       # Project configuration
```

## License

MIT
