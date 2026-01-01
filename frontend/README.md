<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# 魔方 AI - Rubik AI Engine

视频分析与创作辅助平台

> 📖 **完整项目文档**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - 包含架构、开发指南、部署等详细信息
> 
> 🔍 **文档导航**: [DOCS_INDEX.md](DOCS_INDEX.md) - 快速找到您需要的文档

## ✨ 功能特性

### 🎬 视频深度拆解
- 爆款因素分析
- 节奏曲线可视化
- 钩子强度评估
- 雷达图评分

### 📹 镜头拆解分析（新功能）
- 自动识别镜头切换
- 运镜技巧分析（特写、中景、全景等）
- 光线布局识别（三点布光、自然光等）
- 调色风格分析（暖色调、冷色调等）
- 可视化时间轴展示

### 📊 视频转幻灯片
- 自动提取关键帧
- 智能生成幻灯片
- 多种布局样式

### ✍️ 创作中心
- AI 辅助脚本生成
- 跨平台脚本优化
- 分镜可视化编辑

### 📚 灵感仓库
- 知识点管理
- 灵感收藏
- 标签分类

### 🔍 发现爆款案例
- 热门视频推荐
- 案例库浏览

## 🚀 快速开始

### 环境要求
- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
npm install
```

### 环境变量配置

创建 `.env` 文件：

```env
# Gemini API Key（用于 AI 功能）
GEMINI_API_KEY=your_gemini_api_key

# 视频分析 API（原有功能）
VITE_API_BASE_URL=http://localhost:3000/api/v1

# 镜头拆解分析 API（新功能，可选）
VITE_SHOT_ANALYSIS_BASE_URL=http://localhost:8000
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

---

## ⚠️ 重要：后端服务配置

**前端需要后端服务支持才能正常运行！**

### 快速检查

如果您看到 "网络连接失败" 错误：

```bash
# 检查后端是否运行在 8000 端口
lsof -i :8000
```

### 三种运行方式

#### 方式 1：连接真实后端（推荐）

确保后端服务运行在 `http://localhost:8000`

```bash
# 在后端项目目录
cd /path/to/backend
npm run dev  # 或其他启动命令
```

**详细配置请查看**：[BACKEND_SETUP_REQUIRED.md](BACKEND_SETUP_REQUIRED.md)

#### 方式 2：使用 Mock 数据（临时开发）

修改 `.env`：
```env
VITE_ENABLE_MOCK=true
```

重启前端：
```bash
npm run dev
```

#### 方式 3：连接远程后端

修改 `.env`：
```env
VITE_API_BASE_URL=https://your-backend.com/api/v1
VITE_SHOT_ANALYSIS_BASE_URL=https://your-shot-backend.com
```

## 📖 文档

### 📋 总览文档
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** 🌟 项目总文档（架构、开发、部署）

### 📚 使用指南
- **[SHOT_ANALYSIS_GUIDE.md](SHOT_ANALYSIS_GUIDE.md)** - 镜头拆解使用指南
- **[SHOT_ANALYSIS_NEW_FEATURES.md](SHOT_ANALYSIS_NEW_FEATURES.md)** - 新功能详解
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - 快速参考

### 🔧 技术文档
- **[API_COMPATIBILITY.md](API_COMPATIBILITY.md)** ⭐ 后端 API 格式适配
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - API 接口规范
- **[FRONTEND_INTEGRATION_GUIDE.md](FRONTEND_INTEGRATION_GUIDE.md)** - 集成指南
- **[ENV_CONFIG.md](ENV_CONFIG.md)** - 环境变量配置

### 🛠 运维文档
- **[BACKEND_SETUP_REQUIRED.md](BACKEND_SETUP_REQUIRED.md)** - 后端配置要求
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - 故障排查
- **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)** - 集成完成总结

## 🏗️ 项目结构

```
frontend/
├── components/           # React 组件
│   ├── Dashboard.tsx     # 总览面板
│   ├── AnalysisPanel.tsx # 视频分析面板
│   ├── ShotAnalysis.tsx  # 镜头拆解分析（新）
│   ├── Editor.tsx        # 脚本编辑器
│   ├── VideoSlideshow.tsx # 视频转幻灯片
│   ├── KnowledgeBase.tsx # 知识库
│   └── ...
├── services/            # API 服务层
│   ├── api.ts           # Axios 实例
│   ├── analysisService.ts        # 视频分析服务
│   ├── videoAnalysisService.ts   # 镜头拆解服务（新）
│   ├── geminiService.ts          # Gemini AI 服务
│   └── ...
├── types.ts             # TypeScript 类型定义
├── App.tsx              # 主应用组件
└── ...
```

## 🎯 使用流程

### 视频深度拆解
1. 进入"总览面板"
2. 输入视频链接或上传文件
3. 等待分析完成
4. 查看爆款因素、节奏图、雷达评分

### 镜头拆解分析（新功能）
1. 点击侧边栏"镜头拆解分析"
2. 上传本地视频或输入路径
3. 等待 AI 分析
4. 查看时间轴展示的镜头、运镜、光线、调色
5. 点击片段查看详细分析

### 脚本创作
1. 完成视频分析后进入"创作中心"
2. 选择创作策略和目标平台
3. AI 自动生成分镜脚本
4. 手动调整优化

## 🔧 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI**: Tailwind CSS + Lucide Icons
- **HTTP 客户端**: Axios
- **AI 模型**: Google Gemini
- **图表**: Recharts

## 📝 更新日志

### v2.0 - 2025-01-02
- ✨ 新增：视频镜头拆解分析功能
- ✨ 新增：时间轴可视化界面
- ✨ 新增：运镜、光线、调色自动识别
- ✨ 新增：历史记录管理
- 📚 新增：详细使用指南和集成文档

### v1.0
- 🎉 初始版本
- ✅ 视频深度拆解
- ✅ 视频转幻灯片
- ✅ AI 脚本生成
- ✅ 知识库管理

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**祝创作愉快！** 🎬✨
