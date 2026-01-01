#!/bin/bash

# Story Galaxy Controller 启动脚本
# 同时启动前端和后端服务器

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Story Galaxy Controller${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}错误: 未找到 Node.js，请先安装 Node.js${NC}"
    exit 1
fi

# 检查依赖是否已安装
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}正在安装前端依赖...${NC}"
    npm install
fi

if [ ! -d "server/node_modules" ]; then
    echo -e "${YELLOW}正在安装后端依赖...${NC}"
    cd server && npm install && cd ..
fi

# 清理函数：当脚本退出时杀死所有子进程
cleanup() {
    echo ""
    echo -e "${YELLOW}正在关闭服务器...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM EXIT

# 检查并清理旧进程
echo -e "${BLUE}检查端口占用情况...${NC}"

# 检查 8000 端口（Python 后端）
if command -v lsof &> /dev/null; then
    OLD_BACKEND_PIDS=$(lsof -ti :8000 2>/dev/null || true)
    if [ ! -z "$OLD_BACKEND_PIDS" ]; then
        echo -e "${YELLOW}发现占用 8000 端口的进程: ${OLD_BACKEND_PIDS}${NC}"
        echo -e "${YELLOW}正在停止旧进程...${NC}"
        kill $OLD_BACKEND_PIDS 2>/dev/null || true
        sleep 1
    fi
fi

# 检查 3000 端口（前端）
if command -v lsof &> /dev/null; then
    OLD_FRONTEND_PIDS=$(lsof -ti :3000 2>/dev/null || true)
    if [ ! -z "$OLD_FRONTEND_PIDS" ]; then
        echo -e "${YELLOW}发现占用 3000 端口的进程: ${OLD_FRONTEND_PIDS}${NC}"
        echo -e "${YELLOW}正在停止旧进程...${NC}"
        kill $OLD_FRONTEND_PIDS 2>/dev/null || true
        sleep 1
    fi
fi

# 启动 Python 后端服务器
echo -e "${GREEN}启动 Python 后端服务器 (端口 8000)...${NC}"
cd ..

# 检查是否有 SSL 证书（用于 WSS 支持）
CERT_FILE="./story-galaxy-controller/localhost+3.pem"
KEY_FILE="./story-galaxy-controller/localhost+3-key.pem"
USE_SSL=false

if [ "$USE_HTTPS" = "true" ] && [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo -e "${GREEN}🔒 检测到 SSL 证书，后端将支持 WSS${NC}"
    USE_SSL=true
    SSL_ARGS="--ssl-keyfile $KEY_FILE --ssl-certfile $CERT_FILE"
else
    echo -e "${YELLOW}⚠️  未找到 SSL 证书，后端仅支持 WS（HTTP）${NC}"
    SSL_ARGS=""
fi

if command -v uv &> /dev/null; then
    echo -e "${BLUE}使用 uv 启动 Python 后端...${NC}"
    if [ "$USE_SSL" = "true" ]; then
        uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload $SSL_ARGS > /tmp/python_backend.log 2>&1 &
    else
        uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload > /tmp/python_backend.log 2>&1 &
    fi
    BACKEND_PID=$!
    echo -e "${GREEN}Python 后端 PID: ${BACKEND_PID}${NC}"
    echo -e "${BLUE}后端日志: tail -f /tmp/python_backend.log${NC}"
else
    echo -e "${YELLOW}警告: 未找到 uv，尝试使用 python...${NC}"
    if [ "$USE_SSL" = "true" ]; then
        python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload $SSL_ARGS > /tmp/python_backend.log 2>&1 &
    else
        python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload > /tmp/python_backend.log 2>&1 &
    fi
    BACKEND_PID=$!
fi
cd story-galaxy-controller

# 等待后端启动
echo -e "${BLUE}等待后端启动...${NC}"
sleep 3
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Python 后端已启动 (PID: ${BACKEND_PID})${NC}"
else
    echo -e "${YELLOW}⚠️  后端可能启动失败，检查日志: tail -f /tmp/python_backend.log${NC}"
fi

# 启动前端开发服务器
echo -e "${GREEN}启动前端开发服务器 (端口 3000)...${NC}"

# 检查是否启用 HTTPS
if [ "$USE_HTTPS" = "true" ] || [ "$1" = "--https" ]; then
    echo -e "${GREEN}🔒 启用 HTTPS 模式（支持摄像头访问）${NC}"
    USE_HTTPS=true npm run dev 2>&1 | tee /tmp/frontend.log &
    FRONTEND_PID=$!
    echo -e "${GREEN}前端 PID: ${FRONTEND_PID}${NC}"
    echo -e "${BLUE}前端日志: tail -f /tmp/frontend.log${NC}"
else
    echo -e "${YELLOW}⚠️  使用 HTTP 模式（摄像头可能无法访问）${NC}"
    echo -e "${YELLOW}提示: 如需启用 HTTPS，运行: USE_HTTPS=true ./start.sh${NC}"
    npm run dev 2>&1 | tee /tmp/frontend.log &
    FRONTEND_PID=$!
    echo -e "${BLUE}前端日志: tail -f /tmp/frontend.log${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 服务器已启动！${NC}"
echo -e "${BLUE}========================================${NC}"
# 获取本机 IP
if command -v hostname &> /dev/null; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
elif command -v ip &> /dev/null; then
    LOCAL_IP=$(ip addr show | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' | cut -d/ -f1)
else
    LOCAL_IP="YOUR_IP"
fi

# 显示访问地址
if [ "$USE_HTTPS" = "true" ] || [ "$1" = "--https" ]; then
    echo -e "${GREEN}前端 HTTPS 地址:${NC} https://localhost:3000"
    if [ "$LOCAL_IP" != "YOUR_IP" ]; then
        echo -e "${GREEN}手机 HTTPS 访问:${NC} https://${LOCAL_IP}:3000"
        echo -e "${YELLOW}⚠️  首次访问会显示证书警告，点击'高级'→'继续访问'即可${NC}"
    fi
else
    echo -e "${GREEN}前端地址:${NC} http://localhost:3000"
    if [ "$LOCAL_IP" != "YOUR_IP" ]; then
        echo -e "${GREEN}手机访问:${NC} http://${LOCAL_IP}:3000"
    fi
fi
echo -e "${GREEN}后端地址:${NC} http://localhost:8000"
echo -e "${BLUE}后端日志:${NC} tail -f /tmp/python_backend.log"
echo ""
echo -e "${YELLOW}使用说明:${NC}"
if [ "$USE_HTTPS" = "true" ] || [ "$1" = "--https" ]; then
    echo "1. 在浏览器中打开 https://localhost:3000（电脑）"
    echo "2. 手机访问 https://${LOCAL_IP}:3000（首次访问点击'继续访问'）"
else
    echo "1. 在浏览器中打开 http://localhost:3000"
    echo "2. 手机访问 http://${LOCAL_IP}:3000"
fi
echo "3. 点击 'INITIATE_SESSION' 创建会话并显示二维码"
echo "4. 用手机扫描二维码或打开显示的链接"
echo "5. 手机端会自动连接到同一会话并接收实时 action 推送"
echo ""
if [ "$USE_HTTPS" != "true" ] && [ "$1" != "--https" ]; then
    echo -e "${YELLOW}⚠️  摄像头访问提示:${NC}"
    echo "手机访问摄像头需要 HTTPS。如果遇到摄像头错误："
    echo "- 方案1（最简单）: USE_HTTPS=true ./start.sh"
    echo "- 方案2（无警告）: ./setup-https.sh 然后 ./start-https.sh"
fi
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务器${NC}"
echo ""

# 等待所有后台进程
wait

