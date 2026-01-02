#!/bin/bash

# ==============================================
# 检查 Intuition-X 服务状态
# ==============================================

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║     📊 Intuition-X 服务状态             ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 获取 IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

check_port() {
    PORT=$1
    NAME=$2
    PROTOCOL=$3
    
    if lsof -i:$PORT > /dev/null 2>&1; then
        PID=$(lsof -ti:$PORT)
        echo -e "  ${GREEN}✓${NC} $NAME"
        echo -e "    端口: $PORT"
        echo -e "    协议: $PROTOCOL"
        echo -e "    PID:  $PID"
        echo -e "    状态: ${GREEN}运行中${NC}"
    else
        echo -e "  ${RED}✗${NC} $NAME"
        echo -e "    端口: $PORT"
        echo -e "    协议: $PROTOCOL"
        echo -e "    状态: ${RED}未运行${NC}"
    fi
    echo ""
}

check_port 3000 "前端服务       " "HTTPS"
check_port 8000 "Video AI Demo " "HTTP"
check_port 8001 "Phone AI      " "HTTPS/WSS"

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}📱 访问信息${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
echo -e "  本机 IP: ${YELLOW}$LOCAL_IP${NC}"
echo ""
echo "  🌐 电脑访问:"
echo "     https://$LOCAL_IP:3000/"
echo ""
echo "  📱 手机访问:"
echo "     https://$LOCAL_IP:3000/"
echo "     (或扫描页面二维码)"
echo ""
echo "  📖 API 文档:"
echo "     http://$LOCAL_IP:8000/docs  (Video AI)"
echo "     https://$LOCAL_IP:8001/docs (Phone AI)"
echo ""

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}🔧 管理命令${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
echo "  启动服务: ./start.sh"
echo "  停止服务: ./stop_all.sh"
echo "  查看状态: ./status.sh"
echo ""

# 检查日志文件
if [ -d "logs" ]; then
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}📋 日志文件${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
    
    for log in logs/*.log; do
        if [ -f "$log" ]; then
            SIZE=$(du -h "$log" | cut -f1)
            echo "  $(basename $log): $SIZE"
        fi
    done
    echo ""
    echo "  查看实时日志:"
    echo "    tail -f logs/frontend.log"
    echo "    tail -f logs/video_ai_demo.log"
    echo "    tail -f logs/phone_ai.log"
    echo ""
fi

