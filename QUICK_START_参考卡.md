# 🚀 Intuition-X 快速启动参考卡

## 📦 一键启动（推荐新手）

```bash
cd Intuition-X
./start.sh
```

选择模式：
- **1** - 交互模式（显示3个终端命令，适合开发）
- **2** - 后台模式（一键启动所有服务，适合测试）
- **3** - 查看状态

---

## 🎯 手动启动（3个终端）

### 终端 1: Video AI Demo
```bash
cd Intuition-X/Backend/video_ai_demo
./start.sh
```

### 终端 2: Phone AI
```bash
cd Intuition-X/Backend/phone_ai
export PORT=8001
uv run uvicorn src.api.app:app \
    --host 0.0.0.0 --port 8001 --reload \
    --ssl-keyfile="../../frontend/certs/localhost+3-key.pem" \
    --ssl-certfile="../../frontend/certs/localhost+3.pem"
```

### 终端 3: 前端
```bash
cd Intuition-X/frontend
npm run dev
```

---

## 📊 服务管理

```bash
# 查看状态
./status.sh

# 停止所有服务
./stop_all.sh

# 查看日志
tail -f logs/frontend.log
tail -f logs/video_ai_demo.log
tail -f logs/phone_ai.log
```

---

## 🌐 访问地址

| 用途 | 地址 | 说明 |
|------|------|------|
| **电脑访问** | `https://192.168.43.226:3000/` | 将 IP 替换为你的 |
| **手机访问** | 扫描页面二维码 | 或手动输入 HTTPS 地址 |
| **API 文档** | `http://YOUR_IP:8000/docs` | Video AI Demo |
| **API 文档** | `https://YOUR_IP:8001/docs` | Phone AI |

---

## ⚡ 常用命令

```bash
# 获取本机 IP
ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}'

# 检查端口占用
lsof -i:3000  # 前端
lsof -i:8000  # Video AI
lsof -i:8001  # Phone AI

# 杀死进程
kill -9 <PID>

# 查看所有服务
lsof -i:3000,8000,8001
```

---

## 🔧 首次配置

### 1. 生成证书
```bash
cd Intuition-X/frontend
mkdir -p certs
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
mkcert -key-file certs/localhost+3-key.pem \
       -cert-file certs/localhost+3.pem \
       localhost 127.0.0.1 ::1 $LOCAL_IP
```

### 2. 配置 .env
```bash
cd Intuition-X/frontend
nano .env
```

更新以下内容（将 IP 替换为你的）：
```
VITE_API_BASE_URL=http://192.168.43.226:8000/api/v1
VITE_SHOT_ANALYSIS_BASE_URL=http://192.168.43.226:8000
```

---

## ❌ 故障排查

| 问题 | 解决方案 |
|------|---------|
| 端口被占用 | `lsof -ti:8001 \| xargs kill -9` |
| 证书错误 | 重新生成证书或浏览器选择"继续访问" |
| CONNECTION_REFUSED | 检查 `.env` 中的 IP 是否正确 |
| Dashboard 无数据 | 确认 Video AI Demo (8000) 在运行 |
| WebSocket 失败 | 确认 Phone AI (8001) 使用 HTTPS |
| 手机无法访问 | 确认手机和电脑在同一 Wi-Fi |

---

## 📱 手机访问步骤

1. **电脑访问**: `https://YOUR_IP:3000/`
2. **进入拍摄页面**（Phone AI）
3. **扫描二维码**
4. **手机信任证书**（首次）
5. **允许摄像头权限**
6. ✅ **开始使用**

---

## 🏗️ 服务架构

```
前端 (3000 HTTPS)
  ├─→ Video AI Demo (8000 HTTP) - Dashboard 数据
  └─→ Phone AI (8001 HTTPS/WSS) - 实时拍摄指导
```

---

## 📖 详细文档

完整攻略请查看：`项目启动完整攻略.md`

---

**快速获取帮助**: `./start.sh` 选项 3 查看服务状态

