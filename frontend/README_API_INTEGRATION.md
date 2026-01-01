# 📘 API 集成完整指南 - 文档索引

> 本文档汇总了所有与 API 集成相关的文档和资源

---

## 📂 文档结构

```
frontend/
├── API_DOCUMENTATION.md         # ⭐ 完整的 API 接口文档（后端对接必看）
├── MIGRATION_GUIDE.md           # ⭐ Mock 数据迁移指南（前端开发必看）
├── QUICK_START.md               # ⭐ 快速开始指南（5分钟上手）
├── env.example.txt              # 环境变量配置示例
├── services/                    # API 服务层（已实现）
│   ├── api.ts                   # API 客户端配置
│   ├── analysisService.ts       # 视频分析 API
│   ├── dashboardService.ts      # 仪表板 API
│   ├── discoveryService.ts      # 案例探索 API
│   ├── knowledgeService.ts      # 知识库 API
│   ├── scriptService.ts         # 脚本生成 API
│   └── slideshowService.ts      # 幻灯片 API
└── types.ts                     # TypeScript 类型定义
```

---

## 🎯 快速导航

### 👨‍💻 前端开发者

1. **快速开始** → [QUICK_START.md](./QUICK_START.md)
   - 5 分钟快速集成
   - 环境配置
   - 基础示例

