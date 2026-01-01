# 后端技术选型对比

## Node.js vs Python 后端对比

### Node.js 后端（当前实现）

**技术栈：**
- Express.js
- ws (WebSocket)
- 端口：8080

**优点：**
- ✅ 已实现，可直接使用
- ✅ 与前端同栈（JavaScript/TypeScript）
- ✅ 启动快速，适合实时通信
- ✅ 生态成熟，Express + ws 稳定可靠

**缺点：**
- ❌ 需要 Node.js 环境（与 uv 管理 Python 环境不一致）
- ❌ 如果未来需要 AI/ML 功能，集成 Python 库较麻烦

### Python 后端（推荐，配合 uv）

**技术栈：**
- FastAPI
- WebSocket 支持
- uv 管理依赖
- 端口：8080（保持一致）

**优点：**
- ✅ 可用 uv 统一管理项目环境
- ✅ Python 生态丰富（AI/ML、数据处理等）
- ✅ FastAPI 性能优秀，自动生成 API 文档
- ✅ 代码简洁，易于维护和扩展
- ✅ 如果未来需要集成 AI 模型（如 Gemini），Python 更方便

**缺点：**
- ❌ 需要重写后端代码（但功能简单，工作量不大）

## 推荐方案

**如果使用 uv 管理环境 → 选择 Python 后端**

理由：
1. 统一的环境管理工具（uv）
2. 更好的扩展性（未来可能集成 AI 功能）
3. FastAPI 性能不输 Express，且代码更简洁

## 如何选择

1. **继续使用 Node.js**：如果项目已经运行良好，且不需要 Python 生态
2. **切换到 Python**：如果想用 uv 统一管理，或未来需要 AI/ML 功能

## 迁移成本

- Python 后端实现：约 100-150 行代码
- 前端代码：**无需修改**（API 接口保持一致）
- 启动脚本：需要小幅调整

