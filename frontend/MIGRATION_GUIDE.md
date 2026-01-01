# Mock 数据迁移到后端 API 指南

本指南展示如何将现有的 mock 数据替换为从后端 API 获取的真实数据。

---

## 📦 前置准备

### 1. 安装依赖

确保已安装 axios：

```bash
npm install axios
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# 开发环境
VITE_API_BASE_URL=http://localhost:3000/api/v1

# 生产环境
# VITE_API_BASE_URL=https://api.rubik-ai.com/v1
```

### 3. 服务文件结构

所有 API 服务文件已创建在 `/services` 目录：

```
/services
  ├── api.ts                 # API 客户端配置（已创建）
  ├── analysisService.ts     # 视频分析 API（已创建）
  ├── dashboardService.ts    # 仪表板 API（已创建）
  ├── discoveryService.ts    # 案例探索 API（已创建）
  ├── knowledgeService.ts    # 知识库 API（已创建）
  ├── scriptService.ts       # 脚本生成 API（已创建）
  ├── slideshowService.ts    # 幻灯片 API（已创建）
  └── geminiService.ts       # 现有的 Gemini 服务
```

---

## 🔄 迁移步骤

### 示例 1: Dashboard.tsx - 迁移统计数据

**原 Mock 代码**:
```typescript
const Dashboard: React.FC<DashboardProps> = ({ onStartAnalysis, onViewDetails }) => {
  const [url, setUrl] = useState('');
  
  // ❌ Mock 数据
  const stats = [
    { label: '已分析视频', value: '128', icon: FileVideo, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { label: '爆款基因库', value: '2,450', icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
    // ...
  ];
```

**改造后的代码**:
```typescript
import { useEffect, useState } from 'react';
import { getDashboardStats, DashboardStat } from '../services/dashboardService';
import { isApiError } from '../services/api';

const Dashboard: React.FC<DashboardProps> = ({ onStartAnalysis, onViewDetails }) => {
  const [url, setUrl] = useState('');
  
  // ✅ 从后端获取数据
  const [stats, setStats] = useState<DashboardStat[]>([]);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setStatsLoading(true);
      setStatsError(null);
      const data = await getDashboardStats();
      setStats(data);
    } catch (error) {
      console.error('加载统计数据失败:', error);
      if (isApiError(error)) {
        setStatsError(error.message);
      } else {
        setStatsError('加载失败');
      }
    } finally {
      setStatsLoading(false);
    }
  };

  // 渲染部分
  return (
    <div>
      {statsLoading ? (
        <div>加载中...</div>
      ) : statsError ? (
        <div>错误: {statsError}</div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {stats.map((stat, i) => (
            <StatCard key={i} stat={stat} />
          ))}
        </div>
      )}
    </div>
  );
};
```

### 示例 2: Dashboard.tsx - 迁移项目列表

**原 Mock 代码**:
```typescript
const projects: ProjectSummary[] = [
  { id: '1', title: "2024夏季穿搭爆款拆解", thumbnail: "https://picsum.photos/...", ... },
  { id: '2', title: "深夜食堂文案逻辑分析", thumbnail: "https://picsum.photos/...", ... },
  // ...
];
```

**改造后的代码**:
```typescript
import { getProjects } from '../services/dashboardService';

const Dashboard: React.FC<DashboardProps> = ({ onStartAnalysis, onViewDetails }) => {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 10,
    total: 0,
  });

  useEffect(() => {
    loadProjects();
  }, [pagination.page]);

  const loadProjects = async () => {
    try {
      setProjectsLoading(true);
      const data = await getProjects({
        page: pagination.page,
        limit: pagination.limit,
        sortBy: 'timestamp',
      });
      setProjects(data.projects);
      setPagination(prev => ({
        ...prev,
        total: data.total,
      }));
    } catch (error) {
      console.error('加载项目列表失败:', error);
    } finally {
      setProjectsLoading(false);
    }
  };

  return (
    <div>
      {projectsLoading ? (
        <ProjectListSkeleton />
      ) : (
        <>
          <ProjectList projects={projects} onViewDetails={onViewDetails} />
          <Pagination
            current={pagination.page}
            total={pagination.total}
            pageSize={pagination.limit}
            onChange={(page) => setPagination(prev => ({ ...prev, page }))}
          />
        </>
      )}
    </div>
  );
};
```

