# HTTPS 配置指南（解决摄像头访问问题）

## 问题说明

现代浏览器（特别是移动端）要求使用 HTTPS 才能访问摄像头 API (`getUserMedia`)。如果使用 HTTP，会出现以下错误：
- `TypeError: Cannot read properties of undefined (reading 'getUserMedia')`
- 或权限被拒绝

## 解决方案

### 方案一：使用 mkcert（推荐，最简单）

`mkcert` 可以创建本地信任的 SSL 证书，无需手动添加信任。

#### 1. 安装 mkcert

**Linux:**
```bash
# 使用包管理器安装
sudo apt install mkcert  # Ubuntu/Debian
# 或
sudo yum install mkcert  # CentOS/RHEL

# 或使用 snap
sudo snap install mkcert

# 或从 GitHub 下载
wget https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v1.4.4-linux-amd64
chmod +x mkcert-v1.4.4-linux-amd64
sudo mv mkcert-v1.4.4-linux-amd64 /usr/local/bin/mkcert
```

**macOS:**
```bash
brew install mkcert
```

**Windows:**
```bash
# 使用 Chocolatey
choco install mkcert

# 或使用 Scoop
scoop bucket add extras
scoop install mkcert
```

#### 2. 安装本地 CA
```bash
mkcert -install
```

#### 3. 生成证书
```bash
cd /mnt/data/CubeAI/story-galaxy-controller

# 获取本机 IP 地址
LOCAL_IP=$(hostname -I | awk '{print $1}')

# 生成证书（包含 localhost 和本机 IP）
mkcert localhost 127.0.0.1 ::1 $LOCAL_IP

# 会生成两个文件：
# - localhost+3.pem (证书)
# - localhost+3-key.pem (私钥)
```

#### 4. 配置 Vite 使用 HTTPS

更新 `vite.config.ts`：
```typescript
import fs from 'fs';

export default defineConfig({
  server: {
    port: 3000,
    host: '0.0.0.0',
    https: {
      key: fs.readFileSync('./localhost+3-key.pem'),
      cert: fs.readFileSync('./localhost+3.pem'),
    },
  },
  // ... 其他配置
});
```

#### 5. 更新启动脚本

使用 `start-https.sh`（见下方）

### 方案二：使用 Vite 内置 HTTPS（自签名证书）

Vite 可以自动生成自签名证书，但浏览器会显示警告。

#### 1. 更新 vite.config.ts
```typescript
export default defineConfig({
  server: {
    port: 3000,
    host: '0.0.0.0',
    https: true,  // 自动生成自签名证书
  },
});
```

#### 2. 手机端操作
- 首次访问会显示"不安全连接"警告
- 点击"高级" → "继续访问"（或"Proceed to localhost"）
- 之后就可以正常使用摄像头了

### 方案三：Chrome 浏览器特殊配置（仅开发测试）

**⚠️ 仅用于开发测试，不推荐生产环境**

#### Chrome（桌面版）
1. 打开 `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
2. 在输入框中添加你的 IP 地址，例如：`http://192.168.1.100:3000`
3. 选择 "Enabled"
4. 重启浏览器

#### Chrome（Android）
1. 打开 Chrome
2. 在地址栏输入 `chrome://flags`
3. 搜索 `unsafely-treat-insecure-origin-as-secure`
4. 添加你的 IP 地址
5. 重启浏览器

### 方案四：Firefox 浏览器配置（仅开发测试）

1. 在地址栏输入 `about:config`
2. 搜索 `media.getusermedia.insecure.enabled`
3. 设置为 `true`
4. 重启浏览器

## 推荐配置流程

1. **安装 mkcert**（方案一）
2. **生成证书**
3. **更新 vite.config.ts**
4. **使用 HTTPS 启动脚本**

## 验证 HTTPS

启动后，访问 `https://YOUR_IP:3000`，浏览器地址栏应该显示锁图标 🔒，表示 HTTPS 连接成功。

## 常见问题

### Q: 证书生成后，手机仍然显示不安全？
A: 确保手机和电脑在同一网络，并且使用 IP 地址访问（不是 localhost）

### Q: 如何获取本机 IP？
```bash
# Linux
hostname -I | awk '{print $1}'
# 或
ip addr show | grep "inet " | grep -v 127.0.0.1

# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr IPv4
```

### Q: 端口被占用？
A: 修改 `vite.config.ts` 中的端口号，或使用 `--port` 参数

### Q: 防火墙阻止访问？
A: 确保防火墙允许 3000 和 8080 端口的入站连接

