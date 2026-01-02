#!/bin/bash

# ==============================================
# 停止所有 Intuition-X 服务
# ==============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🛑 正在停止所有服务...${NC}"
echo ""

stop_port() {
    PORT=$1
    NAME=$2
    
    PIDS=$(lsof -ti:$PORT 2>/dev/null)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}停止 $NAME (端口 $PORT)...${NC}"
        echo "$PIDS" | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✓ $NAME 已停止${NC}"
    else
        echo -e "${GREEN}✓ $NAME 未在运行${NC}"
    fi
}

stop_port 3000 "前端服务"
stop_port 8000 "Video AI Demo"
stop_port 8001 "Phone AI"

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo ""

