#!/bin/bash

# Phone AI 连接诊断脚本

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}Phone AI 连接诊断${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

# 1. 检查 Phone AI 后端是否运行
echo -e "${YELLOW}1. 检查 Phone AI 后端状态...${NC}"
if lsof -i :8001 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Phone AI 后端正在运行（端口 8001）${NC}"
else
    echo -e "${RED}✗ Phone AI 后端未运行${NC}"
    echo "  请运行: cd Backend/phone_ai && export PORT=8001 && ./start_backend_https.sh"
    exit 1
fi

# 2. 检查 API 端点
echo ""
echo -e "${YELLOW}2. 测试 API 端点...${NC}"
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

# 测试 HTTPS API
echo -e "${BLUE}测试 https://localhost:8001/api/realtime/session${NC}"
RESPONSE=$(curl -k -s -X POST https://localhost:8001/api/realtime/session 2>&1)
if echo "$RESPONSE" | grep -q "session_id"; then
    echo -e "${GREEN}✓ API 端点正常${NC}"
    echo "  响应: $RESPONSE" | head -c 100
    echo ""
else
    echo -e "${RED}✗ API 端点异常${NC}"
    echo "  响应: $RESPONSE"
fi

# 3. 检查前端配置
echo ""
echo -e "${YELLOW}3. 检查前端配置...${NC}"
if [ -f "frontend/.env" ]; then
    PHONE_AI_PORT=$(grep "VITE_PHONE_AI_PORT" frontend/.env | cut -d'=' -f2 | tr -d ' ')
    if [ -n "$PHONE_AI_PORT" ]; then
        echo -e "${GREEN}✓ VITE_PHONE_AI_PORT=$PHONE_AI_PORT${NC}"
    else
        echo -e "${YELLOW}⚠️  VITE_PHONE_AI_PORT 未配置，将使用默认值 8001${NC}"
    fi
else
    echo -e "${RED}✗ frontend/.env 文件不存在${NC}"
fi

# 4. 检查证书
echo ""
echo -e "${YELLOW}4. 检查 HTTPS 证书...${NC}"
if [ -f "frontend/certs/localhost+3-key.pem" ] && [ -f "frontend/certs/localhost+3.pem" ]; then
    echo -e "${GREEN}✓ 证书文件存在${NC}"
else
    echo -e "${RED}✗ 证书文件不存在${NC}"
    echo "  请运行: cd frontend && mkcert -key-file certs/localhost+3-key.pem -cert-file certs/localhost+3.pem localhost 127.0.0.1 ::1 $LOCAL_IP"
fi

# 5. 检查前端服务
echo ""
echo -e "${YELLOW}5. 检查前端服务...${NC}"
if lsof -i :3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务正在运行（端口 3000）${NC}"
    echo "  访问地址:"
    echo "    - https://localhost:3000"
    echo "    - https://$LOCAL_IP:3000"
else
    echo -e "${RED}✗ 前端服务未运行${NC}"
    echo "  请运行: cd frontend && npm run dev"
fi

# 6. 诊断建议
echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}诊断建议${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
echo "如果页面加载不出来，请检查："
echo ""
echo "1. 浏览器控制台错误（F12 打开开发者工具）"
echo "2. 网络请求是否成功（Network 标签页）"
echo "3. WebSocket 连接是否建立（Console 中查看连接日志）"
echo ""
echo "常见问题："
echo "  - 如果看到 'Mixed Content' 错误："
echo "    前端使用 HTTPS，但后端 API 使用 HTTP"
echo "    解决方案：确保 Phone AI 使用 HTTPS 启动（已配置）"
echo ""
echo "  - 如果看到 'WebSocket connection failed'："
echo "    检查后端是否支持 WSS（WebSocket Secure）"
echo "    解决方案：确保使用 start_backend_https.sh 启动"
echo ""
echo "  - 如果看到 CORS 错误："
echo "    检查后端 CORS 配置"
echo ""
echo "访问地址："
echo "  前端: https://$LOCAL_IP:3000/#/shooting-assistant"
echo "  Phone AI API: https://$LOCAL_IP:8001/docs"

