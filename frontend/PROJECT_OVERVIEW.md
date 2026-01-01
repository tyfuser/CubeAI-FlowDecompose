# 魔方 AI - 前端项目文档

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![React](https://img.shields.io/badge/React-18.0-61dafb)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178c6)
![Vite](https://img.shields.io/badge/Vite-5.0-646cff)
![License](https://img.shields.io/badge/license-MIT-green)

**视频分析与创作辅助平台**

[快速开始](#-快速开始) • [功能模块](#-功能模块) • [开发指南](#-开发指南) • [API 文档](#-api-文档) • [部署](#-部署)

</div>

---

## 📋 目录

- [项目概述](#-项目概述)
- [核心特性](#-核心特性)
- [技术栈](#-技术栈)
- [快速开始](#-快速开始)
- [功能模块](#-功能模块)
- [项目结构](#-项目结构)
- [开发指南](#-开发指南)
- [API 文档](#-api-文档)
- [环境配置](#-环境配置)
- [部署](#-部署)
- [文档索引](#-文档索引)
- [团队协作](#-团队协作)

---

## 🎯 项目概述

魔方 AI 是一个专业的视频分析与创作辅助平台，集成了多种 AI 驱动的功能，帮助内容创作者分析视频特性、生成脚本、学习拍摄技巧。

### 核心价值

- 🎬 **视频分析** - AI 分析视频的爆款因素、节奏、钩子
- 📹 **镜头拆解** - 自动识别运镜、光线、调色技巧
- ✍️ **脚本生成** - AI 辅助生成跨平台创作脚本
- 📊 **数据可视化** - 直观展示分析结果
- 🎓 **学习平台** - 系统学习视频创作技巧

### 项目信息

| 项目 | 信息 |
|-----|------|
| **名称** | 魔方 AI (Rubik AI Engine) |
| **版本** | v2.0.0 |
| **前端框架** | React 18 + TypeScript |
| **构建工具** | Vite 5 |
| **UI 库** | Tailwind CSS |
| **状态管理** | React Hooks |
| **许可证** | MIT |

---

## ✨ 核心特性

### 1. 视频深度拆解

分析视频的爆款因素和创作技巧

**功能点**：
- ✅ URL / 文件上传
- ✅ AI 识别爆款因素
- ✅ 节奏曲线可视化
- ✅ 雷达图评分
- ✅ 钩子强度分析
- ✅ 实时进度显示

**技术实现**：
- 后端 AI 模型分析
- 轮询获取结果
- Recharts 图表展示

### 2. 镜头拆解分析 ⭐ 新功能

自动识别视频的拍摄技巧

**功能点**：
- ✅ 视频播放器集成
- ✅ 流式输出分析结果
- ✅ 时间轴可视化
- ✅ 运镜识别（特写、全景、推拉等）
- ✅ 光线识别（三点布光、自然光等）
- ✅ 调色识别（暖色调、冷色调等）
- ✅ 交互式详情查看
- ✅ 历史记录管理

**技术亮点**：
- 🎥 本地视频预览
- 🌊 实时流式输出
- 🎨 渐进式动画
- 🖱️ 点击跳转播放

### 3. 视频转幻灯片

将视频内容转换为演示文稿

**功能点**：
- ✅ 关键帧提取
- ✅ 智能内容总结
- ✅ 多种布局样式
- ✅ 导出演示文稿

### 4. 创作中心

AI 辅助脚本生成和编辑

**功能点**：
- ✅ 多种创作策略
- ✅ 跨平台适配
- ✅ 分镜可视化
- ✅ 实时编辑
- ✅ 导出脚本

### 5. 灵感仓库

知识管理和灵感收藏

**功能点**：
- ✅ 分类管理
- ✅ 标签系统
- ✅ 搜索过滤
- ✅ 笔记编辑

### 6. 总览面板

数据统计和项目管理

**功能点**：
- ✅ 统计数据展示
- ✅ 最近项目
- ✅ 日程热力图
- ✅ 快速入口

---

## 🛠 技术栈

### 前端核心

```json
{
  "框架": "React 18",
  "语言": "TypeScript 5",
  "构建工具": "Vite 5",
  "样式方案": "Tailwind CSS 3",
  "图标库": "Lucide React",
  "图表库": "Recharts",
  "HTTP 客户端": "Axios",
  "AI 模型": "Google Gemini"
}
```

### 开发工具

- **包管理器**: npm
- **代码规范**: ESLint + Prettier
- **类型检查**: TypeScript
- **版本控制**: Git

### 浏览器支持

- Chrome >= 90
- Firefox >= 88
- Safari >= 14
- Edge >= 90

---

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd frontend

# 2. 安装依赖
npm install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 API 地址

# 4. 启动开发服务器
npm run dev
```

### 访问应用

打开浏览器访问：http://localhost:3000

### 默认账号

```
用户名：demo
密码：demo123
```

---

## 📦 功能模块

### 模块架构

```
frontend/
├── 核心模块
│   ├── Dashboard          总览面板
│   ├── Analysis           视频深度拆解
│   ├── ShotAnalysis       镜头拆解分析 ⭐ 新
│   ├── Editor             创作中心
│   ├── VideoSlideshow     视频转幻灯片
│   ├── KnowledgeBase      灵感仓库
│   └── Discovery          发现爆款
│
├── 通用模块
│   ├── Login              登录认证
│   ├── Settings           系统设置
│   └── Sidebar            侧边导航
│
└── 服务层
    ├── api                API 客户端
    ├── analysisService    分析服务
    ├── dashboardService   仪表板服务
    ├── videoAnalysisService  镜头拆解服务
    └── geminiService      AI 服务
```

### 路由配置

| 路径 | 组件 | 功能 |
|-----|------|------|
| `/` | Dashboard | 总览面板 |
| `/analysis` | AnalysisPanel | 视频深度拆解 |
| `/shot-analysis` | ShotAnalysis | 镜头拆解分析 ⭐ |
| `/editor` | Editor | 创作中心 |
| `/slideshow` | VideoSlideshow | 视频转幻灯片 |
| `/kb` | KnowledgeBase | 灵感仓库 |
| `/discovery` | Discovery | 发现爆款 |
| `/settings` | Settings | 系统设置 |

---

## 📁 项目结构

```
frontend/
├── public/                    # 静态资源
├── src/
│   ├── components/           # React 组件
│   │   ├── Dashboard.tsx     # 总览面板
│   │   ├── AnalysisPanel.tsx # 视频分析
│   │   ├── ShotAnalysis.tsx  # 镜头拆解 ⭐
│   │   ├── Editor.tsx        # 脚本编辑器
│   │   ├── VideoSlideshow.tsx # 幻灯片
│   │   ├── KnowledgeBase.tsx # 知识库
│   │   ├── Discovery.tsx     # 发现页
│   │   ├── Login.tsx         # 登录
│   │   ├── Settings.tsx      # 设置
│   │   └── Sidebar.tsx       # 侧边栏
│   │
│   ├── services/            # API 服务层
│   │   ├── api.ts           # Axios 实例
│   │   ├── analysisService.ts      # 分析 API
│   │   ├── dashboardService.ts     # 仪表板 API
│   │   ├── videoAnalysisService.ts # 镜头拆解 API ⭐
│   │   └── geminiService.ts        # AI 服务
│   │
│   ├── types.ts             # TypeScript 类型定义
│   ├── App.tsx              # 主应用组件
│   ├── index.tsx            # 入口文件
│   └── index.css            # 全局样式
│
├── docs/                    # 文档目录
│   ├── API_COMPATIBILITY.md          # API 兼容性 ⭐
│   ├── API_DOCUMENTATION.md          # API 文档
│   ├── SHOT_ANALYSIS_GUIDE.md        # 镜头拆解指南
│   ├── SHOT_ANALYSIS_NEW_FEATURES.md # 新功能说明
│   ├── ENV_CONFIG.md                 # 环境配置
│   ├── BACKEND_SETUP_REQUIRED.md     # 后端配置
│   └── TROUBLESHOOTING.md            # 故障排查
│
├── .env                     # 环境变量
├── .gitignore              # Git 忽略
├── package.json            # 依赖配置
├── tsconfig.json           # TS 配置
├── vite.config.ts          # Vite 配置
└── README.md               # 项目说明
```

---

## 💻 开发指南

### 开发命令

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 类型检查
npm run type-check

# 代码格式化
npm run format

# Lint 检查
npm run lint
```

### 代码规范

#### 组件命名

```typescript
// ✅ 好的命名
const Dashboard: React.FC = () => { ... }
const ShotAnalysis: React.FC = () => { ... }

// ❌ 不好的命名
const dashboard: React.FC = () => { ... }
const shot_analysis: React.FC = () => { ... }
```

#### 文件组织

```typescript
// 组件文件结构
import React, { useState, useEffect } from 'react';
import { SomeType } from '../types';
import { someService } from '../services/someService';

// 1. 类型定义
interface Props {
  ...
}

// 2. 组件定义
const Component: React.FC<Props> = ({ ... }) => {
  // 2.1 状态定义
  const [state, setState] = useState();
  
  // 2.2 副作用
  useEffect(() => { ... }, []);
  
  // 2.3 事件处理
  const handleClick = () => { ... };
  
  // 2.4 渲染
  return ( ... );
};

// 3. 导出
export default Component;
```

#### 样式规范

使用 Tailwind CSS utility classes：

```tsx
// ✅ 好的用法
<div className="flex items-center justify-between p-4 bg-gray-900 rounded-lg">
  <h3 className="text-lg font-bold text-white">标题</h3>
  <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded">
    按钮
  </button>
</div>

// ❌ 避免内联样式
<div style={{ display: 'flex', padding: '16px' }}>
  ...
</div>
```

### Git 工作流

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发并提交
git add .
git commit -m "feat: 添加新功能"

# 3. 推送到远程
git push origin feature/new-feature

# 4. 创建 Pull Request
```

### Commit 规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构代码
perf: 性能优化
test: 测试相关
chore: 构建/工具相关
```

---

## 🔌 API 文档

### API 架构

前端与两个独立的后端服务通信：

```
Frontend (localhost:3000)
    ↓
    ├─→ Backend API 1 (localhost:8000/api/v1)
    │   ├─ Dashboard
    │   ├─ Analysis
    │   └─ Projects
    │
    └─→ Backend API 2 (localhost:8000/v1/video-analysis)
        └─ Shot Analysis
```

### API 格式兼容 ⭐

前端支持两种后端响应格式：

**格式 1：code 格式**
```json
{
  "code": 0,
  "data": { ... },
  "message": "成功"
}
```

**格式 2：success 格式**
```json
{
  "success": true,
  "data": { ... }
}
```

### 核心 API

#### 视频分析

```typescript
// 创建分析
POST /api/v1/analysis/create
{
  "url": "https://...",
  "platform": "auto"
}

// 查询状态
GET /api/v1/analysis/{id}/status

// 获取结果
GET /api/v1/analysis/{id}
```

#### 镜头拆解 ⭐

```typescript
// 创建任务
POST /v1/video-analysis/jobs
{
  "mode": "learn",
  "target_video": {
    "source": {
      "type": "file",
      "path": "/path/to/video.mp4"
    }
  }
}

// 查询状态（轮询）
GET /v1/video-analysis/jobs/{job_id}

// 响应（流式）
{
  "status": "running",
  "progress": { ... },
  "partial_result": { ... }  // 实时更新
}
```

详细 API 文档：[API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## ⚙️ 环境配置

### .env 配置

```env
# ============ API 配置 ============

# 原有功能的后端服务（Dashboard、分析等）
VITE_API_BASE_URL=http://localhost:8000/api/v1

# 镜头拆解功能的后端服务
VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000

# API 超时时间（毫秒）
VITE_API_TIMEOUT=30000

# ============ 功能开关 ============

# 是否启用 Mock 数据
VITE_ENABLE_MOCK=false

# 是否启用 API 日志
VITE_ENABLE_API_LOG=true

# ============ 业务配置 ============

# 每日免费配额
VITE_FREE_DAILY_QUOTA=5

# 最大文件大小（MB）
VITE_MAX_FILE_SIZE=100

# 支持的视频格式
VITE_SUPPORTED_VIDEO_FORMATS=mp4,mov,avi,mkv

# 轮询间隔（毫秒）
VITE_POLL_INTERVAL=2000

# 最大轮询次数
VITE_MAX_POLL_ATTEMPTS=60
```

### 环境变量说明

| 变量 | 说明 | 默认值 |
|-----|------|--------|
| `VITE_API_BASE_URL` | 主 API 地址 | - |
| `VITE_SHOT_ANALYSIS_BASE_URL` | 镜头拆解 API | `http://localhost:8000` |
| `VITE_API_TIMEOUT` | 请求超时 | 30000 |
| `VITE_ENABLE_MOCK` | Mock 模式 | false |
| `VITE_ENABLE_API_LOG` | API 日志 | true |

详细配置文档：[ENV_CONFIG.md](ENV_CONFIG.md)

---

## 🚢 部署

### 构建生产版本

```bash
# 1. 构建
npm run build

# 2. 生成产物在 dist/ 目录
ls dist/
```

### 部署到 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/frontend/dist;
    index index.html;
    
    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 部署到 Vercel

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 部署
vercel

# 3. 配置环境变量（在 Vercel Dashboard）
VITE_API_BASE_URL=https://api.your-domain.com/v1
```

### Docker 部署

```dockerfile
# Dockerfile
FROM node:18-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```bash
# 构建镜像
docker build -t rubik-ai-frontend .

# 运行容器
docker run -p 3000:80 rubik-ai-frontend
```

---

## 📚 文档索引

### 使用文档

| 文档 | 说明 |
|-----|------|
| [README.md](README.md) | 项目简介 |
| [SHOT_ANALYSIS_GUIDE.md](SHOT_ANALYSIS_GUIDE.md) | 镜头拆解使用指南 |
| [SHOT_ANALYSIS_NEW_FEATURES.md](SHOT_ANALYSIS_NEW_FEATURES.md) | 新功能详解 |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 快速参考 |

### 技术文档

| 文档 | 说明 |
|-----|------|
| [API_COMPATIBILITY.md](API_COMPATIBILITY.md) | API 兼容性 ⭐ |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | API 规范 |
| [FRONTEND_INTEGRATION_GUIDE.md](FRONTEND_INTEGRATION_GUIDE.md) | 集成指南 |
| [ENV_CONFIG.md](ENV_CONFIG.md) | 环境配置 |

### 运维文档

| 文档 | 说明 |
|-----|------|
| [BACKEND_SETUP_REQUIRED.md](BACKEND_SETUP_REQUIRED.md) | 后端配置 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 故障排查 |
| [INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md) | 集成总结 |

---

## 👥 团队协作

### 开发流程

1. **需求评审** - 确认功能需求
2. **技术设计** - 设计技术方案
3. **开发实现** - 编写代码
4. **代码审查** - Pull Request Review
5. **测试验证** - 功能测试
6. **部署上线** - 发布生产环境

### 分支策略

```
main          生产分支（稳定版本）
  ↓
develop       开发分支（最新功能）
  ↓
feature/*     功能分支
hotfix/*      热修复分支
```

### 代码审查清单

- [ ] 代码符合规范
- [ ] 类型定义完整
- [ ] 无 ESLint 警告
- [ ] 无 TypeScript 错误
- [ ] 功能测试通过
- [ ] 文档已更新

---

## 🐛 问题反馈

### 常见问题

1. **无法连接后端**
   - 检查 `.env` 配置
   - 确认后端服务运行
   - 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

2. **视频上传失败**
   - 检查文件大小限制
   - 确认文件格式支持
   - 查看后端日志

3. **分析结果不显示**
   - 检查 API 响应格式
   - 查看浏览器控制台
   - 参考 [API_COMPATIBILITY.md](API_COMPATIBILITY.md)

### 获取帮助

- 📖 查看文档：[文档索引](#-文档索引)
- 🐛 提交 Issue：GitHub Issues
- 💬 技术讨论：团队频道

---

## 📊 项目统计

### 代码统计

```
Languages:
  TypeScript:    85%
  CSS:           10%
  JavaScript:     3%
  Other:          2%

Components:     12 个
Services:        5 个
Types:         200+ 个
Lines of Code: 8000+
```

### 功能覆盖

- ✅ 视频深度拆解: 100%
- ✅ 镜头拆解分析: 100% ⭐
- ✅ 视频转幻灯片: 100%
- ✅ 创作中心: 100%
- ✅ 灵感仓库: 100%
- ⏳ Dashboard: 80%（需后端 API）

---

## 🎉 更新日志

### v2.0.0 (2025-01-02) ⭐

**新增功能**：
- ✨ 镜头拆解分析功能
- ✨ 视频播放器集成
- ✨ 流式输出支持
- ✨ API 兼容性增强

**改进优化**：
- 🎨 UI/UX 全面优化
- 🚀 性能提升
- 📚 文档完善

**Bug 修复**：
- 🐛 修复文件上传问题
- 🐛 修复 API 响应格式兼容
- 🐛 修复类型定义

### v1.0.0 (2024-12-01)

**初始版本**：
- ✅ 视频深度拆解
- ✅ 视频转幻灯片
- ✅ AI 脚本生成
- ✅ 知识库管理

---

## 📄 许可证

MIT License

Copyright (c) 2025 Rubik AI

---

## 🙏 致谢

感谢以下开源项目：

- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)
- [Recharts](https://recharts.org/)
- [Axios](https://axios-http.com/)

---

<div align="center">

**魔方 AI - 让视频创作更简单** ✨

Made with ❤️ by Rubik AI Team

[开始使用](#-快速开始) • [查看文档](#-文档索引) • [反馈问题](#-问题反馈)

</div>

