#!/bin/bash

# ==============================================
# Intuition-X 项目快速启动脚本
# ==============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║     🚀 Intuition-X 项目启动器           ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 获取 IP 地址
echo -e "${YELLOW}📍 检测网络配置...${NC}"
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

if [ -z "$LOCAL_IP" ]; then
    echo -e "${RED}❌ 无法获取本机 IP 地址${NC}"
    echo "请手动检查网络连接"
    exit 1
fi

echo -e "${GREEN}✓ 本机 IP: $LOCAL_IP${NC}"
echo ""

# 检查必要工具
echo -e "${YELLOW}🔍 检查依赖工具...${NC}"

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓ $1 已安装${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 未安装${NC}"
        return 1
    fi
}

ALL_DEPS_OK=true
check_command "node" || ALL_DEPS_OK=false
check_command "npm" || ALL_DEPS_OK=false
check_command "python3" || ALL_DEPS_OK=false
check_command "uvicorn" || ALL_DEPS_OK=false

if [ "$ALL_DEPS_OK" = false ]; then
    echo ""
    echo -e "${RED}❌ 缺少必要的依赖工具，请先安装${NC}"
    exit 1
fi

echo ""

# 检查证书
echo -e "${YELLOW}🔐 检查 HTTPS 证书...${NC}"
if [ -f "frontend/certs/localhost+3-key.pem" ] && [ -f "frontend/certs/localhost+3.pem" ]; then
    echo -e "${GREEN}✓ 证书文件存在${NC}"
else
    echo -e "${YELLOW}⚠️  证书文件不存在，正在生成...${NC}"
    cd frontend
    mkdir -p certs
    if command -v mkcert &> /dev/null; then
        mkcert -key-file certs/localhost+3-key.pem \
               -cert-file certs/localhost+3.pem \
               localhost 127.0.0.1 ::1 $LOCAL_IP
        echo -e "${GREEN}✓ 证书已生成${NC}"
    else
        echo -e "${RED}❌ mkcert 未安装，无法生成证书${NC}"
        echo "请安装 mkcert: brew install mkcert (macOS)"
        exit 1
    fi
    cd ..
fi

echo ""

# 检查 .env 文件
echo -e "${YELLOW}⚙️  检查配置文件...${NC}"
if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}⚠️  创建前端 .env 文件...${NC}"
    cat > frontend/.env << EOF
# API 配置
VITE_API_BASE_URL=http://${LOCAL_IP}:8000/api/v1
VITE_SHOT_ANALYSIS_BASE_URL=http://${LOCAL_IP}:8000
VITE_PHONE_AI_PORT=8001
VITE_API_TIMEOUT=30000

# 认证配置
VITE_TOKEN_KEY=rubik_token
VITE_REFRESH_TOKEN_KEY=rubik_refresh_token

# 功能开关
VITE_ENABLE_MOCK=false
VITE_ENABLE_API_LOG=true

# 业务配置
VITE_FREE_DAILY_QUOTA=5
VITE_MAX_FILE_SIZE=100
VITE_SUPPORTED_VIDEO_FORMATS=mp4,mov,avi,mkv
VITE_POLL_INTERVAL=2000
VITE_MAX_POLL_ATTEMPTS=60
EOF
    echo -e "${GREEN}✓ .env 文件已创建${NC}"
else
    # 更新 IP 地址
    sed -i '' "s/VITE_API_BASE_URL=http:\/\/.*:8000/VITE_API_BASE_URL=http:\/\/${LOCAL_IP}:8000/g" frontend/.env
    sed -i '' "s/VITE_SHOT_ANALYSIS_BASE_URL=http:\/\/.*:8000/VITE_SHOT_ANALYSIS_BASE_URL=http:\/\/${LOCAL_IP}:8000/g" frontend/.env
    echo -e "${GREEN}✓ .env 文件已更新${NC}"
fi

echo ""

# 询问启动方式
echo -e "${BLUE}请选择启动方式：${NC}"
echo "  1) 交互模式（3个独立终端窗口）- 推荐用于开发"
echo "  2) 后台模式（所有服务后台运行）- 快速测试"
echo "  3) 仅检查状态"
echo ""
read -p "请输入选项 (1/2/3): " CHOICE

