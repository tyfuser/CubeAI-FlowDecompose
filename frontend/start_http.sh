#!/bin/bash

# 使用 HTTP 启动前端（解决混合内容问题）

echo "==================================="
echo "启动前端服务 (HTTP 模式)"
echo "==================================="
echo ""
echo "⚠️  注意：此模式用于开发环境，当后端不支持 HTTPS 时使用"
echo ""

# 设置环境变量强制使用 HTTP
export FORCE_HTTP=true

# 启动服务
npm run dev


