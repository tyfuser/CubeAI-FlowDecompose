# 📱 AI 拍摄助手页面加载问题排查

## 快速诊断

运行诊断脚本：
```bash
./check_phone_ai.sh
```

## 常见问题及解决方案

### 1. 页面空白或加载不出来

**可能原因**：
- 浏览器控制台有 JavaScript 错误
- 网络请求失败
- WebSocket 连接失败

**排查步骤**：

1. **打开浏览器开发者工具**（F12）
   - 查看 Console 标签页的错误信息
   - 查看 Network 标签页的请求状态

2. **检查控制台错误**：
   ```javascript
   // 应该看到类似这样的日志：
   [API Config] VITE_API_BASE_URL: http://192.168.x.x:8000/api/v1
   [ShootingConsole] Connecting to wss://192.168.x.x:8001/api/realtime/session/xxx/ws
   ```

3. **检查网络请求**：
   - 打开 Network 标签页
   - 刷新页面
   - 查看是否有失败的请求（红色）
   - 特别关注：
     - `POST /api/realtime/session` - 创建会话
     - `WebSocket` 连接

### 2. WebSocket 连接失败

**错误信息**：
```
WebSocket connection to 'wss://...' failed
```

**可能原因**：
- 后端未使用 HTTPS 启动
- 证书问题
- 防火墙阻止

**解决方案**：

```bash
# 1. 确保 Phone AI 使用 HTTPS 启动
cd Backend/phone_ai
export PORT=8001
./start_backend_https.sh

# 2. 检查证书文件
ls -la ../../frontend/certs/

# 3. 检查防火墙
sudo ufw status
sudo ufw allow 8001/tcp
```

### 3. Mixed Content 错误

**错误信息**：
```
Mixed Content: The page was loaded over HTTPS, but requested an insecure resource
```

**原因**：
- 前端使用 HTTPS，但尝试连接 HTTP 后端

**解决方案**：
- 确保 Phone AI 使用 HTTPS 启动（已配置）
- 检查前端 `.env` 中的配置

### 4. CORS 错误

**错误信息**：
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

**解决方案**：
- 检查后端 CORS 配置
- 确保后端允许前端域名访问

### 5. 会话创建失败

**错误信息**：
```
Failed to create session
Backend unreachable, using local session
```

**排查步骤**：

```bash
# 1. 测试 API 端点
curl -k -X POST https://localhost:8001/api/realtime/session

# 2. 检查后端日志
# 查看启动 Phone AI 的终端窗口

# 3. 检查端口占用
lsof -i :8001
```

### 6. 页面路由问题

**检查路由配置**：
- 访问 `https://YOUR_IP:3000/#/shooting-assistant`
- 确保 URL 中包含 `#/shooting-assistant`

**如果路由不工作**：
- 检查 `App.tsx` 中的路由配置
- 确保 `AppSection.ShootingAssistant` 已正确配置

## 完整排查流程

### 步骤 1: 检查服务状态

```bash
# 检查所有服务
./status.sh

# 应该看到：
# ✓ 前端服务 (端口 3000): 运行中
# ✓ Video AI Demo (端口 8000): 运行中
# ✓ Phone AI (端口 8001): 运行中
```

### 步骤 2: 检查浏览器控制台

1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签页
3. 刷新页面
4. 查看错误信息

**正常情况应该看到**：
```
[API Config] VITE_API_BASE_URL: http://192.168.x.x:8000/api/v1
[ShootingConsole] Connecting to wss://192.168.x.x:8001/api/realtime/session/xxx/ws
[ShootingConsole] ✅ WebSocket connected
```

### 步骤 3: 检查网络请求

1. 打开 Network 标签页
2. 刷新页面
3. 查看请求状态：
   - ✅ 绿色：成功
   - ❌ 红色：失败

**关键请求**：
- `POST /api/realtime/session` - 应该返回 200
- `WebSocket` - 应该显示 "101 Switching Protocols"

### 步骤 4: 手动测试 API

```bash
# 测试创建会话
curl -k -X POST https://localhost:8001/api/realtime/session

# 应该返回：
# {"session_id":"...","ws_url":"...","message":"Session created successfully"}
```

### 步骤 5: 检查前端配置

```bash
# 检查 .env 文件
cat frontend/.env | grep VITE_PHONE_AI_PORT

# 应该看到：
# VITE_PHONE_AI_PORT=8001
```

## 调试技巧

### 1. 启用详细日志

在浏览器控制台运行：
```javascript
localStorage.setItem('debug', 'true');
// 然后刷新页面
```

### 2. 检查 WebSocket 连接

在浏览器控制台运行：
```javascript
// 检查 WebSocket 连接状态
const ws = new WebSocket('wss://YOUR_IP:8001/api/realtime/session/TEST/ws');
ws.onopen = () => console.log('✅ WebSocket 连接成功');
ws.onerror = (e) => console.error('❌ WebSocket 错误:', e);
ws.onclose = (e) => console.log('🔌 WebSocket 关闭:', e.code, e.reason);
```

### 3. 检查环境变量

在浏览器控制台运行：
```javascript
console.log('VITE_PHONE_AI_PORT:', import.meta.env.VITE_PHONE_AI_PORT);
console.log('Current hostname:', window.location.hostname);
console.log('Current protocol:', window.location.protocol);
```

## 常见错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|---------|
| 101 | WebSocket 协议切换成功 | ✅ 正常 |
| 400 | 请求格式错误 | 检查请求参数 |
| 404 | 端点不存在 | 检查 API 路径 |
| 500 | 服务器内部错误 | 查看后端日志 |
| ERR_CONNECTION_REFUSED | 连接被拒绝 | 检查后端是否运行 |
| ERR_SSL_PROTOCOL_ERROR | SSL 协议错误 | 检查证书配置 |

## 获取帮助

如果以上方法都无法解决问题：

1. **收集信息**：
   - 浏览器控制台的完整错误信息
   - Network 标签页的请求详情
   - 后端日志

2. **检查文档**：
   - [README.md](./README.md)
   - [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
   - [CONFIGURATION_GUIDE.md](./CONFIGURATION_GUIDE.md)

3. **运行诊断**：
   ```bash
   ./check_phone_ai.sh
   ```

## 快速修复命令

```bash
# 1. 重启所有服务
./stop_all.sh
./start.sh

# 2. 检查配置
./check_phone_ai.sh

# 3. 查看日志
tail -f logs/phone_ai.log
```