case $CHOICE in
    1)
        echo ""
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo -e "${GREEN}🎯 交互模式启动说明${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo ""
        echo "请按以下步骤在 3 个终端中分别执行命令："
        echo ""
        echo -e "${YELLOW}【终端 1 - Video AI Demo】${NC}"
        echo "  cd $(pwd)/Backend/video_ai_demo"
        echo "  ./start.sh"
        echo ""
        echo -e "${YELLOW}【终端 2 - Phone AI】${NC}"
        echo "  cd $(pwd)/Backend/phone_ai"
        echo "  export PORT=8001"
        echo "  uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8001 --reload \\"
        echo "      --ssl-keyfile=\"../../frontend/certs/localhost+3-key.pem\" \\"
        echo "      --ssl-certfile=\"../../frontend/certs/localhost+3.pem\""
        echo ""
        echo -e "${YELLOW}【终端 3 - 前端】${NC}"
        echo "  cd $(pwd)/frontend"
        echo "  npm run dev"
        echo ""
        echo -e "${GREEN}访问地址：${NC}"
        echo "  电脑: https://${LOCAL_IP}:3000/"
        echo "  手机: 扫描页面二维码"
        echo ""
        ;;
    
    2)
        echo ""
        echo -e "${YELLOW}🚀 启动所有服务（后台模式）...${NC}"
        echo ""
        
        # 停止现有服务
        echo "停止现有服务..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
        sleep 2
        
        # 启动 Video AI Demo
        echo -e "${BLUE}▶️  启动 Video AI Demo (端口 8000)...${NC}"
        cd Backend/video_ai_demo
        nohup ./start.sh > ../../logs/video_ai_demo.log 2>&1 &
        cd ../..
        sleep 3
        
        # 启动 Phone AI
        echo -e "${BLUE}▶️  启动 Phone AI (端口 8001)...${NC}"
        cd Backend/phone_ai
        export PORT=8001
        nohup uv run uvicorn src.api.app:app \
            --host 0.0.0.0 \
            --port 8001 \
            --reload \
            --ssl-keyfile="../../frontend/certs/localhost+3-key.pem" \
            --ssl-certfile="../../frontend/certs/localhost+3.pem" \
            > ../../logs/phone_ai.log 2>&1 &
        cd ../..
        sleep 3
        
        # 启动前端
        echo -e "${BLUE}▶️  启动前端 (端口 3000)...${NC}"
        cd frontend
        nohup npm run dev > ../logs/frontend.log 2>&1 &
        cd ..
        
        sleep 5
        
        echo ""
        echo -e "${GREEN}✅ 所有服务已启动！${NC}"
        echo ""
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo -e "${GREEN}📱 访问信息${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo ""
        echo "  🌐 电脑访问: https://${LOCAL_IP}:3000/"
        echo "  📱 手机访问: 扫描页面二维码"
        echo ""
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo -e "${GREEN}📋 管理命令${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo ""
        echo "  查看状态: ./status.sh"
        echo "  停止服务: ./stop_all.sh"
        echo ""
        echo "  查看日志:"
        echo "    tail -f logs/video_ai_demo.log"
        echo "    tail -f logs/phone_ai.log"
        echo "    tail -f logs/frontend.log"
        echo ""
        ;;
    
    3)
        echo ""
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo -e "${GREEN}📊 服务状态${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo ""
        
        check_port() {
            PORT=$1
            NAME=$2
            if lsof -i:$PORT > /dev/null 2>&1; then
                echo -e "  ${GREEN}✓${NC} $NAME (端口 $PORT): ${GREEN}运行中${NC}"
            else
                echo -e "  ${RED}✗${NC} $NAME (端口 $PORT): ${RED}未运行${NC}"
            fi
        }
        
        check_port 3000 "前端服务      "
        check_port 8000 "Video AI Demo"
        check_port 8001 "Phone AI     "
        
        echo ""
        echo -e "${GREEN}访问地址: https://${LOCAL_IP}:3000/${NC}"
        echo ""
        ;;
    
    *)
        echo ""
        echo -e "${RED}无效的选项${NC}"
        exit 1
        ;;
esac

