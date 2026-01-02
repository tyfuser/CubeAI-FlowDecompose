#!/bin/bash

# Phone AI 后端启动脚本

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Phone AI - 后端服务启动${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 uv
if command -v uv &> /dev/null; then
    echo -e "${GREEN}检测到 uv，使用 uv 管理环境${NC}"
    USE_UV=true
else
    echo -e "${YELLOW}未检测到 uv，使用传统 pip 方式${NC}"
    echo -e "${YELLOW}推荐安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    USE_UV=false
fi

if [ "$USE_UV" = true ]; then
    # 使用 uv
    echo -e "${YELLOW}同步依赖（uv sync）...${NC}"
    uv sync
    
    echo -e "${GREEN}使用 uv 启动服务...${NC}"
else
    # 传统方式
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 Python3，请先安装 Python 3.10+${NC}"
        exit 1
    fi

    # 检查虚拟环境
    if [ -d "venv" ]; then
        echo -e "${GREEN}激活虚拟环境...${NC}"
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        echo -e "${GREEN}激活虚拟环境...${NC}"
        source .venv/bin/activate
    fi

    # 检查依赖是否已安装
    echo -e "${YELLOW}检查依赖...${NC}"
    python3 -c "import fastapi" 2>/dev/null || {
        echo -e "${YELLOW}依赖未安装，正在安装...${NC}"
        pip install -e ".[dev]"
    }
fi

# 注意：Redis 当前版本未使用（会话管理使用内存存储）
# 以下检查已注释，如果将来需要Redis可以取消注释
# echo -e "${YELLOW}检查 Redis 连接...${NC}"
# if ! python3 -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping()" 2>/dev/null; then
#     echo -e "${RED}警告: 无法连接到 Redis (localhost:6379)${NC}"
#     echo -e "${YELLOW}请确保 Redis 正在运行:${NC}"
#     echo "  - redis-server"
#     echo "  - 或 docker run -d --name redis -p 6379:6379 redis:latest"
#     read -p "是否继续？(y/n) " -n 1 -r
#     echo
#     if [[ ! $REPLY =~ ^[Yy]$ ]]; then
#         exit 1
#     fi
# fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
    echo -e "${YELLOW}将使用默认配置，建议创建 .env 文件${NC}"
    echo ""
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 设置默认端口
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo -e "${GREEN}启动 FastAPI 后端服务...${NC}"
echo -e "${BLUE}地址:${NC} http://${HOST}:${PORT}"
echo -e "${BLUE}API文档:${NC} http://localhost:${PORT}/docs"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo ""

# 启动服务
if [ "$USE_UV" = true ]; then
    if [ -f ".env" ]; then
        uv run uvicorn src.api.app:app --host "$HOST" --port "$PORT" --reload --env-file .env
    else
        uv run uvicorn src.api.app:app --host "$HOST" --port "$PORT" --reload
    fi
else
    if [ -f ".env" ]; then
        uvicorn src.api.app:app --host "$HOST" --port "$PORT" --reload --env-file .env
    else
        uvicorn src.api.app:app --host "$HOST" --port "$PORT" --reload
    fi
fi

