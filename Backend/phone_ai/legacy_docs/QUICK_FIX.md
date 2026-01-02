# ⚡ 快速修复指南

## 问题：前端打不开

### 原因
npm 依赖安装不完整，缺少 `@rollup/rollup-linux-x64-gnu` 模块。

### 解决方案

```bash
cd /mnt/data/CubeAI/phone_ai/story-galaxy-controller

# 1. 清理依赖
rm -rf node_modules package-lock.json

# 2. 重新安装
npm install

# 3. 启动服务
USE_HTTPS=true ./start.sh
```

### 验证

启动后检查：
```bash
# 检查端口
netstat -tlnp | grep -E ":(3000|8080)"

# 应该看到：
# - 端口 3000：前端 (Vite)
# - 端口 8080：后端 (Node.js)
```

### 访问地址

- **前端**: https://localhost:3000 (HTTPS) 或 http://localhost:3000 (HTTP)
- **后端**: http://localhost:8080

**注意**：首次访问 HTTPS 会显示证书警告，点击"高级" → "继续访问"即可。

