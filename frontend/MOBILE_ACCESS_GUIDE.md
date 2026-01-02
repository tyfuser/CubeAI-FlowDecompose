# 📱 手机访问指南

## 问题

如果在电脑上使用 `localhost` 或 `127.0.0.1` 访问前端，生成的手机访问链接也会是 `localhost`，导致手机无法访问（因为手机的 `localhost` 指向手机自己，而不是你的电脑）。

## 解决方案

### 方法 1: 使用电脑的 IP 地址访问（推荐）

1. **获取电脑的 IP 地址**：

   **macOS/Linux:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   # 或者
   ip addr show | grep "inet " | grep -v 127.0.0.1
   ```

   **Windows:**
   ```bash
   ipconfig
   # 查找 IPv4 地址，通常是 192.168.x.x 或 10.x.x.x
   ```

2. **使用 IP 地址访问前端**：
   
   不要使用：
   - ❌ `http://localhost:3000`
   - ❌ `http://127.0.0.1:3000`
   
   应该使用：
   - ✅ `http://192.168.x.x:3000`（你的实际IP地址）
   - ✅ `http://10.x.x.x:3000`

3. **确保手机和电脑在同一网络**：
   - 手机和电脑必须连接到同一个 Wi-Fi 网络
   - 如果使用手机热点，需要确保电脑连接到手机热点

4. **防火墙设置**：
   - 确保防火墙允许 3000 端口（前端）和 8001 端口（Phone AI 后端）的入站连接

### 方法 2: 手动替换 URL（临时方案）

如果已经使用了 `localhost` 访问，可以在生成的二维码 URL 中手动替换：

1. 复制生成的 URL（例如：`http://localhost:3000/#/shooting-mobile/1CF8E323`）
2. 将 `localhost` 替换为你的电脑 IP 地址
3. 在手机浏览器中打开替换后的 URL

### 方法 3: 使用二维码生成工具

一些二维码生成工具可以自动检测并替换 localhost 为 IP 地址。

## 验证连接

1. **在手机上打开生成的 URL**
2. **检查浏览器控制台**（如果可能）：
   - 不应该有 "CONNECTION_REFUSED" 错误
   - WebSocket 连接应该成功

3. **测试摄像头访问**：
   - 点击"开始分析"按钮
   - 允许浏览器访问摄像头权限
   - 应该能看到摄像头画面

## 常见问题

### Q: 手机显示 "CONNECTION_REFUSED"

A: 
- 确保使用 IP 地址访问，而不是 localhost
- 确保手机和电脑在同一网络
- 检查防火墙设置
- 确保前端服务正在运行

### Q: 手机无法访问摄像头

A:
- 确保使用 HTTPS 访问（需要配置证书，见 [HTTPS_SETUP.md](./HTTPS_SETUP.md)）
- 或者使用 HTTP，但某些浏览器可能限制摄像头访问
- 检查浏览器权限设置

### Q: 如何找到我的 IP 地址？

A:
- **macOS**: `ifconfig | grep "inet " | grep -v 127.0.0.1`
- **Linux**: `ip addr show | grep "inet " | grep -v 127.0.0.1`
- **Windows**: `ipconfig` 然后查找 IPv4 地址

### Q: 手机和电脑不在同一网络怎么办？

A:
- 可以使用手机热点：
  1. 打开手机热点
  2. 电脑连接到手机热点
  3. 使用电脑的 IP 地址访问（热点网络中分配的 IP）
- 或者使用 ngrok 等内网穿透工具（高级用户）

## 推荐流程

1. **启动所有服务**：
   ```bash
   # 终端1: 主后端
   cd Backend/video_ai_demo && ./start.sh
   
   # 终端2: Phone AI后端
   cd Backend/phone_ai && export PORT=8001 && ./start_backend.sh
   
   # 终端3: 前端
   cd frontend && npm run dev
   ```

2. **获取电脑 IP 地址**

3. **使用 IP 地址访问前端**（例如：`http://192.168.1.100:3000`）

4. **扫描二维码或复制 URL 到手机**

5. **在手机上打开链接并允许摄像头权限**

## 相关文档

- [HTTPS 配置指南](./HTTPS_SETUP.md)
- [项目启动指南](../START_PROJECT.md)

