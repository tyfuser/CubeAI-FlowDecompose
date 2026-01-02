#!/bin/bash

# Phone AI 后端启动脚本 (HTTPS 版本)

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Phone AI - 后端服务启动 (HTTPS)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查证书文件
CERT_DIR="../../frontend/certs"
KEY_FILE="$CERT_DIR/localhost+3-key.pem"
CERT_FILE="$CERT_DIR/localhost+3.pem"

if [ ! -f "$KEY_FILE" ] || [ ! -f "$CERT_FILE" ]; then
    echo -e "${RED}错误: 未找到 SSL 证书文件${NC}"
    echo -e "${YELLOW}证书位置: $CERT_DIR${NC}"
    echo -e "${YELLOW}请确保前端已生成证书（使用 mkcert）${NC}"
    echo ""
    echo -e "${BLUE}生成证书步骤：${NC}"
    echo "  cd ../../frontend"
    echo "  mkdir -p certs"
    echo "  LOCAL_IP=\$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print \$2}')"
    echo "  mkcert -key-file certs/localhost+3-key.pem -cert-file certs/localhost+3.pem localhost 127.0.0.1 ::1 \$LOCAL_IP"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ 找到 SSL 证书${NC}"

# 检查 uv
if command -v uv &> /dev/null; then
    echo -e "${GREEN}检测到 uv，使用 uv 管理环境${NC}"
    USE_UV=true
else
    echo -e "${YELLOW}未检测到 uv，使用传统 pip 方式${NC}"
    USE_UV=false
fi

if [ "$USE_UV" = true ]; then
    echo -e "${YELLOW}同步依赖（uv sync）...${NC}"
    uv sync
    echo -e "${GREEN}使用 uv 启动服务...${NC}"
else
    # 传统方式
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    python3 -c "import fastapi" 2>/dev/null || {
        echo -e "${YELLOW}依赖未安装，正在安装...${NC}"
        pip install -e ".[dev]"
    }
fi

# 设置默认端口
PORT=${PORT:-8001}
HOST=${HOST:-0.0.0.0}

# 获取本机 IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

echo -e "${GREEN}启动 FastAPI 后端服务 (HTTPS)...${NC}"
echo -e "${BLUE}地址:${NC} https://${HOST}:${PORT}"
echo -e "${BLUE}API文档:${NC} https://localhost:${PORT}/docs"
echo -e "${BLUE}网络访问:${NC} https://${LOCAL_IP}:${PORT}/docs"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo ""

# 启动服务 (带 SSL)
if [ "$USE_UV" = true ]; then
    if [ -f ".env" ] && [ -r ".env" ]; then
        uv run uvicorn src.api.app:app \
            --host "$HOST" \
            --port "$PORT" \
            --reload \
            --ssl-keyfile="$KEY_FILE" \
            --ssl-certfile="$CERT_FILE" \
            --env-file .env
    else
        uv run uvicorn src.api.app:app \
            --host "$HOST" \
            --port "$PORT" \
            --reload \
            --ssl-keyfile="$KEY_FILE" \
            --ssl-certfile="$CERT_FILE"
    fi
else
    if [ -f ".env" ] && [ -r ".env" ]; then
        uvicorn src.api.app:app \
            --host "$HOST" \
            --port "$PORT" \
            --reload \
            --ssl-keyfile="$KEY_FILE" \
            --ssl-certfile="$CERT_FILE" \
            --env-file .env
    else
        uvicorn src.api.app:app \
            --host "$HOST" \
            --port "$PORT" \
            --reload \
            --ssl-keyfile="$KEY_FILE" \
            --ssl-certfile="$CERT_FILE"
    fi
fi

