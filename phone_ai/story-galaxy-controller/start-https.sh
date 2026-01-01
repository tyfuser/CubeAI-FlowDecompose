#!/bin/bash

# Story Galaxy Controller HTTPS 启动脚本
# 使用 HTTPS 以支持摄像头访问

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Story Galaxy Controller (HTTPS)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查证书文件
if [ ! -f "localhost+3.pem" ] && [ ! -f "localhost+2.pem" ]; then
    CERT_FILE=$(ls localhost*.pem 2>/dev/null | head -1)
    if [ -z "$CERT_FILE" ]; then
        echo -e "${RED}未找到 SSL 证书文件！${NC}"
        echo -e "${YELLOW}请先运行 setup-https.sh 来生成证书${NC}"
        echo ""
        read -p "是否现在运行 setup-https.sh? [y/N]: " answer
        if [[ $answer =~ ^[Yy]$ ]]; then
            ./setup-https.sh
        else
            echo -e "${YELLOW}使用 HTTP 模式启动（摄像头可能无法访问）${NC}"
        fi
    fi
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到 Node.js，请先安装 Node.js${NC}"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}正在安装前端依赖...${NC}"
    npm install
fi

if [ ! -d "server/node_modules" ]; then
    echo -e "${YELLOW}正在安装后端依赖...${NC}"
    cd server && npm install && cd ..
fi

# 获取本机 IP
if command -v hostname &> /dev/null; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
elif command -v ip &> /dev/null; then
    LOCAL_IP=$(ip addr show | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' | cut -d/ -f1)
else
    LOCAL_IP="YOUR_IP"
fi

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在关闭服务器...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit
}

trap cleanup SIGINT SIGTERM EXIT

# 启动后端服务器
echo -e "${GREEN}启动后端服务器 (端口 8080)...${NC}"
cd server
node index.js &
BACKEND_PID=$!
cd ..

sleep 2

# 启动前端 HTTPS 服务器
echo -e "${GREEN}启动前端 HTTPS 服务器 (端口 3000)...${NC}"

# 检查是否有 HTTPS 配置文件
if [ -f "vite.config.https.ts" ]; then
    # 临时重命名配置文件
    mv vite.config.ts vite.config.http.ts.bak 2>/dev/null || true
    mv vite.config.https.ts vite.config.ts
    
    npm run dev &
    FRONTEND_PID=$!
    
    # 恢复原配置
    sleep 1
    mv vite.config.ts vite.config.https.ts
    mv vite.config.http.ts.bak vite.config.ts 2>/dev/null || true
else
    # 使用环境变量强制 HTTPS
    VITE_HTTPS=true npm run dev &
    FRONTEND_PID=$!
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 服务器已启动！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}前端 HTTPS 地址:${NC} https://localhost:3000"
if [ "$LOCAL_IP" != "YOUR_IP" ]; then
    echo -e "${GREEN}手机访问地址:${NC} https://${LOCAL_IP}:3000"
fi
echo -e "${GREEN}后端地址:${NC} http://localhost:8080"
echo ""
echo -e "${YELLOW}使用说明:${NC}"
echo "1. 在浏览器中打开 https://localhost:3000（电脑）"
echo "2. 手机访问 https://${LOCAL_IP}:3000"
echo "3. 首次访问可能显示证书警告，点击'高级'→'继续访问'"
echo "4. 点击 'INITIATE_SESSION' 创建会话并显示二维码"
echo "5. 用手机扫描二维码"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务器${NC}"
echo ""

wait

