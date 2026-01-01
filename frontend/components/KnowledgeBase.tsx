
import React, { useState, useEffect } from 'react';
import { 
  Search, Filter, Bookmark, Star, Zap, 
  MessageSquare, Layout, Music, Palette, 
  ArrowUpRight, Share2, Plus, Hash, 
  Sparkles, Flame, Fingerprint
} from 'lucide-react';
import { getKBItems, KBItem, KBCategory } from '../services/knowledgeService';
import { isApiError } from '../services/api';

const KnowledgeBase: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<KBCategory>('hooks');
  const [searchQuery, setSearchQuery] = useState('');
  const [items, setItems] = useState<KBItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ page: 1, total: 0 });

  const categories = [
    { id: 'hooks', label: '钩子模板', icon: AnchorIcon },
    { id: 'narrative', label: '叙事结构', icon: Layout },
    { id: 'style', label: '话术风格', icon: MessageSquare },
    { id: 'bgm', label: '音效BGM', icon: Music },
    { id: 'fingerprints', label: '爆款指纹', icon: Fingerprint },
  ];

  // 当分类改变时重新加载
  useEffect(() => {
    setPagination({ page: 1, total: 0 });
    loadItems();
  }, [activeCategory]);

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      setPagination({ page: 1, total: 0 });
      loadItems();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

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
      if (isApiError(error)) {
        console.error('错误详情:', error.message);
      }
      // 失败时清空列表
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredItems = items;

  return (
    <div className="h-full flex flex-col bg-gray-900 text-gray-100 overflow-hidden">
      {/* KB Header */}
      <header className="p-8 border-b border-gray-800 bg-gray-950/50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <h2 className="text-3xl font-black tracking-tight flex items-center gap-3">
              灵感仓库 <Sparkles className="text-yellow-500 animate-pulse" size={24} />
            </h2>
            <p className="text-gray-500 text-sm mt-1 font-medium italic">汇聚千万级爆款逻辑，你的创意弹药库。</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-indigo-400 transition-colors" size={18} />
              <input 
                type="text" 
                placeholder="搜索模板、标签、关键词..." 
                className="bg-gray-900 border border-gray-800 rounded-2xl pl-12 pr-6 py-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none w-full md:w-80 transition-all shadow-inner"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="bg-indigo-600 hover:bg-indigo-700 p-3 rounded-2xl text-white shadow-lg shadow-indigo-600/20 transition-all active:scale-95">
              <Plus size={20} />
            </button>
          </div>
        </div>

        {/* Categories Tabs */}
        <div className="max-w-7xl mx-auto mt-8 flex gap-2 overflow-x-auto pb-2 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id as KBCategory)}
              className={`flex items-center gap-2 px-6 py-3 rounded-2xl text-sm font-bold transition-all whitespace-nowrap border ${
                activeCategory === cat.id 
                  ? 'bg-indigo-600 border-indigo-500 text-white shadow-xl shadow-indigo-600/20 translate-y-[-2px]' 
                  : 'bg-gray-900 border-gray-800 text-gray-500 hover:text-gray-300 hover:border-gray-700'
              }`}
            >
              <cat.icon size={16} />
              {cat.label}
            </button>
          ))}
        </div>
      </header>

      {/* KB Content */}
      <div className="flex-1 overflow-y-auto p-8 scrollbar-thin">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            // 加载骨架屏
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="bg-gray-800/40 border border-gray-700/50 rounded-[2.5rem] overflow-hidden animate-pulse">
                  <div className="h-40 bg-gray-700" />
                  <div className="p-6 space-y-4">
                    <div className="h-4 bg-gray-700 rounded w-3/4" />
                    <div className="h-3 bg-gray-700 rounded" />
                    <div className="flex gap-2">
                      <div className="h-6 bg-gray-700 rounded w-16" />
                      <div className="h-6 bg-gray-700 rounded w-20" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : filteredItems.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {filteredItems.map((item) => (
                <div 
                  key={item.id} 
                  className="group bg-gray-800/40 border border-gray-700/50 rounded-[2.5rem] overflow-hidden hover:border-indigo-500/50 transition-all flex flex-col shadow-lg hover:shadow-indigo-500/10 cursor-pointer"
                >
                  <div className={`h-40 bg-gradient-to-br ${item.previewColor} relative p-6 flex flex-col justify-between`}>
                    <div className="absolute inset-0 bg-black/20" />
                    <div className="relative z-10 flex justify-between items-start">
                       <div className="bg-white/10 backdrop-blur-md px-3 py-1 rounded-full border border-white/20 text-[10px] font-black uppercase tracking-widest text-white shadow-sm">
                         {item.category}
                       </div>
                       <button className="p-2 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 text-white hover:bg-white/20 transition-all">
                         <Bookmark size={14} />
                       </button>
                    </div>
                    <div className="relative z-10">
                      <h4 className="text-xl font-black text-white group-hover:translate-x-1 transition-transform">{item.title}</h4>
                    </div>
                    {/* Decorative Zap */}
                    <Zap className="absolute -bottom-6 -right-6 w-32 h-32 text-white/10 -rotate-12 group-hover:rotate-0 transition-transform duration-700" />
                  </div>
                  
                  <div className="p-6 flex-1 flex flex-col justify-between space-y-4">
                    <p className="text-sm text-gray-400 leading-relaxed italic line-clamp-2">
                      "{item.description}"
                    </p>
                    
                    <div className="flex flex-wrap gap-2">
                      {item.tags.map(tag => (
                        <span key={tag} className="flex items-center gap-1 text-[10px] font-bold text-gray-500 bg-gray-900 px-2 py-1 rounded-lg border border-gray-800 group-hover:border-indigo-500/30 transition-colors">
                          <Hash size={10} /> {tag}
                        </span>
                      ))}
                    </div>

                    <div className="pt-4 border-t border-gray-800 flex items-center justify-between">
                       <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1.5">
                            <Flame size={12} className="text-orange-500" />
                            <span className="text-[10px] font-bold text-gray-500">{item.usageCount} 使用</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <Star size={12} className="text-yellow-500 fill-yellow-500" />
                            <span className="text-[10px] font-bold text-gray-500">{item.rating}</span>
                          </div>
                       </div>
                       <button className="flex items-center gap-1.5 text-[10px] font-black text-indigo-400 uppercase tracking-widest hover:text-indigo-300 transition-colors">
                         立即使用 <ArrowUpRight size={14} />
                       </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-32 space-y-6 opacity-30">
               <div className="relative">
                 <Search size={64} className="stroke-[1]" />
                 <div className="absolute -top-2 -right-2 p-2 bg-gray-800 rounded-full">
                    <Zap size={24} className="fill-gray-600 text-gray-600" />
                 </div>
               </div>
               <div className="text-center">
                 <h3 className="text-xl font-bold">
                   {searchQuery ? '没有找到匹配项' : '暂无数据'}
                 </h3>
                 <p className="text-sm">
                   {searchQuery ? '尝试更换搜索词或选择其他分类' : '该分类下暂无内容'}
                 </p>
               </div>
            </div>
          )}
        </div>
      </div>

      {/* Team Collaboration Bar */}
      <footer className="bg-gray-950 border-t border-gray-800 p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
             <div className="flex -space-x-2">
                {[1, 2, 3].map(i => (
                  <img key={i} src={`https://i.pravatar.cc/100?u=team${i}`} className="w-8 h-8 rounded-full border-2 border-gray-950" />
                ))}
             </div>
             <p className="text-xs text-gray-500 font-medium">团队已共享 12 个私有模板</p>
          </div>
          <button className="flex items-center gap-2 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors">
            <Share2 size={14} /> 共享到团队灵感库
          </button>
        </div>
      </footer>
    </div>
  );
};

// Simple Icon Fallback for the Anchor icon if not directly in lucide
const AnchorIcon = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="5" r="3" />
    <path d="M12 22V8" />
    <path d="M5 12H2a10 10 0 0 0 20 0h-3" />
  </svg>
);

export default KnowledgeBase;