### 示例 3: KnowledgeBase.tsx - 迁移知识库数据

**原 Mock 代码**:
```typescript
const items: KBItem[] = [
  {
    id: '1',
    category: 'hooks',
    title: '视觉反差钩子',
    description: '前0.5秒展示极端对比画面...',
    tags: ['高点击', '强反转', '生活'],
    usageCount: 1240,
    rating: 4.9,
  },
  // ...
];

const filteredItems = items.filter(item => 
  (item.category === activeCategory) && 
  (item.title.toLowerCase().includes(searchQuery.toLowerCase()))
);
```

**改造后的代码**:
```typescript
import { useEffect, useState } from 'react';
import { getKBItems, KBItem, KBCategory } from '../services/knowledgeService';

const KnowledgeBase: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<KBCategory>('hooks');
  const [searchQuery, setSearchQuery] = useState('');
  const [items, setItems] = useState<KBItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, total: 0 });

  // 当分类或搜索关键词改变时重新加载
  useEffect(() => {
    loadItems();
  }, [activeCategory, searchQuery, pagination.page]);

  const loadItems = async () => {
    try {
      setLoading(true);
      const data = await getKBItems({
        category: activeCategory,
        search: searchQuery || undefined,
        page: pagination.page,
        limit: 15,
      });
      setItems(data.items);
      setPagination(prev => ({ ...prev, total: data.total }));
    } catch (error) {
      console.error('加载知识库失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      setPagination(prev => ({ ...prev, page: 1 })); // 搜索时重置到第一页
      loadItems();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  return (
    <div>
      {/* 分类切换 */}
      <CategoryTabs
        activeCategory={activeCategory}
        onChange={(cat) => {
          setActiveCategory(cat);
          setPagination({ page: 1, total: 0 });
        }}
      />

      {/* 搜索框 */}
      <SearchInput value={searchQuery} onChange={setSearchQuery} />

      {/* 内容列表 */}
      {loading ? (
        <ItemListSkeleton />
      ) : items.length > 0 ? (
        <ItemGrid items={items} />
      ) : (
        <EmptyState />
      )}
    </div>
  );
};
```

### 示例 4: Discovery.tsx - 迁移案例数据和 AI 对话

**原 Mock 代码**:
```typescript
const viralCases = [
  { 
    id: 'v1', 
    title: '2024 夏季穿搭：冷淡风极致表达', 
    cover: 'https://picsum.photos/...',
    // ...
  },
  // ...
];

const handleSendMessage = async () => {
  // 模拟 AI 回复
  setTimeout(() => {
    const assistantMsg = {
      role: 'assistant',
      content: '这是模拟的 AI 回复...',
    };
    setMessages(prev => [...prev, assistantMsg]);
  }, 1200);
};
```

**改造后的代码**:
```typescript
import { useEffect, useState } from 'react';
import { getCases, sendChatMessage, ViralCase } from '../services/discoveryService';

const Discovery: React.FC = () => {
  const [cases, setCases] = useState<ViralCase[]>([]);
  const [casesLoading, setCasesLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState<ViralCase | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      setCasesLoading(true);
      const data = await getCases({
        page: 1,
        limit: 12,
        sortBy: 'score',
      });
      setCases(data.cases);
    } catch (error) {
      console.error('加载案例失败:', error);
    } finally {
      setCasesLoading(false);
    }
  };

  const openChat = (video: ViralCase) => {
    setSelectedVideo(video);
    setConversationId(null);
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `你好！我是你的 AI 创作助手。关于《${video.title}》这个视频，你可以问我任何问题。`,
        timestamp: Date.now(),
      }
    ]);
  };

  const handleSendMessage = async (content: string) => {
    if (!selectedVideo || !content.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const response = await sendChatMessage({
        caseId: selectedVideo.id,
        message: content,
        conversationId: conversationId || undefined,
      });

      // 更新会话 ID
      if (!conversationId) {
        setConversationId(response.conversationId);
      }

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        timestamp: Date.now(),
        attachments: response.attachments,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('发送消息失败:', error);
      // 可以显示错误提示
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div>
      {/* 案例列表 */}
      {casesLoading ? (
        <CaseGridSkeleton />
      ) : (
        <CaseGrid cases={cases} onOpenChat={openChat} />
      )}

      {/* AI 对话抽屉 */}
      {selectedVideo && (
        <ChatDrawer
          video={selectedVideo}
          messages={messages}
          isTyping={isTyping}
          onSendMessage={handleSendMessage}
          onClose={() => setSelectedVideo(null)}
        />
      )}
    </div>
  );
};
```