2. **迁移指南** → [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
   - 详细的代码迁移步骤
   - 每个组件的改造示例
   - UI 优化建议
   - 调试技巧

3. **API 文档** → [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
   - 查询具体接口定义
   - 了解数据格式
   - 错误码说明

### 👨‍🔧 后端开发者

1. **API 文档** → [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) ⭐
   - 所有接口端点定义
   - 完整的请求/响应格式
   - 认证机制说明
   - 错误码列表

2. **数据模型** → [types.ts](./types.ts)
   - TypeScript 类型定义
   - 可转换为后端模型

### 🧪 测试/QA

1. **API 文档** → [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
   - 接口测试用例
   - 响应格式验证

---

## 📊 数据格式总览

### 核心数据模型

| 模型 | 用途 | 文档位置 |
|------|------|---------|
| `ProjectSummary` | 项目摘要信息 | [API 文档 §2.2](./API_DOCUMENTATION.md#22-获取项目列表) |
| `VideoAnalysis` | 视频分析结果 | [API 文档 §3.2](./API_DOCUMENTATION.md#32-获取分析结果) |
| `Shot` | 脚本分镜信息 | [API 文档 §6.1](./API_DOCUMENTATION.md#61-生成创作脚本) |
| `SlideData` | 幻灯片数据 | [API 文档 §7.2](./API_DOCUMENTATION.md#72-获取幻灯片生成结果) |
| `ViralCase` | 爆款案例 | [API 文档 §4.1](./API_DOCUMENTATION.md#41-获取爆款案例列表) |
| `KBItem` | 知识库条目 | [API 文档 §5.1](./API_DOCUMENTATION.md#51-获取知识库条目) |

---

## 🔌 API 端点速查

### 认证相关
```
POST   /auth/login          # 用户登录
POST   /auth/register       # 用户注册
POST   /auth/refresh        # 刷新 Token
```

### 仪表板
```
GET    /dashboard/stats     # 统计数据
GET    /dashboard/projects  # 项目列表
GET    /dashboard/trends    # 实时趋势
GET    /dashboard/templates # 叙事模板
GET    /dashboard/schedule  # 日程热力图
```

### 视频分析
```
POST   /analysis/create              # 发起分析
GET    /analysis/{id}                # 获取结果
GET    /analysis/{id}/status         # 获取状态
```

### 案例探索
```
GET    /discovery/cases     # 案例列表
POST   /discovery/chat      # AI 对话
```

### 知识库
```
GET    /knowledge/items               # 条目列表
GET    /knowledge/items/{id}          # 单个条目
POST   /knowledge/items/{id}/bookmark # 收藏
```

### 脚本生成
```
POST   /scripts/generate    # 生成脚本
POST   /scripts/save        # 保存脚本
GET    /scripts             # 脚本列表
GET    /scripts/{id}        # 单个脚本
DELETE /scripts/{id}        # 删除脚本
```

### 幻灯片
```
POST   /slideshow/create                    # 创建任务
GET    /slideshow/{taskId}                  # 获取结果
PATCH  /slideshow/{taskId}/slides/{slideId} # 更新幻灯片
POST   /slideshow/{taskId}/export           # 导出 PPTX
```

完整文档请查看 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

---

## 🔧 服务层使用示例

### 1. 仪表板数据

```typescript
import { getDashboardStats, getProjects } from './services/dashboardService';

// 获取统计数据
const stats = await getDashboardStats();

// 获取项目列表
const projects = await getProjects({ page: 1, limit: 10 });
```

### 2. 视频分析

```typescript
import { createAnalysis, pollAnalysisResult } from './services/analysisService';

// 创建分析任务
const task = await createAnalysis({ url: videoUrl });

// 轮询获取结果
const result = await pollAnalysisResult(task.analysisId, (status) => {
  console.log(`进度: ${status.progress}%`);
});
```

### 3. 脚本生成

```typescript
import { generateScript } from './services/scriptService';

// 生成脚本
const script = await generateScript({
  analysisId: '12345',
  strategy: 'remake',
  platform: 'douyin'
});
```

### 4. 知识库查询

```typescript
import { getKBItems } from './services/knowledgeService';

// 获取知识库条目
const items = await getKBItems({
  category: 'hooks',
  search: '视觉',
  page: 1
});
```

更多示例请查看 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)

---

## ⚙️ 环境配置

### 创建 .env 文件

```bash
# 复制配置模板
cp env.example.txt .env

# 编辑配置
nano .env
```

### 必需配置项

```env
# API 基础地址（必需）
VITE_API_BASE_URL=http://localhost:3000/api/v1

# 是否启用 Mock（可选，开发阶段）
VITE_ENABLE_MOCK=false

# 是否启用 API 日志（可选）
VITE_ENABLE_API_LOG=true
```

完整配置说明请查看 [env.example.txt](./env.example.txt)

---

## 🏗️ 项目架构

### Mock 数据 → API 调用转换

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Component     │       │   API Service   │       │   Backend API   │
│  (Dashboard)    │──────▶│ (dashboardSvc)  │──────▶│   /api/v1/...   │
│                 │       │                 │       │                 │
│  - Mock 数据    │       │  - axios 调用   │       │  - 真实数据     │
│  - 静态数组     │       │  - 类型安全     │       │  - 数据库       │
│  - 假数据       │       │  - 错误处理     │       │  - 业务逻辑     │
└─────────────────┘       └─────────────────┘       └─────────────────┘
     ❌ 旧方式                  ✅ 新方式                 后端
```

### 服务层职责

```typescript
// services/dashboardService.ts
export async function getDashboardStats(): Promise<DashboardStat[]> {
  // 1. 发起 HTTP 请求
  const response = await apiClient.get('/dashboard/stats');
  
  // 2. 自动处理：
  //    - Token 认证
  //    - 错误拦截
  //    - 响应转换
  //    - 类型校验
  
  // 3. 返回类型安全的数据
  return response.data.stats;
}
```

---

## ✅ 集成检查清单

### 准备阶段
- [ ] 已阅读 [QUICK_START.md](./QUICK_START.md)
- [ ] 已配置环境变量
- [ ] 已安装 axios 依赖
- [ ] 已测试后端 API 可访问

### 开发阶段
- [ ] Dashboard 组件已迁移
- [ ] Discovery 组件已迁移
- [ ] KnowledgeBase 组件已迁移
- [ ] Editor 组件已迁移
- [ ] VideoSlideshow 组件已迁移
- [ ] 错误处理已完善
- [ ] 加载状态已添加

### 测试阶段
- [ ] 所有接口可正常调用
- [ ] Token 认证机制正常
- [ ] 错误提示用户友好
- [ ] 加载状态显示正确
- [ ] 数据格式与后端一致

### 优化阶段
- [ ] 添加请求缓存（React Query）
- [ ] 实现离线支持
- [ ] 性能优化（虚拟滚动等）
- [ ] 单元测试覆盖

---

## 🐛 调试技巧

### 1. 开启 API 日志

```env
VITE_ENABLE_API_LOG=true
```

控制台输出：
```
[API] GET /dashboard/stats
[API] Response: { success: true, data: {...} }
```

### 2. 使用 Chrome DevTools

- **Network 面板**: 查看所有 HTTP 请求
- **Console 面板**: 查看错误日志
- **React DevTools**: 查看组件状态

### 3. API 测试工具

- **Postman**: 独立测试接口
- **Thunder Client**: VS Code 插件
- **curl**: 命令行工具

```bash
# 测试获取统计数据
curl -X GET http://localhost:3000/api/v1/dashboard/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🆘 常见问题

### Q: CORS 错误怎么办？

**A**: 在 `vite.config.ts` 配置代理：

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true
      }
    }
  }
});
```

### Q: Token 过期怎么处理？

**A**: 已在 `services/api.ts` 自动处理：

```typescript
// 401 错误会自动跳转登录
if (status === 401) {
  localStorage.removeItem('rubik_token');
  window.location.href = '/login';
}
```

### Q: 如何处理 API 限流（429）？

**A**: 错误拦截器会自动捕获并提示用户。

更多问题请查看 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) 的「常见问题」章节。

---

## 📞 技术支持

- **API 文档**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **迁移指南**: [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
- **快速开始**: [QUICK_START.md](./QUICK_START.md)
- **问题反馈**: GitHub Issues
- **技术支持**: dev@rubik-ai.com

---

## 📝 更新日志

### v1.0.0 (2025-01-02)
- ✅ 完成所有 API 服务层实现
- ✅ 完成 API 接口文档
- ✅ 完成迁移指南
- ✅ 完成快速开始指南
- ✅ 创建环境变量配置示例

---

## 🎉 开始使用

1. 阅读 [QUICK_START.md](./QUICK_START.md) 了解基础配置
2. 参考 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) 进行组件迁移
3. 查阅 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) 了解接口细节
4. 遇到问题查看「常见问题」章节或联系技术支持

**祝开发顺利！🚀**

