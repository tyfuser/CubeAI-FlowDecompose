#!/bin/bash

# ==============================================
# Cube AI - 统一环境配置脚本
# ==============================================
# 自动配置项目所需的所有环境依赖
# 支持 uv（推荐）和传统 pip 两种方式

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║     🔧 Cube AI 环境配置脚本            ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# 获取本机 IP 地址
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' 2>/dev/null || echo "localhost")

# 检查命令是否存在
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

# ==============================================
# 步骤 1: 检查系统依赖
# ==============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}步骤 1: 检查系统依赖${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

ALL_DEPS_OK=true

# 检查 Python
if check_command "python3"; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "  Python 版本: $PYTHON_VERSION"
    
    # 检查 Python 版本是否 >= 3.9
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    PYTHON_PATCH=$(echo $PYTHON_VERSION | cut -d. -f3)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        echo -e "${RED}错误: 需要 Python 3.9+，当前版本: $PYTHON_VERSION${NC}"
        ALL_DEPS_OK=false
    elif [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -eq 13 ]; then
        echo -e "${YELLOW}⚠️  检测到 Python 3.13，某些依赖可能需要更新版本${NC}"
        echo -e "${YELLOW}   如果遇到构建错误，建议使用 Python 3.12 或更新依赖版本${NC}"
    fi
else
    ALL_DEPS_OK=false
fi

# 检查 Node.js
if check_command "node"; then
    NODE_VERSION=$(node --version)
    echo "  Node.js 版本: $NODE_VERSION"
    
    # 检查 Node.js 版本是否 >= 16
    NODE_MAJOR=$(echo $NODE_VERSION | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -lt 16 ]; then
        echo -e "${RED}错误: 需要 Node.js 16+，当前版本: $NODE_VERSION${NC}"
        ALL_DEPS_OK=false
    fi
else
    ALL_DEPS_OK=false
fi

# 检查 npm
check_command "npm" || ALL_DEPS_OK=false

# 检查 FFmpeg
check_command "ffmpeg" || ALL_DEPS_OK=false

# 检查 ffprobe
check_command "ffprobe" || echo -e "${YELLOW}⚠️  ffprobe 未找到（通常与 ffmpeg 一起安装）${NC}"

if [ "$ALL_DEPS_OK" = false ]; then
    echo ""
    echo -e "${RED}❌ 缺少必要的系统依赖，请先安装${NC}"
    echo ""
    echo "安装指南："
    echo "  Python 3.9+: https://www.python.org/downloads/"
    echo "  Node.js 16+: https://nodejs.org/"
    echo "  FFmpeg:"
    echo "    macOS: brew install ffmpeg"
    echo "    Ubuntu: sudo apt install ffmpeg"
    exit 1
fi

echo ""

# ==============================================
# 步骤 2: 安装/检查 uv
# ==============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}步骤 2: 配置 Python 依赖管理工具${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version)
    echo -e "${GREEN}✓ uv 已安装 (${UV_VERSION})${NC}"
    USE_UV=true
else
    echo -e "${YELLOW}未检测到 uv${NC}"
    echo -e "${YELLOW}是否安装 uv？（推荐，可大幅提升依赖安装速度）${NC}"
    read -p "安装 uv? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        echo -e "${YELLOW}正在安装 uv...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
        # 添加到 PATH
        if [ -f "$HOME/.cargo/env" ]; then
            source "$HOME/.cargo/env"
        fi
        
        # 验证安装
        if command -v uv &> /dev/null; then
            echo -e "${GREEN}✓ uv 安装成功${NC}"
            USE_UV=true
        else
            echo -e "${YELLOW}⚠️  uv 安装完成，但需要重新加载 shell 环境${NC}"
            echo -e "${YELLOW}请运行: source ~/.cargo/env${NC}"
            USE_UV=false
        fi
    else
        echo -e "${YELLOW}跳过 uv 安装，将使用传统 pip 方式${NC}"
        USE_UV=false
    fi
fi

echo ""

# ==============================================
# 步骤 3: 配置 Phone AI 后端
# ==============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}步骤 3: 配置 Phone AI 后端${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

cd Backend/phone_ai

if [ "$USE_UV" = true ]; then
    echo -e "${YELLOW}使用 uv 同步依赖...${NC}"
    uv sync
    echo -e "${GREEN}✓ Phone AI 依赖已配置${NC}"
else
    echo -e "${YELLOW}使用 pip 安装依赖...${NC}"
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        python3 -m venv venv
    fi
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    if [ -f "pyproject.toml" ]; then
        pip install -e ".[dev]"
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    echo -e "${GREEN}✓ Phone AI 依赖已配置${NC}"
fi

cd ../..

echo ""

# ==============================================
# 步骤 4: 配置 Video AI Demo 后端
# ==============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}步骤 4: 配置 Video AI Demo 后端${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

cd Backend/video_ai_demo