### 示例 5: App.tsx - 迁移视频分析流程

**原 Mock 代码**:
```typescript
const handleStartAnalysis = async (url: string) => {
  setLoading(true);
  try {
    // 直接调用 Gemini API
    const data = await analyzeVideoConcept(url);
    const mockRhythm = Array.from({ length: 30 }, ...);
    const newAnalysis: VideoAnalysis = { ...data, rhythmData: mockRhythm };
    setAnalysis(newAnalysis);
    setActiveSection(AppSection.Analysis);
  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
};
```

**改造后的代码**:
```typescript
import { createAnalysis, pollAnalysisResult } from './services/analysisService';
import { isApiError } from './services/api';

const App: React.FC = () => {
  const [analysis, setAnalysis] = useState<VideoAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState({
    status: '',
    progress: 0,
    currentStep: '',
  });

  const handleStartAnalysis = async (url: string) => {
    if (!url.trim()) {
      alert('请输入视频链接');
      return;
    }

    setLoading(true);
    setAnalysisProgress({ status: '', progress: 0, currentStep: '' });

    try {
      // 1. 创建分析任务
      const task = await createAnalysis({
        url,
        platform: 'auto', // 自动识别平台
      });

      console.log(`分析任务已创建，ID: ${task.analysisId}`);

      // 2. 轮询获取结果
      const result = await pollAnalysisResult(
        task.analysisId,
        (status) => {
          setAnalysisProgress({
            status: status.status,
            progress: status.progress,
            currentStep: status.currentStep,
          });
        },
        60, // 最多轮询 60 次
        2000 // 每 2 秒轮询一次
      );

      // 3. 设置分析结果
      setAnalysis(result);
      
      // 4. 生成默认脚本
      setShots(generateDefaultShots(result.title));
      
      // 5. 跳转到分析页面
      setActiveSection(AppSection.Analysis);

      console.log('分析完成:', result);
    } catch (error) {
      console.error('分析失败:', error);
      
      if (isApiError(error)) {
        if (error.code === 'QUOTA_EXCEEDED') {
          setErrorToast({ 
            message: 'API 配额已用完，请升级套餐或稍后再试', 
            type: 'warning' 
          });
        } else if (error.code === 'INVALID_URL') {
          setErrorToast({ 
            message: '视频链接格式不正确，请检查后重试', 
            type: 'error' 
          });
        } else {
          setErrorToast({ 
            message: error.message || '分析失败，请稍后重试', 
            type: 'error' 
          });
        }
      } else {
        setErrorToast({ 
          message: '网络连接失败，请检查网络', 
          type: 'error' 
        });
      }
    } finally {
      setLoading(false);
      setAnalysisProgress({ status: '', progress: 0, currentStep: '' });
    }
  };

  return (
    <div>
      {/* 加载状态 - 显示进度 */}
      {loading && (
        <div className="loading-overlay">
          <h3>{analysisProgress.currentStep || '正在分析...'}</h3>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${analysisProgress.progress}%` }}
            />
          </div>
          <p>{analysisProgress.progress}% 完成</p>
        </div>
      )}

      {/* 其他内容 */}
      <Dashboard onStartAnalysis={handleStartAnalysis} />
    </div>
  );
};
```

---

## 🎨 UI 优化建议

### 1. 加载状态

为所有 API 调用添加加载状态：

```typescript
// 骨架屏组件
const ProjectListSkeleton = () => (
  <div className="grid grid-cols-2 gap-8">
    {[1, 2, 3, 4].map(i => (
      <div key={i} className="animate-pulse">
        <div className="bg-gray-800 h-48 rounded-3xl" />
        <div className="bg-gray-800 h-4 w-3/4 mt-4 rounded" />
      </div>
    ))}
  </div>
);
```

### 2. 错误处理

创建统一的错误提示组件：

```typescript
const ErrorAlert = ({ error, onRetry }: { error: string; onRetry: () => void }) => (
  <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6">
    <p className="text-red-400">{error}</p>
    <button onClick={onRetry} className="mt-4 px-6 py-2 bg-red-600 rounded-xl">
      重试
    </button>
  </div>
);
```

### 3. 空状态

为没有数据的情况添加空状态：

```typescript
const EmptyState = ({ message }: { message: string }) => (
  <div className="flex flex-col items-center justify-center py-32 opacity-30">
    <Search size={64} />
    <p className="mt-6 text-xl font-bold">{message}</p>
  </div>
);
```

---

## 🔧 调试技巧

### 1. 开启 API 日志

在 `services/api.ts` 中添加请求日志：

```typescript
apiClient.interceptors.request.use(config => {
  console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
  return config;
});

