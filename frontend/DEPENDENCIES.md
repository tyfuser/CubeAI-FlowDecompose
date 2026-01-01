# 📦 依赖项说明

## 必需依赖

### axios
```bash
npm install axios
```

**用途**: HTTP 客户端库，用于发起 API 请求

**配置**: 已在 `services/api.ts` 中完成基础配置

---

## 推荐依赖（可选）

### 1. React Query / TanStack Query
```bash
npm install @tanstack/react-query
```

**用途**: 
- 自动缓存 API 响应
- 自动重试失败请求
- 后台自动刷新数据
- 简化加载状态管理

**使用示例**:
```typescript
import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from './services/dashboardService';

function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: getDashboardStats,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
  });

  if (isLoading) return <Loading />;
  if (error) return <Error />;
  
  return <StatsDisplay data={data} />;
}
```

---

### 2. SWR
```bash
npm install swr
```

**用途**: 轻量级数据获取库（React Query 的替代品）

**使用示例**:
```typescript
import useSWR from 'swr';
import { getDashboardStats } from './services/dashboardService';

function Dashboard() {
  const { data, error, isLoading } = useSWR('dashboardStats', getDashboardStats);
  
  // ...
}
```

---

### 3. Zod
```bash
npm install zod
```

**用途**: 运行时数据验证，确保 API 响应符合预期格式

**使用示例**:
```typescript
import { z } from 'zod';

const ProjectSchema = z.object({
  id: z.string(),
  title: z.string(),
  score: z.number().min(0).max(100),
  status: z.enum(['analyzing', 'completed', 'draft', 'failed']),
});

// 验证 API 响应
const project = ProjectSchema.parse(apiResponse);
```

---

### 4. Axios Retry
```bash
npm install axios-retry
```

**用途**: 自动重试失败的请求

**配置**:
```typescript
// services/api.ts
import axiosRetry from 'axios-retry';

axiosRetry(apiClient, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return error.response?.status === 429 || error.response?.status >= 500;
  }
});
```

---

### 5. React Hook Form
```bash
npm install react-hook-form
```

**用途**: 表单状态管理（如果需要复杂表单）

---

## 开发依赖

### 1. MSW (Mock Service Worker)
```bash
npm install -D msw
```

**用途**: 在开发阶段 Mock API 响应

**配置**:
```typescript
// mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/v1/dashboard/stats', () => {
    return HttpResponse.json({
      success: true,
      data: {
        stats: [/* mock data */]
      }
    });
  }),
];
```

---

### 2. JSON Server
```bash
npm install -D json-server
```

**用途**: 快速搭建 Mock API 服务器

**使用**:
```bash
# 创建 mock/db.json
npx json-server --watch mock/db.json --port 3000
```

---

## package.json 更新建议

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0"  // 可选但推荐
  },
  "devDependencies": {
    "msw": "^2.0.0",  // 可选，用于开发
    "json-server": "^0.17.0"  // 可选，用于开发
  }
}
```

---

## 安装命令

### 最小配置（必需）
```bash
npm install axios
```

### 推荐配置
```bash
npm install axios @tanstack/react-query
npm install -D msw
```

### 完整配置
```bash
npm install axios @tanstack/react-query zod axios-retry
npm install -D msw json-server
```

---

## 版本兼容性

| 依赖 | 最低版本 | 推荐版本 | 备注 |
|------|---------|---------|------|
| axios | ^1.0.0 | ^1.6.0 | 核心依赖 |
| @tanstack/react-query | ^5.0.0 | ^5.0.0 | 推荐 |
| msw | ^2.0.0 | ^2.0.0 | 开发依赖 |
| React | ^18.0.0 | ^18.2.0 | 已有 |
| TypeScript | ^5.0.0 | ^5.3.0 | 已有 |

---

## 相关资源

- **Axios 文档**: https://axios-http.com/
- **TanStack Query 文档**: https://tanstack.com/query/latest
- **MSW 文档**: https://mswjs.io/
- **Zod 文档**: https://zod.dev/