if [ "$USE_UV" = true ] && [ -f "pyproject.toml" ]; then
    echo -e "${YELLOW}使用 uv 同步依赖...${NC}"
    if uv sync; then
        echo -e "${GREEN}✓ Video AI Demo 依赖已配置${NC}"
    else
        echo -e "${YELLOW}⚠️  uv sync 失败，尝试使用 pip 回退方案...${NC}"
        # 回退到 pip
        if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
            python3 -m venv venv
        fi
        
        if [ -d "venv" ]; then
            source venv/bin/activate
        elif [ -d ".venv" ]; then
            source .venv/bin/activate
        fi
        
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
            echo -e "${GREEN}✓ Video AI Demo 依赖已配置（使用 pip）${NC}"
        else
            echo -e "${RED}错误: 未找到 requirements.txt，无法回退${NC}"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}使用 pip 安装依赖...${NC}"
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        python3 -m venv venv
    fi
    
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    echo -e "${GREEN}✓ Video AI Demo 依赖已配置${NC}"
fi

# 创建数据目录
mkdir -p data

# 检查 .env 文件
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${YELLOW}创建 .env 文件（从 .env.example）...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  请编辑 .env 文件，填入 MM_LLM_API_KEY${NC}"
    else
        echo -e "${YELLOW}⚠️  未找到 .env.example，请手动创建 .env 文件${NC}"
    fi
fi

cd ../..

echo ""

# ==============================================
# 步骤 5: 配置前端
# ==============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}步骤 5: 配置前端${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

cd frontend

# 安装 Node.js 依赖
echo -e "${YELLOW}安装 Node.js 依赖...${NC}"
npm install
echo -e "${GREEN}✓ Node.js 依赖已安装${NC}"

# 生成 HTTPS 证书
echo ""
echo -e "${YELLOW}检查 HTTPS 证书...${NC}"
if [ ! -f "certs/localhost+3-key.pem" ] || [ ! -f "certs/localhost+3.pem" ]; then
    if command -v mkcert &> /dev/null; then
        echo -e "${YELLOW}生成 HTTPS 证书...${NC}"
        mkdir -p certs
        
        # 获取本机 IP
        LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' 2>/dev/null || echo "localhost")
        
        mkcert -key-file certs/localhost+3-key.pem \
               -cert-file certs/localhost+3.pem \
               localhost 127.0.0.1 ::1 ${LOCAL_IP}
        echo -e "${GREEN}✓ 证书已生成${NC}"
    else
        echo -e "${YELLOW}⚠️  mkcert 未安装，跳过证书生成${NC}"
        echo -e "${YELLOW}安装方法:${NC}"
        echo "  macOS: brew install mkcert"
        echo "  Linux: 需要手动安装 mkcert"
        echo ""
        echo -e "${YELLOW}注意: 没有证书，前端将使用 HTTP 模式（摄像头功能可能受限）${NC}"
    fi
else
    echo -e "${GREEN}✓ 证书文件已存在${NC}"
fi

# 创建 .env 文件
echo ""
echo -e "${YELLOW}检查前端 .env 文件...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}创建 .env 文件...${NC}"
    cat > .env << EOF
# API 配置（使用本机 IP，不要用 localhost）
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
    echo -e "${YELLOW}⚠️  请确认 IP 地址是否正确: ${LOCAL_IP}${NC}"
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
    # 检查是否需要更新 IP
    if grep -q "localhost" .env; then
        echo -e "${YELLOW}⚠️  .env 文件中使用了 localhost，建议改为本机 IP: ${LOCAL_IP}${NC}"
    fi
fi

cd ..

echo ""

# ==============================================
# 步骤 6: 创建日志目录
# ==============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}步骤 6: 创建日志目录${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

mkdir -p logs
echo -e "${GREEN}✓ 日志目录已创建${NC}"

echo ""

# ==============================================
# 完成
# ==============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ 环境配置完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}📋 下一步：${NC}"
echo ""
echo "1. 配置 API 密钥："
echo "   - 编辑 Backend/video_ai_demo/.env"
echo "   - 填入 MM_LLM_API_KEY"
echo ""
echo "2. 启动服务："
echo "   方式 1: 使用统一启动脚本"
echo "     ./start.sh"
echo ""
echo "   方式 2: 手动启动（3个终端）"
echo "     终端 1: cd Backend/video_ai_demo && ./start.sh"
echo "     终端 2: cd Backend/phone_ai && export PORT=8001 && ./start_backend_https.sh"
echo "     终端 3: cd frontend && npm run dev"
echo ""
echo -e "${BLUE}📱 访问地址：${NC}"
echo "   前端: https://${LOCAL_IP}:3000/"
echo "   Video AI API: http://${LOCAL_IP}:8000/docs"
echo "   Phone AI API: https://${LOCAL_IP}:8001/docs"
echo ""

