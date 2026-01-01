# Cube AI 魔方 AI - 项目总文档

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/Frontend-React-61dafb)

**智能视频分析与创作辅助平台**

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [技术架构](#-技术架构) • [部署指南](#-部署指南) • [开发文档](#-开发文档)

</div>

---

## 📖 目录

- [项目概述](#-项目概述)
- [核心价值](#-核心价值)
- [功能特性](#-功能特性)
- [技术架构](#-技术架构)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
- [部署指南](#-部署指南)
- [API 文档](#-api-文档)
- [开发文档](#-开发文档)
- [使用指南](#-使用指南)
- [常见问题](#-常见问题)
- [更新日志](#-更新日志)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🎯 项目概述

**CubeAI (魔方 AI)** 是一个专业的视频分析与创作辅助平台，利用多模态AI技术，帮助内容创作者深度分析视频特性、学习拍摄技巧、生成创作脚本，提升视频创作效率和质量。

### 项目信息

| 项目 | 信息 |
|------|------|
| **名称** | CubeAI-X / 魔方 AI (Rubik AI Engine) |
| **版本** | v2.0.0 |
| **状态** | ✅ 生产就绪 |
| **开发模式** | 前后端分离 |
| **后端框架** | FastAPI (Python 3.9+) |
| **前端框架** | React 18 + TypeScript |
| **AI 模型** | Qwen2.5-VL, Google Gemini |
| **许可证** | MIT |

### 适用场景

- 🎬 **视频创作者** - 学习爆款视频技巧
- 📹 **摄影师** - 分析运镜、打光、调色
- ✍️ **编剧/导演** - AI 辅助脚本创作
- 🎓 **教育机构** - 视频制作教学
- 📊 **数据分析师** - 视频内容研究

---

## 💡 核心价值

### 1. 🎯 智能视频分析
- AI 驱动的视频内容理解
- 自动识别爆款因素
- 多维度评分体系
- 可视化分析结果

### 2. 📹 专业镜头拆解
- 自动镜头切分检测
- 运镜技巧识别（推拉摇移跟等）
- 光线布局分析（三点布光、自然光等）
- 调色风格识别（色调、饱和度等）

### 3. ✍️ AI 创作辅助
- 智能脚本生成
- 跨平台内容适配
- 分镜可视化编辑
- 创作策略推荐

### 4. 📚 知识库管理
- 影视技巧收藏
- 创意灵感管理
- 标签分类系统
- 快速检索功能

---

## ✨ 功能特性

### 🎬 视频深度拆解

**功能描述**：全面分析视频的爆款因素和创作特点

**核心能力**：
- ✅ 支持 URL 和本地文件上传
- ✅ 爆款因素智能识别
- ✅ 节奏曲线可视化
- ✅ 钩子强度分析
- ✅ 雷达图多维评分
- ✅ 实时进度跟踪

**技术实现**：
- 多模态 AI 模型分析
- 异步任务处理
- 结果数据可视化

---

### 📹 镜头拆解分析 ⭐ 新功能

**功能描述**：专业级镜头语言分析和学习工具

**核心能力**：

#### 1. 镜头切分
- 自动识别镜头边界
- 精确到毫秒级时间戳
- 支持各类切换方式

#### 2. 运镜识别
- **推镜** (Push In) - 向主体推进
- **拉镜** (Pull Out) - 远离主体
- **摇镜** (Pan) - 水平旋转
- **移镜** (Track) - 横向/纵向移动
- **跟镜** (Follow) - 跟随主体
- **固定机位** (Static) - 无运动
- **组合运镜** - 复杂运动分析

#### 3. 光线分析
- **三点布光** - 主光、辅光、轮廓光
- **自然光** - 窗光、室外光
- **侧光** - 侧面照明
- **逆光** - 背光效果
- **顶光/底光** - 特殊光位
- **柔光/硬光** - 光质分析

#### 4. 调色识别
- **暖色调** - 橙黄色系
- **冷色调** - 蓝绿色系
- **中性色调** - 平衡色彩
- **高饱和度** - 鲜艳色彩
- **低饱和度** - 素雅风格
- **高对比度** - 明暗分明
- **低对比度** - 柔和过渡

**交互特性**：
- 🎥 内置视频播放器
- 🌊 实时流式输出
- 🎨 时间轴可视化
- 🖱️ 点击跳转播放
- 📝 详细特征说明
- 💾 历史记录管理

---

### 📊 视频转幻灯片

**功能描述**：将视频内容自动转换为演示文稿

**核心能力**：
- ✅ 智能关键帧提取
- ✅ 内容自动总结
- ✅ 多种布局模板
- ✅ 支持导出 PPT

---

### ✍️ 创作中心

**功能描述**：AI 辅助的视频脚本创作工具

**核心能力**：
- ✅ 多种创作策略
  - 故事叙述型
  - 知识分享型
  - 产品展示型
  - 情感共鸣型
- ✅ 跨平台适配
  - 抖音 / TikTok
  - B站 / YouTube
  - 小红书
  - 视频号
- ✅ 分镜可视化
- ✅ 实时编辑预览
- ✅ 脚本导出

---

### 📚 灵感仓库

**功能描述**：影视技巧和创意灵感管理系统

**核心能力**：
- ✅ 知识点分类
  - 钩子技巧
  - 叙事结构
  - 风格参考
  - 配乐方案
  - 指纹识别
- ✅ 标签系统
- ✅ 搜索过滤
- ✅ 收藏管理
- ✅ 笔记编辑

---

### 📈 总览面板

**功能描述**：数据统计和项目管理中心

**核心能力**：
- ✅ 统计数据展示
  - 已分析视频数
  - 生成脚本数
  - 知识库条目
  - 今日配额
- ✅ 最近项目列表
- ✅ 日程热力图
- ✅ 快速操作入口

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户浏览器                            │
│                     (Chrome/Firefox/Safari)                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        前端应用层                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React 18 + TypeScript + Vite                        │  │
│  │  - UI 组件 (12个核心组件)                             │  │
│  │  - 状态管理 (React Hooks)                            │  │
│  │  - 路由系统 (客户端路由)                              │  │
│  │  - API 服务层 (5个服务模块)                           │  │
│  └──────────────────────────────────────────────────────┘  │
│           Tailwind CSS │ Lucide Icons │ Recharts            │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API / JSON
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        后端服务层                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI (Python 3.9+)                                │  │
│  │                                                        │  │
│  │  API 路由层                                            │  │
│  │  ├─ routes_auth.py        认证/授权                   │  │
│  │  ├─ routes_dashboard.py   仪表板数据                  │  │
│  │  ├─ routes_analysis.py    视频分析                    │  │
│  │  ├─ routes_jobs.py        任务管理                    │  │
│  │  ├─ routes_knowledge.py   知识库                      │  │
│  │  └─ routes_user.py        用户管理                    │  │
│  │                                                        │  │
│  │  核心业务层                                            │  │
│  │  ├─ Pipeline 编排器       任务流程编排                 │  │
│  │  ├─ 视频处理步骤          抽帧/分析/对比               │  │
│  │  ├─ AI 集成层            多模态LLM调用                 │  │
│  │  └─ 数据仓储层           数据库操作                   │  │
│  │                                                        │  │
│  │  支持服务层                                            │  │
│  │  ├─ 认证系统 (JWT)                                    │  │
│  │  ├─ 配置管理 (Pydantic)                               │  │
│  │  ├─ 错误处理                                          │  │
│  │  ├─ 日志系统                                          │  │
│  │  └─ JSON Schema 校验                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬───────────────────────┬────────────────────────┘
             │                       │
             ▼                       ▼
┌──────────────────────┐  ┌──────────────────────────────────┐
│    数据存储层         │  │       外部服务集成                 │
│                      │  │                                   │
│  ┌────────────────┐ │  │  ┌──────────────────────────┐    │
│  │  SQLite / PG   │ │  │  │  Qwen2.5-VL              │    │
│  │  - 任务表      │ │  │  │  多模态视觉理解           │    │
│  │  - 用户表      │ │  │  └──────────────────────────┘    │
│  │  - 资源表      │ │  │                                   │
│  │  - 知识库表    │ │  │  ┌──────────────────────────┐    │
│  └────────────────┘ │  │  │  Google Gemini           │    │
│                      │  │  │  AI 内容生成             │    │
│  ┌────────────────┐ │  │  └──────────────────────────┘    │
│  │  文件系统      │ │  │                                   │
│  │  - 上传视频    │ │  │  ┌──────────────────────────┐    │
│  │  - 抽帧图片    │ │  │  │  FFmpeg                  │    │
│  │  - 关键帧      │ │  │  │  视频处理工具             │    │
│  │  - 预览视频    │ │  │  └──────────────────────────┘    │
│  └────────────────┘ │  │                                   │
└──────────────────────┘  └───────────────────────────────────┘
```

### 技术栈详情

#### 前端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **框架** | React | 18.x | UI 框架 |
| **语言** | TypeScript | 5.x | 类型安全 |
| **构建** | Vite | 6.x | 构建工具 |
| **样式** | Tailwind CSS | 3.x | 样式方案 |
| **图标** | Lucide React | 0.562 | 图标库 |
| **图表** | Recharts | 3.6 | 数据可视化 |
| **HTTP** | Axios | 1.13 | API 请求 |
| **AI** | Google Gemini | 1.34 | AI 服务 |

#### 后端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **框架** | FastAPI | 0.109 | Web 框架 |
| **服务器** | Uvicorn | 0.27 | ASGI 服务器 |
| **语言** | Python | 3.9+ | 开发语言 |
| **数据验证** | Pydantic | 2.6 | 数据校验 |
| **数据库** | SQLAlchemy | 2.0 | ORM |
| **HTTP 客户端** | httpx | 0.26 | 异步 HTTP |
| **视频处理** | FFmpeg | - | 视频处理 |
| **CV 分析** | OpenCV | 4.9 | 计算机视觉 |
| **场景检测** | PySceneDetect | 0.6.3 | 镜头切分 |
| **认证** | PyJWT | 2.8 | JWT Token |
| **AI 模型** | Qwen2.5-VL | - | 多模态理解 |

---

## 📁 项目结构

```
Cube AI/
│
├── Backend/                          # 后端服务
│   └── video_ai_demo/
│       ├── app/                      # 应用代码
│       │   ├── api/                  # API 路由
│       │   │   ├── routes_auth.py           认证路由
│       │   │   ├── routes_dashboard.py      仪表板路由
│       │   │   ├── routes_analysis.py       分析路由
│       │   │   ├── routes_jobs.py           任务路由
│       │   │   ├── routes_knowledge.py      知识库路由
│       │   │   ├── routes_terminology.py    术语路由
│       │   │   ├── routes_user.py           用户路由
│       │   │   └── routes_virtual_motion.py 虚拟运镜路由
│       │   │
│       │   ├── core/                 # 核心模块
│       │   │   ├── auth.py                  JWT 认证
│       │   │   ├── config.py                配置管理
│       │   │   ├── errors.py                错误定义
│       │   │   ├── json_schema.py           Schema 校验
│       │   │   ├── logging.py               日志系统
│       │   │   ├── response.py              统一响应
│       │   │   └── shot_terminology.py      镜头术语
│       │   │
│       │   ├── db/                   # 数据库层
│       │   │   ├── models.py                ORM 模型
│       │   │   ├── repo.py                  仓储层
│       │   │   └── session.py               数据库会话
│       │   │
│       │   ├── pipeline/             # 处理流水线
│       │   │   ├── orchestrator.py          任务编排器
│       │   │   └── steps/                   处理步骤
│       │   │       ├── ingest.py               视频摄取
│       │   │       ├── extract_frames.py       抽帧
│       │   │       ├── scene_detect.py         场景检测
│       │   │       ├── mm_llm_decompose.py     LLM 分析
│       │   │       ├── format_analysis.py      格式化
│       │   │       ├── artifacts.py            产物生成
│       │   │       ├── compare_map.py          对比映射
│       │   │       └── improve_steps.py        改进建议
│       │   │
│       │   ├── integrations/         # 外部集成
│       │   │   ├── mm_llm_client.py          多模态 LLM
│       │   │   └── img2video_client.py       图生视频
│       │   │
│       │   ├── main.py               # 主程序入口
│       │   └── plugins/              # 插件系统
│       │
│       ├── data/                     # 数据目录
│       │   ├── demo.db                      SQLite 数据库
│       │   ├── uploads/                     上传文件
│       │   └── jobs/                        任务数据
│       │
│       ├── tests/                    # 测试代码
│       ├── examples/                 # 示例代码
│       ├── requirements.txt          # Python 依赖
│       ├── start.sh                  # 启动脚本
│       ├── .env.example              # 环境变量示例
│       │
│       └── 📚 文档/
│           ├── README.md                    后端说明
│           ├── PROJECT_SUMMARY.md           项目总结
│           ├── QUICKSTART.md                快速入门
│           ├── API_GUIDE.md                 API 指南
│           ├── DEPLOYMENT.md                部署指南
│           └── ...                          更多文档
│
├── frontend/                         # 前端应用
│   ├── components/                   # React 组件
│   │   ├── Dashboard.tsx                 总览面板
│   │   ├── AnalysisPanel.tsx             视频分析
│   │   ├── ShotAnalysis.tsx              镜头拆解 ⭐
│   │   ├── Editor.tsx                    脚本编辑器
│   │   ├── VideoSlideshow.tsx            视频幻灯片
│   │   ├── KnowledgeBase.tsx             知识库
│   │   ├── Discovery.tsx                 发现页
│   │   ├── Login.tsx                     登录
│   │   ├── Settings.tsx                  设置
│   │   ├── Sidebar.tsx                   侧边栏
│   │   └── ProfileModal.tsx              个人资料
│   │
│   ├── services/                     # API 服务层
│   │   ├── api.ts                        Axios 实例
│   │   ├── analysisService.ts            分析 API
│   │   ├── dashboardService.ts           仪表板 API
│   │   ├── videoAnalysisService.ts       镜头拆解 API ⭐
│   │   ├── knowledgeService.ts           知识库 API
│   │   └── geminiService.ts              Gemini AI
│   │
│   ├── types.ts                      # TypeScript 类型
│   ├── App.tsx                       # 主应用组件
│   ├── index.tsx                     # 入口文件
│   ├── index.html                    # HTML 模板
│   ├── index.css                     # 全局样式
│   │
│   ├── package.json                  # Node 依赖
│   ├── tsconfig.json                 # TS 配置
│   ├── vite.config.ts                # Vite 配置
│   ├── .env.example                  # 环境变量示例
│   │
│   └── 📚 文档/
│       ├── README.md                     前端说明
│       ├── PROJECT_OVERVIEW.md           项目总览
│       ├── QUICK_START.md                快速开始
│       ├── API_COMPATIBILITY.md          API 兼容性 ⭐
│       ├── API_DOCUMENTATION.md          API 文档
│       ├── SHOT_ANALYSIS_GUIDE.md        镜头拆解指南
│       ├── ENV_CONFIG.md                 环境配置
│       ├── TROUBLESHOOTING.md            故障排查
│       └── ...                           更多文档
│
└── 📄 PROJECT_README.md              # 项目总文档（本文件）
```

---

## 🚀 快速开始

### 环境要求

#### 系统要求
- **操作系统**: macOS / Linux / Windows
- **内存**: 最低 4GB，推荐 8GB+
- **磁盘空间**: 最低 10GB（用于视频存储）

#### 软件依赖

**后端**:
- Python 3.9+
- FFmpeg (包含 ffprobe)
- pip

**前端**:
- Node.js 16+
- npm 或 yarn

### 安装步骤

#### 1️⃣ 克隆项目

```bash
git clone <repository-url>
cd Cube AI
```

#### 2️⃣ 后端配置

```bash
# 进入后端目录
cd Backend/video_ai_demo

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 FFmpeg
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# 配置环境变量
cp .env.example .env

# 编辑 .env 文件
nano .env
```

**.env 配置示例**:

```env
# 多模态 LLM 配置（必需）
MM_LLM_BASE_URL=https://www.sophnet.com/api/open-apis/v1
MM_LLM_API_KEY=your_api_key_here
MM_LLM_MODEL=Qwen2.5-VL-7B-Instruct

# 数据存储
DATA_DIR=./data
SQLITE_PATH=./data/demo.db

# FFmpeg 路径
FFMPEG_BIN=ffmpeg
FFPROBE_BIN=ffprobe

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# JWT 密钥（生产环境务必修改）
SECRET_KEY=your-secret-key-change-in-production
```

#### 3️⃣ 前端配置

```bash
# 进入前端目录
cd ../../frontend

# 安装 Node.js 依赖
npm install

# 配置环境变量
cp env.example.txt .env

# 编辑 .env 文件
nano .env
```

**.env 配置示例**:

```env
# API 配置
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000

# Gemini API（可选，用于 AI 功能）
GEMINI_API_KEY=your_gemini_api_key

# 功能开关
VITE_ENABLE_MOCK=false
VITE_ENABLE_API_LOG=true

# 业务配置
VITE_FREE_DAILY_QUOTA=5
VITE_MAX_FILE_SIZE=100
VITE_POLL_INTERVAL=2000
```

#### 4️⃣ 启动服务

**启动后端**:

```bash
cd Backend/video_ai_demo

# 方式 1：使用启动脚本
./start.sh

# 方式 2：直接启动
uvicorn app.main:app --reload --port 8000

# 方式 3：Python 模块方式
python -m app.main
```

后端服务将在 `http://localhost:8000` 启动

**启动前端**:

```bash
cd frontend

# 开发模式
npm run dev
```

前端应用将在 `http://localhost:3000` 启动

#### 5️⃣ 访问应用

1. **前端应用**: http://localhost:3000
2. **后端 API 文档**: http://localhost:8000/docs
3. **默认账号**:
   - 邮箱: 任意邮箱
   - 密码: `demo123`

---

## 🎮 使用指南

### 视频深度拆解

1. 登录系统
2. 进入「总览面板」或「视频分析」
3. 输入视频 URL 或上传本地文件
4. 等待 AI 分析（通常 1-3 分钟）
5. 查看分析结果：
   - 爆款因素雷达图
   - 节奏曲线
   - 钩子强度
   - 详细评分

### 镜头拆解分析 ⭐

1. 点击侧边栏「镜头拆解分析」
2. 上传视频文件
   - 支持格式: MP4, MOV, AVI 等
   - 最大 100MB
3. 等待 AI 分析（自动场景检测 + 多模态理解）
4. 查看结果：
   - **时间轴视图**: 可视化镜头序列
   - **运镜分析**: 每个镜头的运镜类型
   - **光线分析**: 光线布局和类型
   - **调色分析**: 色调和风格
5. 交互操作：
   - 点击片段 → 跳转到视频对应位置
   - 查看详情 → 展开特征详细说明
   - 历史记录 → 查看之前的分析

### 脚本创作

1. 完成视频分析后，进入「创作中心」
2. 选择创作策略：
   - 故事叙述型
   - 知识分享型
   - 产品展示型
   - 情感共鸣型
3. 选择目标平台（抖音/B站/小红书等）
4. AI 自动生成分镜脚本
5. 手动调整和优化
6. 导出脚本

### 知识库管理

1. 进入「灵感仓库」
2. 浏览不同分类：
   - 钩子技巧
   - 叙事结构
   - 风格参考
   - 配乐方案
   - 指纹识别
3. 搜索关键词
4. 收藏感兴趣的内容
5. 添加笔记和标签

---

## 🚢 部署指南

### 开发环境

已在上面「快速开始」中说明。

### 生产环境部署

#### 后端部署

**方式 1: 使用 Docker**

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 安装 FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建镜像
docker build -t Cube AI-backend .

# 运行容器
docker run -d -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e MM_LLM_API_KEY=your_key \
  Cube AI-backend
```

**方式 2: 使用 Systemd（Linux）**

```ini
# /etc/systemd/system/intuition-backend.service
[Unit]
Description=Cube AI Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/Cube AI/Backend/video_ai_demo
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable intuition-backend
sudo systemctl start intuition-backend
sudo systemctl status intuition-backend
```

**方式 3: 使用 Nginx + Gunicorn**

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### 前端部署

**方式 1: 静态文件部署**

```bash
# 构建生产版本
npm run build

# 产物在 dist/ 目录
ls dist/
```

**Nginx 配置**:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/Cube AI/frontend/dist;
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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**方式 2: 使用 Docker**

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
# 构建和运行
docker build -t Cube AI-frontend .
docker run -d -p 3000:80 Cube AI-frontend
```

**方式 3: 部署到 Vercel**

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署
vercel

# 配置环境变量（在 Vercel Dashboard）
VITE_API_BASE_URL=https://api.your-domain.com/v1
```

#### Docker Compose 一键部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./Backend/video_ai_demo
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - MM_LLM_API_KEY=${MM_LLM_API_KEY}
      - SQLITE_PATH=/app/data/demo.db
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
    restart: always

volumes:
  data:
```

```bash
# 启动全部服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 📡 API 文档

### API 概览

```
后端 API 架构:

/api/v1/                        # 新版 API（推荐）
├── /auth/login                     用户登录
├── /auth/register                  用户注册
├── /dashboard/stats                统计数据
├── /dashboard/projects             项目列表
├── /analysis/create                创建分析
├── /analysis/{id}                  获取结果
├── /knowledge/items                知识库列表
└── /user/profile                   用户信息

/v1/video-analysis/             # 原有 API（兼容）
├── /jobs                           任务管理
├── /jobs/{job_id}                  任务状态
└── /history                        历史记录

/v1/terminology/                # 术语查询
└── /search                         搜索术语
```

### 统一响应格式

#### 成功响应

```json
{
  "success": true,
  "data": {
    // 实际数据
  },
  "message": "操作成功",
  "timestamp": 1704153600000
}
```

#### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": null
  },
  "timestamp": 1704153600000
}
```

### 核心 API 示例

#### 1. 用户登录

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "demo123"
}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_xxx",
      "email": "user@example.com",
      "name": "用户名"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 604800
  }
}
```

#### 2. 创建视频分析任务（镜头拆解）

```bash
POST /v1/video-analysis/jobs
Content-Type: application/json

{
  "mode": "learn",
  "target_video": {
    "source": {
      "type": "file",
      "path": "/path/to/video.mp4"
    }
  },
  "options": {
    "frame_extract": {
      "fps": 1.0,
      "max_frames": 20
    },
    "analysis": {
      "enabled_modules": ["camera_motion", "lighting", "color_grading"]
    }
  }
}
```

**响应**:

```json
{
  "job_id": "job_abc123",
  "status": "queued",
  "status_url": "/v1/video-analysis/jobs/job_abc123"
}
```

#### 3. 查询任务状态

```bash
GET /v1/video-analysis/jobs/job_abc123
```

**响应**:

```json
{
  "job_id": "job_abc123",
  "status": "succeeded",
  "result": {
    "mode": "learn",
    "target": {
      "segments": [
        {
          "segment_id": "seg_001",
          "start_ms": 0,
          "end_ms": 3500,
          "features": [
            {
              "category": "camera_motion",
              "type": "push_in",
              "value": "缓慢推镜",
              "confidence": 0.85
            }
          ]
        }
      ]
    }
  }
}
```

### 详细 API 文档

- **后端 API**: `Backend/video_ai_demo/API_GUIDE.md`
- **前端集成**: `frontend/API_DOCUMENTATION.md`
- **兼容性说明**: `frontend/API_COMPATIBILITY.md`

---

## 📚 开发文档

### 文档导航

#### 后端文档

| 文档 | 说明 | 路径 |
|------|------|------|
| README.md | 后端总说明 | `Backend/video_ai_demo/README.md` |
| PROJECT_SUMMARY.md | 项目总结 | `Backend/video_ai_demo/PROJECT_SUMMARY.md` |
| QUICKSTART.md | 快速入门 | `Backend/video_ai_demo/QUICKSTART.md` |
| API_GUIDE.md | API 使用指南 | `Backend/video_ai_demo/API_GUIDE.md` |
| DEPLOYMENT.md | 部署指南 | `Backend/video_ai_demo/DEPLOYMENT.md` |
| CV_SCENE_DETECTION.md | 场景检测说明 | `Backend/video_ai_demo/CV_SCENE_DETECTION.md` |
| SHOT_TERMINOLOGY.md | 镜头术语 | `Backend/video_ai_demo/SHOT_TERMINOLOGY.md` |

#### 前端文档

| 文档 | 说明 | 路径 |
|------|------|------|
| README.md | 前端总说明 | `frontend/README.md` |
| PROJECT_OVERVIEW.md | 项目总览 | `frontend/PROJECT_OVERVIEW.md` |
| QUICK_START.md | 快速开始 | `frontend/QUICK_START.md` |
| SHOT_ANALYSIS_GUIDE.md | 镜头拆解指南 | `frontend/SHOT_ANALYSIS_GUIDE.md` |
| API_COMPATIBILITY.md | API 兼容性 | `frontend/API_COMPATIBILITY.md` |
| ENV_CONFIG.md | 环境配置 | `frontend/ENV_CONFIG.md` |
| TROUBLESHOOTING.md | 故障排查 | `frontend/TROUBLESHOOTING.md` |

### 开发规范

#### 代码规范

**后端（Python）**:
- 遵循 PEP 8 规范
- 使用类型提示（Type Hints）
- 编写 Docstring
- 单元测试覆盖

**前端（TypeScript）**:
- 使用 TypeScript 严格模式
- 组件使用 PascalCase 命名
- 函数使用 camelCase 命名
- Props 定义接口类型

#### Git 工作流

```bash
# 主分支
main          生产环境
develop       开发环境

# 功能分支
feature/*     新功能开发
bugfix/*      Bug 修复
hotfix/*      紧急修复
```

#### Commit 规范

```
feat: 新功能
fix: Bug 修复
docs: 文档更新
style: 代码格式
refactor: 重构
perf: 性能优化
test: 测试相关
chore: 构建/工具
```

---

## ❓ 常见问题

### 安装问题

**Q: Python 依赖安装失败？**

A: 确保 Python 版本 >= 3.9，可尝试：

```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

**Q: FFmpeg 未找到？**

A: 安装 FFmpeg 并确保在 PATH 中：

```bash
# 检查
ffmpeg -version
ffprobe -version

# macOS 安装
brew install ffmpeg

# Ubuntu 安装
sudo apt install ffmpeg
```

**Q: Node.js 依赖安装慢？**

A: 使用国内镜像：

```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### 运行问题

**Q: 后端启动失败？**

A: 检查：
1. `.env` 文件是否配置正确
2. `MM_LLM_API_KEY` 是否有效
3. 端口 8000 是否被占用

```bash
# 查看端口占用
lsof -i :8000

# 更换端口
uvicorn app.main:app --port 8001
```

**Q: 前端无法连接后端？**

A: 检查：
1. 后端是否正常运行（访问 http://localhost:8000/docs）
2. `.env` 中的 `VITE_API_BASE_URL` 是否正确
3. 浏览器控制台是否有 CORS 错误

**Q: 视频分析失败？**

A: 可能原因：
1. 视频格式不支持 → 转换为 MP4
2. API 密钥额度不足 → 检查账户余额
3. 网络问题 → 检查网络连接
4. 视频太大 → 压缩视频或调整 `max_frames`

### 功能问题

**Q: 镜头拆解结果不准确？**

A: 调整参数：
- 降低场景检测阈值（更多镜头）
- 增加抽帧率 `fps`（更精细分析）
- 增加 `max_frames`（更完整分析）

**Q: 分析速度太慢？**

A: 优化建议：
- 减少 `fps` 和 `max_frames`
- 使用较短的视频测试
- 考虑升级服务器配置

**Q: Token 过期怎么办？**

A: Token 默认 7 天有效期，过期后重新登录获取新 Token。

### 部署问题

**Q: Docker 部署失败？**

A: 检查：
1. Docker 版本 >= 20.10
2. 磁盘空间是否充足
3. 网络是否能访问 Docker Hub

**Q: Nginx 配置后前端路由 404？**

A: 确保配置了 `try_files`:

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

---

## 🔄 更新日志

### v2.0.0 (2025-01-02) ⭐ 最新版本

**重大更新**：
- ✨ **新增镜头拆解分析功能**
  - 自动场景检测（PySceneDetect + OpenCV）
  - 多模态 AI 镜头分析（Qwen2.5-VL）
  - 运镜、光线、调色识别
  - 时间轴可视化展示
  - 实时流式输出

**前端改进**：
- ✨ 新增 `ShotAnalysis.tsx` 组件
- ✨ 新增 `videoAnalysisService.ts` 服务
- ✨ API 格式兼容性增强
- 🎨 UI/UX 全面优化
- 🚀 性能提升和优化

**后端改进**：
- ✨ 集成 PySceneDetect 场景检测
- ✨ 新增 `scene_detect.py` 步骤
- ✨ 新增镜头术语系统
- 📚 完善 API 文档
- 🐛 Bug 修复和稳定性提升

**文档更新**：
- 📝 新增项目总文档（本文件）
- 📝 新增镜头拆解使用指南
- 📝 更新 API 兼容性文档
- 📝 更新部署指南

### v1.0.0 (2024-12-01)

**初始版本**：
- ✅ 视频深度拆解功能
- ✅ 视频转幻灯片
- ✅ AI 脚本生成
- ✅ 知识库管理
- ✅ 用户认证系统
- ✅ 总览面板
- ✅ 完整的前后端分离架构

---

## 🤝 贡献指南

欢迎贡献代码、报告问题、提出建议！

### 如何贡献

1. **Fork 项目**

```bash
# Fork 到你的账号，然后克隆
git clone <your-fork-url>
cd Cube AI
```

2. **创建功能分支**

```bash
git checkout -b feature/your-feature-name
```

3. **开发和测试**

```bash
# 后端测试
cd Backend/video_ai_demo
pytest tests/

# 前端测试
cd frontend
npm run lint
npm run type-check
```

4. **提交代码**

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/your-feature-name
```

5. **创建 Pull Request**

在 GitHub 上创建 PR，描述你的修改。

### 开发环境设置

```bash
# 安装开发依赖
cd Backend/video_ai_demo
pip install -r requirements.txt
pip install pytest pytest-asyncio  # 测试工具

cd ../../frontend
npm install
```

### 代码审查清单

- [ ] 代码符合规范
- [ ] 添加必要的注释
- [ ] 更新相关文档
- [ ] 通过测试
- [ ] 无 Lint 警告

---

## 📊 项目统计

### 代码量

```
后端:
  Python 代码:      ~3000 行
  核心模块:         8 个
  API 路由:         8 个
  Pipeline 步骤:    8 个

前端:
  TypeScript 代码:  ~8000 行
  React 组件:       12 个
  服务模块:         5 个
  类型定义:         200+ 个
```

### 功能完成度

- ✅ 视频深度拆解: 100%
- ✅ 镜头拆解分析: 100% ⭐
- ✅ 视频转幻灯片: 100%
- ✅ 创作中心: 100%
- ✅ 知识库管理: 100%
- ✅ 用户认证: 100%
- ⏳ 总览面板: 80%（需后端完整 API）

---

## 🙏 致谢

### 开源项目

感谢团队的倾心付出：
@Valentina_Yang
@Kindin-X
@晓叶

感谢以下优秀的开源项目：

**后端**:
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - 强大的 ORM
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证
- [PySceneDetect](https://scenedetect.com/) - 场景检测
- [OpenCV](https://opencv.org/) - 计算机视觉

**前端**:
- [React](https://react.dev/) - UI 框架
- [TypeScript](https://www.typescriptlang.org/) - 类型安全
- [Vite](https://vitejs.dev/) - 构建工具
- [Tailwind CSS](https://tailwindcss.com/) - 样式方案
- [Lucide Icons](https://lucide.dev/) - 图标库
- [Recharts](https://recharts.org/) - 图表库
- [Axios](https://axios-http.com/) - HTTP 客户端

**AI 服务**:
- [Qwen2.5-VL](https://github.com/QwenLM/Qwen2-VL) - 多模态视觉理解
- [Google Gemini](https://ai.google.dev/) - AI 内容生成

---

## 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/tyfuser/CubeAI-FlowDecompose)
- **问题反馈**: [GitHub Issues](https://github.com/tyfuser/CubeAI-FlowDecompose/issues)
- **邮箱**: yifant584@gmail.com
- **文档**: 见 `Backend/video_ai_demo/` 和 `frontend/` 目录

---

## 📄 许可证

本项目采用 **MIT License** 开源协议。

```
MIT License

Copyright (c) 2025 Jumping_Cats Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🎉 结语

**Cube AI (魔方 AI)** 致力于为视频创作者提供专业的 AI 分析和创作辅助工具。

我们相信，通过技术的力量，可以让每个人都能创作出更优质的视频内容。

**让视频创作更简单，让灵感触手可及！** ✨

---

<div align="center">

**Cube AI - 智能视频分析与创作辅助平台**

Made with ❤️ by Jumping_Cats Team

[开始使用](#-快速开始) • [查看文档](#-开发文档) • [反馈问题](#-联系方式)

⭐ 如果这个项目对你有帮助，请给我们一个 Star！

</div>

