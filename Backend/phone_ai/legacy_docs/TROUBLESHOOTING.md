# 🔧 故障排查指南

## 常见问题

### 1. 前端无法启动 - "Permission denied" 或 "Cannot find module"

**症状**：
```bash
sh: 1: vite: Permission denied
# 或
Error: Cannot find module @rollup/rollup-linux-x64-gnu
```

**解决方案**：
```bash
cd /mnt/data/CubeAI/phone_ai/story-galaxy-controller

# 清理并重新安装依赖
rm -rf node_modules package-lock.json
npm install
```

### 2. 端口被占用

**症状**：
- 启动时提示端口 3000 或 8080 已被占用

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :3000
lsof -i :8080

# 或使用
netstat -tlnp | grep -E ":(3000|8080)"

# 杀死进程
kill -9 <PID>
```

### 3. HTTPS 证书问题

**症状**：
- 浏览器显示证书警告
- 无法访问摄像头

**解决方案**：
```bash
cd /mnt/data/CubeAI/phone_ai/story-galaxy-controller

# 使用 mkcert 生成证书（推荐）
./setup-https.sh

# 然后使用 HTTPS 启动
./start-https.sh
```

### 4. 后端连接失败

**症状**：
- WebSocket 连接失败
- 前端无法连接到后端

**检查步骤**：
1. 确认后端服务器正在运行：
   ```bash
   ps aux | grep "node index.js"
   netstat -tlnp | grep 8080
   ```

2. 检查后端日志：
   ```bash
   cd story-galaxy-controller/server
   node index.js
   ```

3. 检查前端 WebSocket URL 配置是否正确

### 5. 摄像头无法访问

**症状**：
- 浏览器提示摄像头权限错误
- 无法打开摄像头

**解决方案**：
1. **必须使用 HTTPS**：
   ```bash
   USE_HTTPS=true ./start.sh
   ```

2. 检查浏览器权限：
   - Chrome: 设置 → 隐私和安全 → 网站设置 → 摄像头
   - 确保允许 localhost 访问摄像头

3. 首次访问时点击"继续访问"（自签名证书警告）

### 6. Python 后端连接问题

**症状**：
- Node.js 后端无法连接到 Python 后端
- AI 功能不工作

**检查步骤**：
1. 确认 Python 后端正在运行：
   ```bash
   ps aux | grep uvicorn
   curl http://localhost:8000/
   ```

2. 检查 Node.js 后端的 Python 后端配置

3. 查看 Python 后端日志

## 诊断命令

### 检查服务状态
```bash
# 检查所有相关进程
ps aux | grep -E "(node|vite|uvicorn)" | grep -v grep

# 检查端口占用
netstat -tlnp | grep -E ":(3000|8080|8000)"
# 或
ss -tlnp | grep -E ":(3000|8080|8000)"
```

### 检查依赖
```bash
# 前端依赖
cd story-galaxy-controller
npm list --depth=0

# 后端依赖
cd server
npm list --depth=0

# Python 依赖
cd ../..
uv pip list
```

### 查看日志
```bash
# Node.js 后端日志（如果在前台运行）
cd story-galaxy-controller/server
node index.js

# Python 后端日志（如果在前台运行）
cd ../..
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

## 完全重置

如果所有方法都失败，可以完全重置：

```bash
cd /mnt/data/CubeAI/phone_ai/story-galaxy-controller

# 1. 停止所有进程
pkill -f "node index.js"
pkill -f "vite"
pkill -f "uvicorn"

# 2. 清理前端依赖
rm -rf node_modules package-lock.json
npm install

# 3. 清理后端依赖
cd server
rm -rf node_modules package-lock.json
npm install
cd ..

# 4. 重新启动
USE_HTTPS=true ./start.sh
```

## 获取帮助

如果问题仍然存在，请提供：
1. 错误信息（完整输出）
2. 服务状态（`ps aux | grep -E "(node|vite)"`）
3. 端口占用情况（`netstat -tlnp | grep -E ":(3000|8080)"`）
4. 浏览器控制台错误（F12 → Console）

