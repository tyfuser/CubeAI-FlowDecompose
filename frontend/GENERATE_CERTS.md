# 🔐 生成 HTTPS 证书（可选）

## 为什么需要 HTTPS？

如果使用 **Phone AI 实时拍摄助手**功能，需要访问摄像头，现代浏览器要求使用 HTTPS 才能访问摄像头 API。

**注意**：如果只是开发测试主应用功能（不需要摄像头），可以使用 HTTP 模式，无需配置证书。

---

## 快速生成证书（使用 mkcert）

### 1. 安装 mkcert

**macOS:**
```bash
brew install mkcert
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt install mkcert

# 或使用 snap
sudo snap install mkcert
```

**Windows:**
```bash
# 使用 Chocolatey
choco install mkcert

# 或使用 Scoop
scoop bucket add extras
scoop install mkcert
```

### 2. 安装本地 CA

```bash
mkcert -install
```

### 3. 生成证书

```bash
cd frontend

# 确保 certs 目录存在
mkdir -p certs

# 获取本机 IP 地址（macOS）
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

# 生成证书（包含 localhost 和本机 IP）
mkcert -key-file certs/localhost+3-key.pem -cert-file certs/localhost+3.pem localhost 127.0.0.1 ::1 $LOCAL_IP
```

### 4. 验证

证书文件应该已生成：
```bash
ls -la certs/
# 应该看到：
# - localhost+3-key.pem (私钥)
# - localhost+3.pem (证书)
```

### 5. 重新启动前端

```bash
cd frontend
npm run dev
```

现在前端将使用 HTTPS 启动，访问 `https://localhost:3000` 或 `https://YOUR_IP:3000`

---

## 不使用 HTTPS（开发模式）

如果你**不需要摄像头功能**，可以跳过证书生成，直接使用 HTTP 模式：

```bash
cd frontend
npm run dev
```

访问 `http://localhost:3000` 即可。

**注意**：vite.config.ts 已配置为自动检测证书，如果证书不存在，会自动使用 HTTP 模式。

---

## 详细文档

更多信息请参考：[HTTPS_SETUP.md](../HTTPS_SETUP.md)