apiClient.interceptors.response.use(response => {
  console.log(`[API] Response:`, response.data);
  return response;
});
```

### 2. Mock 服务器（开发阶段）

如果后端还没准备好，可以使用 Mock 服务器：

```bash
npm install -D json-server
```

创建 `mock/db.json`：

```json
{
  "stats": [
    {
      "label": "已分析视频",
      "value": "128",
      "icon": "FileVideo",
      "color": "text-blue-400",
      "bg": "bg-blue-400/10"
    }
  ],
  "projects": [
    {
      "id": "1",
      "title": "2024夏季穿搭爆款拆解",
      "score": 94
    }
  ]
}
```

启动 Mock 服务器：

```bash
npx json-server --watch mock/db.json --port 3000
```

---

## ✅ 迁移检查清单

- [ ] 环境变量配置完成
- [ ] 所有服务文件已创建
- [ ] API 客户端配置正确
- [ ] Token 认证机制已实现
- [ ] Dashboard 组件已迁移
- [ ] Discovery 组件已迁移
- [ ] KnowledgeBase 组件已迁移
- [ ] Editor 组件已迁移
- [ ] VideoSlideshow 组件已迁移
- [ ] 错误处理已完善
- [ ] 加载状态已添加
- [ ] 空状态已添加
- [ ] API 文档已与后端对齐
- [ ] 测试覆盖已完成

---

## 📝 后续优化

1. **添加请求取消机制**：使用 `AbortController` 取消未完成的请求
2. **实现请求缓存**：使用 React Query 或 SWR 管理服务端状态
3. **离线支持**：使用 Service Worker 实现离线缓存
4. **性能优化**：实现虚拟滚动、懒加载等
5. **单元测试**：为所有 API 服务添加单元测试

---

## 🆘 常见问题

### Q: CORS 错误怎么办？

A: 需要后端配置 CORS。开发阶段可以在 `vite.config.ts` 中配置代理：

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
});
```

### Q: Token 过期怎么处理？

A: 在 API 拦截器中自动刷新 Token：

```typescript
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // 尝试刷新 Token
      try {
        const newToken = await refreshToken();
        localStorage.setItem('rubik_token', newToken);
        // 重试原请求
        return apiClient.request(error.config);
      } catch {
        // 刷新失败，跳转登录
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

### Q: 如何处理文件上传进度？

A: 使用 axios 的 `onUploadProgress`：

```typescript
await apiClient.post('/slideshow/create', formData, {
  onUploadProgress: (progressEvent) => {
    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
    console.log(`上传进度: ${progress}%`);
  }
});
```

