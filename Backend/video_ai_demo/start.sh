#!/bin/bash

# Video AI Demo 启动脚本
# 支持 uv 和传统 pip 两种方式

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================${NC}"
echo -e "${BLUE}Video AI Demo Backend${NC}"
echo -e "${BLUE}===================================${NC}"
echo ""

# 检查 .env 文件
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${YELLOW}警告: .env 文件不存在，正在从 .env.example 复制...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}请编辑 .env 文件，填入你的API密钥${NC}"
        echo ""
    else
        echo -e "${YELLOW}警告: .env 文件不存在，将使用默认配置${NC}"
        echo ""
    fi
fi

# 检查 uv
if command -v uv &> /dev/null; then
    echo -e "${GREEN}检测到 uv，使用 uv 管理环境${NC}"
    USE_UV=true
else
    echo -e "${YELLOW}未检测到 uv，使用传统 pip 方式${NC}"
    echo -e "${YELLOW}推荐安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    USE_UV=false
fi

# 安装依赖
if [ "$USE_UV" = true ]; then
    # 使用 uv
    if [ -f "pyproject.toml" ]; then
        echo -e "${YELLOW}同步依赖（uv sync）...${NC}"
        uv sync
        echo -e "${GREEN}✓ 依赖已同步${NC}"
    else
        echo -e "${YELLOW}未找到 pyproject.toml，使用 requirements.txt...${NC}"
        uv pip install -r requirements.txt
    fi
else
    # 传统方式
    echo -e "${YELLOW}检查依赖...${NC}"
    python3 -c "import fastapi" 2>/dev/null || {
        echo -e "${YELLOW}依赖未安装，正在安装...${NC}"
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        else
            echo -e "${RED}错误: 未找到 requirements.txt${NC}"
            exit 1
        fi
    }
fi

# 检查 ffmpeg
echo -e "${YELLOW}检查 FFmpeg...${NC}"
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}错误: 未找到 ffmpeg，请先安装：${NC}"
    echo "  macOS: brew install ffmpeg"
    echo "  Ubuntu: sudo apt install ffmpeg"
    exit 1
fi
echo -e "${GREEN}✓ FFmpeg 已安装${NC}"

# 检查 ffprobe
if ! command -v ffprobe &> /dev/null; then
    echo -e "${YELLOW}警告: 未找到 ffprobe（通常与 ffmpeg 一起安装）${NC}"
fi

# 创建数据目录
mkdir -p data

echo ""
echo -e "${GREEN}启动服务...${NC}"
echo -e "${BLUE}访问地址:${NC} http://localhost:8000"
echo -e "${BLUE}API文档:${NC} http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo ""

# 启动服务
if [ "$USE_UV" = true ]; then
    if [ -f ".env" ]; then
        uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file .env
    else
        uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    fi
else
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi

