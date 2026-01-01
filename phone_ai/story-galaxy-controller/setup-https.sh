#!/bin/bash

# HTTPS 证书设置脚本

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  HTTPS 证书设置${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否安装了 mkcert
if ! command -v mkcert &> /dev/null; then
    echo -e "${YELLOW}mkcert 未安装，正在安装...${NC}"
    echo ""
    echo "请选择安装方式："
    echo "1. 使用包管理器安装（推荐）"
    echo "2. 从 GitHub 下载"
    echo "3. 跳过（手动安装后重新运行此脚本）"
    read -p "请选择 [1-3]: " choice
    
    case $choice in
        1)
            if command -v apt &> /dev/null; then
                sudo apt update && sudo apt install -y mkcert
            elif command -v yum &> /dev/null; then
                sudo yum install -y mkcert
            elif command -v brew &> /dev/null; then
                brew install mkcert
            else
                echo -e "${RED}未找到支持的包管理器，请手动安装 mkcert${NC}"
                exit 1
            fi
            ;;
        2)
            echo "正在从 GitHub 下载 mkcert..."
            ARCH=$(uname -m)
            OS=$(uname -s | tr '[:upper:]' '[:lower:]')
            if [ "$ARCH" = "x86_64" ]; then
                ARCH="amd64"
            fi
            VERSION="v1.4.4"
            URL="https://github.com/FiloSottile/mkcert/releases/download/${VERSION}/mkcert-${VERSION}-${OS}-${ARCH}"
            wget -O /tmp/mkcert "$URL"
            chmod +x /tmp/mkcert
            sudo mv /tmp/mkcert /usr/local/bin/mkcert
            ;;
        3)
            echo -e "${YELLOW}请手动安装 mkcert 后重新运行此脚本${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            exit 1
            ;;
    esac
fi

echo -e "${GREEN}✓ mkcert 已安装${NC}"
echo ""

# 安装本地 CA
echo -e "${BLUE}正在安装本地 CA...${NC}"
mkcert -install
echo -e "${GREEN}✓ 本地 CA 已安装${NC}"
echo ""

# 获取本机 IP 地址
echo -e "${BLUE}正在获取本机 IP 地址...${NC}"
if command -v hostname &> /dev/null; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
elif command -v ip &> /dev/null; then
    LOCAL_IP=$(ip addr show | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}' | cut -d/ -f1)
else
    echo -e "${YELLOW}无法自动获取 IP，请输入本机 IP 地址：${NC}"
    read -p "IP 地址: " LOCAL_IP
fi

if [ -z "$LOCAL_IP" ]; then
    echo -e "${RED}无法获取 IP 地址${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 本机 IP: ${LOCAL_IP}${NC}"
echo ""

# 生成证书
echo -e "${BLUE}正在生成 SSL 证书...${NC}"
cd "$(dirname "$0")"
mkcert localhost 127.0.0.1 ::1 "$LOCAL_IP"

# 重命名证书文件（如果生成了多个）
if [ -f "localhost+3.pem" ]; then
    echo -e "${GREEN}✓ 证书已生成: localhost+3.pem${NC}"
elif [ -f "localhost+2.pem" ]; then
    echo -e "${GREEN}✓ 证书已生成: localhost+2.pem${NC}"
else
    # 查找最新的证书文件
    CERT_FILE=$(ls -t localhost*.pem 2>/dev/null | head -1)
    KEY_FILE=$(ls -t localhost*-key.pem 2>/dev/null | head -1)
    if [ -n "$CERT_FILE" ] && [ -n "$KEY_FILE" ]; then
        echo -e "${GREEN}✓ 证书已生成: $CERT_FILE${NC}"
    else
        echo -e "${RED}证书生成失败${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ HTTPS 设置完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步：${NC}"
echo "1. 使用 vite.config.https.ts 作为配置文件"
echo "2. 或运行 start-https.sh 启动 HTTPS 服务器"
echo ""
echo -e "${GREEN}手机访问地址:${NC} https://${LOCAL_IP}:3000"
echo ""

