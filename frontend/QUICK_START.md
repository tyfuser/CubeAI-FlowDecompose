# 🚀 快速开始 - API 集成指南

本文档帮助你快速将前端项目从 Mock 数据切换到真实的后端 API。

---

## 📚 相关文档

1. **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - 完整的 API 接口文档，包含所有数据格式和端点定义
2. **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - 详细的迁移指南，包含代码示例和最佳实践
3. **[.env.example](./.env.example)** - 环境变量配置示例

---

## ⚡ 快速开始（5 分钟）

### Step 1: 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，设置 API 地址
# VITE_API_BASE_URL=http://localhost:3000/api/v1
```

### Step 2: 安装依赖（如果还没有）

```bash
npm install axios
```

### Step 3: 验证 API 连接

创建测试文件 `test-api.ts`：

```typescript
import { getDashboardStats } from './services/dashboardService';

async function testConnection() {
  try {
    const stats = await getDashboardStats();
    console.log('✅ API 连接成功:', stats);
  } catch (error) {
    console.error('❌ API 连接失败:', error);
  }
}

testConnection();
```

### Step 4: 在组件中使用

在 `Dashboard.tsx` 中：

```typescript
import { useEffect, useState } from 'react';
import { getDashboardStats } from '../services/dashboardService';

function Dashboard() {
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      const data = await getDashboardStats();
      setStats(data);
    } catch (error) {
      console.error('加载失败:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>加载中...</div>;
  
  return <div>{/* 渲染统计数据 */}</div>;
}
```

---

## 📦 已创建的服务文件

所有 API 服务文件已准备就绪，可直接使用：

| 文件 | 功能 | 主要方法 |
|------|------|---------|
| `services/api.ts` | API 客户端配置 | `apiClient`, `ApiError` |
| `services/dashboardService.ts` | 仪表板数据 | `getDashboardStats()`, `getProjects()`, `getTrends()` |
| `services/analysisService.ts` | 视频分析 | `createAnalysis()`, `getAnalysis()`, `pollAnalysisResult()` |
| `services/discoveryService.ts` | 案例探索 | `getCases()`, `sendChatMessage()` |
| `services/knowledgeService.ts` | 知识库 | `getKBItems()`, `bookmarkKBItem()` |
| `services/scriptService.ts` | 脚本生成 | `generateScript()`, `saveScript()` |
| `services/slideshowService.ts` | 幻灯片 | `createSlideshow()`, `exportSlideshow()` |

---

## 🎯 核心功能迁移优先级

### 🔴 高优先级（必须先完成）

1. **用户认证** - `POST /auth/login`
   ```typescript
   import apiClient from './services/api';
   
   async function login(email: string, password: string) {
     const response = await apiClient.post('/auth/login', { email, password });
     localStorage.setItem('rubik_token', response.data.token);
   }
   ```

2. **仪表板数据** - `GET /dashboard/stats`, `GET /dashboard/projects`
   ```typescript
   import { getDashboardStats, getProjects } from './services/dashboardService';
   
   const stats = await getDashboardStats();
   const projects = await getProjects({ page: 1, limit: 10 });
   ```

3. **视频分析** - `POST /analysis/create`, `GET /analysis/{id}`
   ```typescript
   import { createAnalysis, pollAnalysisResult } from './services/analysisService';
   
   const task = await createAnalysis({ url: videoUrl });
   const result = await pollAnalysisResult(task.analysisId);
   ```

### 🟡 中优先级（核心功能）

4. **脚本生成** - `POST /scripts/generate`
5. **案例探索** - `GET /discovery/cases`
6. **知识库** - `GET /knowledge/items`

### 🟢 低优先级（增强功能）

7. **视频转幻灯片** - `POST /slideshow/create`
8. **AI 对话** - `POST /discovery/chat`

---

## 🔧 开发模式 vs 生产模式

### 开发模式（使用 Mock 数据）

如果后端还没准备好，可以暂时保留 Mock 数据：

```typescript
// .env
VITE_ENABLE_MOCK=true
```

```typescript
// services/dashboardService.ts
import { getDashboardStats as getStatsAPI } from './dashboardService';

export async function getDashboardStats() {
  // 如果启用 Mock
  if (import.meta.env.VITE_ENABLE_MOCK === 'true') {
    return [
      { label: '已分析视频', value: '128', /* ... */ },
      // Mock 数据
    ];
  }
  
  // 否则调用真实 API
  return await getStatsAPI();
}
```

### 生产模式（使用真实 API）

```bash
# .env.production
VITE_API_BASE_URL=https://api.rubik-ai.com/v1
VITE_ENABLE_MOCK=false
```

---

## 🛠️ 调试工具

### 1. API 请求日志

在 `.env` 中启用：

```env
VITE_ENABLE_API_LOG=true
```

所有 API 请求将在控制台输出：

```
[API] GET /dashboard/stats
[API] Response: { success: true, data: {...} }
```

### 2. Chrome DevTools

安装 React DevTools 和 Network 面板查看请求：

- **Network**: 查看所有 HTTP 请求
- **Console**: 查看 API 日志
- **React DevTools**: 查看组件状态

### 3. 使用 Postman 测试

导入 API 文档到 Postman 进行接口测试：

1. 打开 Postman
2. 导入 Collection
3. 设置环境变量 `BASE_URL`
4. 测试各个接口

---

## 📋 接口对照表

### Dashboard 页面

| Mock 数据 | API 端点 | 服务方法 |
|-----------|----------|---------|
| `stats` 数组 | `GET /dashboard/stats` | `getDashboardStats()` |
| `projects` 数组 | `GET /dashboard/projects` | `getProjects()` |
| `trends` 数组 | `GET /dashboard/trends` | `getTrends()` |
| `templates` 数组 | `GET /dashboard/templates` | `getTemplates()` |
| `scheduleHeatmap` | `GET /dashboard/schedule` | `getSchedule()` |

### Discovery 页面

| Mock 数据 | API 端点 | 服务方法 |
|-----------|----------|---------|
| `viralCases` 数组 | `GET /discovery/cases` | `getCases()` |
| AI 对话 | `POST /discovery/chat` | `sendChatMessage()` |

### KnowledgeBase 页面

| Mock 数据 | API 端点 | 服务方法 |
|-----------|----------|---------|
| `items` 数组 | `GET /knowledge/items` | `getKBItems()` |

### Editor 页面

| Mock 数据 | API 端点 | 服务方法 |
|-----------|----------|---------|
| 生成脚本 | `POST /scripts/generate` | `generateScript()` |
| 保存脚本 | `POST /scripts/save` | `saveScript()` |

### VideoSlideshow 页面

| Mock 数据 | API 端点 | 服务方法 |
|-----------|----------|---------|
| `mockSlides` | `POST /slideshow/create` | `createSlideshow()` |
| 幻灯片结果 | `GET /slideshow/{taskId}` | `getSlideshow()` |

---

## ⚠️ 常见问题

### Q1: 如何处理 CORS 错误？

**方案 1: Vite 代理（开发环境）**

编辑 `vite.config.ts`：

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      }
    }
  }
});
```

**方案 2: 后端配置 CORS**

需要后端添加 CORS 响应头。

### Q2: Token 如何管理？

Token 自动在 `services/api.ts` 的拦截器中处理：

```typescript
// 登录后保存 Token
localStorage.setItem('rubik_token', token);

// 之后的所有请求会自动携带
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('rubik_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Q3: 如何处理加载状态？

推荐使用 React Query 或创建自定义 Hook：

```typescript
function useApiData<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetcher()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

// 使用
const { data: stats, loading, error } = useApiData(getDashboardStats);
```

### Q4: 如何测试 API 是否正常？

创建测试脚本 `scripts/test-api.js`：

```javascript
import { getDashboardStats } from '../services/dashboardService';

async function testAll() {
  console.log('🧪 开始测试 API...\n');

  try {
    console.log('测试 1: 获取统计数据');
    const stats = await getDashboardStats();
    console.log('✅ 成功:', stats);
  } catch (error) {
    console.error('❌ 失败:', error.message);
  }

  // 其他测试...
}

testAll();
```

---

## 📞 获取帮助

- **API 文档**: 查看 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **迁移指南**: 查看 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
- **技术支持**: dev@rubik-ai.com
- **问题反馈**: GitHub Issues

---

## ✅ 检查清单

在开始前，确保完成以下步骤：

- [ ] 已复制 `.env.example` 为 `.env`
- [ ] 已配置 `VITE_API_BASE_URL`
- [ ] 已安装 `axios` 依赖
- [ ] 已测试 API 连接
- [ ] 已阅读 API 文档
- [ ] 已了解错误处理机制
- [ ] 已配置 Token 认证

完成后即可开始迁移各个页面的数据获取逻辑！

---

**祝开发顺利！🎉**

