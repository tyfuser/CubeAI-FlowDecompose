<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Story Galaxy Controller

一个实时交互式故事体验系统：电脑端创建会话并显示二维码，手机扫码加入同一会话，后端每秒推送 action，手机 UI 根据 action 动态响应。

## 功能特性

- 🖥️ **电脑端控制台**：创建会话，显示二维码和加入链接
- 📱 **手机端界面**：扫码加入会话，实时接收并显示 action
- 🔄 **WebSocket 实时通信**：后端每秒推送一个 action 到所有连接的客户端
- 🎨 **动态 UI 响应**：根据不同的 action 类型（dialogue、alert、scan、input、success）显示不同的 UI 效果

## 快速开始

### 前置要求

- Node.js (v16+)
- **手机访问摄像头需要 HTTPS**（见下方说明）

### ⚠️ 重要：手机摄像头访问需要 HTTPS

现代浏览器（特别是移动端）要求使用 HTTPS 才能访问摄像头。如果使用 HTTP，会出现摄像头无法访问的错误。

**快速解决方案（推荐）：**

```bash
# 1. 设置 HTTPS（使用 Vite 内置 HTTPS，最简单）
# 编辑 vite.config.ts，添加 https: true
# 然后运行 ./start.sh

# 2. 或使用 mkcert（推荐，无警告）
./setup-https.sh    # 首次运行，生成证书
./start-https.sh     # 使用 HTTPS 启动
```

**详细说明请查看 [HTTPS_SETUP.md](./HTTPS_SETUP.md)**

### 方式一：使用启动脚本（HTTP，摄像头可能无法访问）

```bash
# 进入项目目录
cd story-galaxy-controller

# 运行启动脚本（会自动安装依赖并启动前后端）
./start.sh
```

启动脚本会自动：
1. 检查并安装前端依赖
2. 检查并安装后端依赖
3. 启动后端服务器（端口 8080）
4. 启动前端开发服务器（端口 3000）

### 方式二：使用 HTTPS 启动（推荐，支持摄像头）

```bash
# 首次运行：设置 HTTPS 证书
./setup-https.sh

# 之后使用 HTTPS 启动
./start-https.sh
```

### 方式二：手动启动

```bash
# 1. 安装前端依赖
npm install

# 2. 安装后端依赖
cd server
npm install
cd ..

# 3. 启动后端服务器（新终端窗口）
cd server
npm start
# 或
node index.js

# 4. 启动前端开发服务器（另一个终端窗口）
npm run dev
```

## 使用说明

1. **启动服务器**：运行 `./start.sh` 或手动启动前后端
2. **打开电脑端**：在浏览器中访问 `http://localhost:3000`
3. **创建会话**：点击 "INITIATE_SESSION" 按钮
4. **获取二维码**：页面会显示二维码和加入链接
5. **手机扫码**：用手机扫描二维码或直接打开显示的链接
6. **实时交互**：手机端会自动连接到会话，并每秒接收一个 action，UI 会根据 action 类型动态变化

## 项目结构

```
story-galaxy-controller/
├── components/          # React 组件
│   ├── ConsoleView.tsx  # 电脑端控制台视图
│   ├── MobileView.tsx   # 手机端视图
│   └── QRCode.tsx       # 二维码组件
├── server/              # 后端服务器
│   ├── index.js         # Express + WebSocket 服务器
│   └── package.json
├── services/            # 服务层
│   └── mockService.ts   # Session 服务
├── App.tsx              # 主应用组件
└── start.sh             # 启动脚本
```

## 技术栈

- **前端**：React 19 + TypeScript + Vite
- **后端**：Express + WebSocket (ws)
- **通信协议**：WebSocket + REST API

## 端口说明

- **前端开发服务器**：`http://localhost:3000`
- **后端服务器**：`http://localhost:8080`
- **WebSocket 连接**：`ws://localhost:8080`

## 停止服务器

如果使用启动脚本，按 `Ctrl+C` 即可停止所有服务器。

如果手动启动，需要在各自的终端窗口中按 `Ctrl+C` 停止。
