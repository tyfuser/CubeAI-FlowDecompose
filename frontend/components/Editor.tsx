
import React, { useState, useEffect } from 'react';
import { Shot, CreationStrategy, TargetPlatform } from '../types';
import { 
  Type, Image as ImageIcon, Music, Scissors, Layout, 
  ChevronRight, MoreVertical, Plus, Save, Download, Share2,
  Sparkles, Wand2, Play, Volume2, Mic, Clock, Trash2, 
  Layers, Settings2, History, Copy, Info,
  Smartphone, Globe, Zap, MessageSquare, Send
} from 'lucide-react';

interface EditorProps {
  initialShots: Shot[];
  onGenerate: (strategy: CreationStrategy, platform: TargetPlatform) => Promise<void>;
  isGenerating?: boolean;
}

const Editor: React.FC<EditorProps> = ({ initialShots, onGenerate, isGenerating }) => {
  const [shots, setShots] = useState<Shot[]>(initialShots);
  const [activeShotId, setActiveShotId] = useState<number | null>(initialShots[0]?.id || null);
  const [activeStrategy, setActiveStrategy] = useState<CreationStrategy>('remake');
  const [activePlatform, setActivePlatform] = useState<TargetPlatform>('douyin');
  const [activeTab, setActiveTab] = useState<'content' | 'style' | 'asset'>('content');

  useEffect(() => {
    setShots(initialShots);
    if (initialShots.length > 0) {
      setActiveShotId(initialShots[0].id);
    }
  }, [initialShots]);

  const activeShot = shots.find(s => s.id === activeShotId);

  const strategies = [
    { id: 'remake', label: '1:1 复刻版', desc: '完美保留爆款节奏与核心结构', icon: Layers, color: 'text-orange-400' },
    { id: 'explainer', label: '深度解说版', desc: '强化信息密度与逻辑推导', icon: Info, color: 'text-blue-400' },
    { id: 'review', label: '好物测评版', desc: '优化信任建立与卖点透传', icon: Sparkles, color: 'text-green-400' },
    { id: 'mashup', label: '创意混剪版', desc: '多素材融合与视觉张力突破', icon: Scissors, color: 'text-purple-400' },
  ];

  const platforms = [
    { id: 'douyin', label: '抖音', icon: Smartphone, color: 'bg-black text-white', activeColor: 'bg-indigo-600', hover: 'hover:bg-gray-800' },
    { id: 'red', label: '小红书', icon: Send, color: 'bg-red-500 text-white', activeColor: 'bg-red-600', hover: 'hover:bg-red-400' },
    { id: 'bilibili', label: 'B站', icon: Globe, color: 'bg-blue-400 text-white', activeColor: 'bg-blue-500', hover: 'hover:bg-blue-300' },
  ];

  const currentStrategyInfo = strategies.find(s => s.id === activeStrategy);

  const handlePlatformSwitch = (platformId: TargetPlatform) => {
    setActivePlatform(platformId);
    onGenerate(activeStrategy, platformId);
  };

  const updateShot = (id: number, updates: Partial<Shot>) => {
    setShots(prev => prev.map(s => s.id === id ? { ...s, ...updates } : s));
  };

  const deleteShot = (id: number) => {
    setShots(prev => prev.filter(s => s.id !== id));
    if (activeShotId === id) setActiveShotId(shots[0]?.id || null);
  };

  return (
    <div className="flex h-full flex-col bg-[#0b0f1a] text-gray-100 overflow-hidden">
      {/* Top Toolbar */}
      <div className="flex flex-col border-b border-gray-800 bg-gray-950/80 backdrop-blur-md">
        <div className="flex items-center justify-between px-8 py-5">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="bg-indigo-600 p-2 rounded-xl shadow-[0_0_20px_rgba(79,70,229,0.3)]">
                <Wand2 size={20} className="text-white" />
              </div>
              <div>
                <h2 className="text-xl font-black tracking-tighter uppercase">创作中心</h2>
                <p className="text-[9px] font-black text-gray-500 tracking-widest uppercase">Rubik Script Studio</p>
              </div>
            </div>
            <div className="h-8 w-[1px] bg-gray-800" />
            <div className="flex bg-gray-900/50 p-1.5 rounded-2xl border border-gray-800 shadow-inner overflow-x-auto no-scrollbar">
              {strategies.map((strat) => (
                <button
                  key={strat.id}
                  onClick={() => {
                    setActiveStrategy(strat.id as CreationStrategy);
                    onGenerate(strat.id as CreationStrategy, activePlatform);
                  }}
                  className={`px-5 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 whitespace-nowrap ${
                    activeStrategy === strat.id 
                      ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-600/30 scale-105' 
                      : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/30'
                  }`}
                >
                  <strat.icon size={14} className={activeStrategy === strat.id ? 'text-white' : strat.color} />
                  {strat.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-black rounded-xl shadow-2xl shadow-indigo-600/20 transition-all active:scale-95 border border-indigo-500/20">
              <Save size={16} /> 保存草稿
            </button>
            <div className="h-6 w-[1px] bg-gray-800" />
            <button className="p-2.5 text-gray-500 hover:text-white transition-colors bg-gray-900 border border-gray-800 rounded-xl">
              <Share2 size={20} />
            </button>
          </div>
        </div>

        {/* Platform Selection Bar */}
        <div className="px-8 pb-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">适配目标平台:</span>
            <div className="flex gap-2">
              {platforms.map((p) => {
                const isActive = activePlatform === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => handlePlatformSwitch(p.id as TargetPlatform)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-black transition-all border ${
                      isActive 
                        ? `${p.activeColor} border-white/20 text-white shadow-lg scale-105` 
                        : `bg-gray-900 border-gray-800 text-gray-500 ${p.hover}`
                    }`}
                  >
                    <p.icon size={14} />
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="flex items-center gap-3 bg-indigo-600/10 px-4 py-2 rounded-xl border border-indigo-500/20">
             <Zap size={14} className="text-indigo-400 animate-pulse" />
             <span className="text-[10px] font-black text-indigo-300 uppercase tracking-widest">
               AI 已自动适配 {activePlatform === 'douyin' ? '高流量钩子' : activePlatform === 'red' ? '种草属性' : '交互引导'}
             </span>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Shot List Sidebar */}
        <div className="w-[420px] border-r border-gray-800 flex flex-col bg-gray-950/20 backdrop-blur-sm">
          <div className="p-6 border-b border-gray-800/50 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">
                分镜大纲 ({shots.length})
              </span>
              <p className="text-[10px] text-gray-600 font-medium italic mt-1">
                {activePlatform === 'red' ? '✨ 小红书风格重构完成' : activePlatform === 'bilibili' ? '📺 B站互动版本就绪' : '🔥 抖音爆款节奏映射中'}
              </p>
            </div>
            <button className="p-2 bg-indigo-600/10 hover:bg-indigo-600/20 rounded-xl text-indigo-400 transition-all border border-indigo-500/10">
              <Plus size={18} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin">
            {isGenerating ? (
              <div className="flex flex-col items-center justify-center h-full space-y-6 animate-pulse">
                <div className="relative">
                  <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
                  <Sparkles className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-indigo-400 w-5 h-5" />
                </div>
                <div className="text-center space-y-2">
                  <p className="text-sm font-black text-indigo-300">正在跨平台重构脚本...</p>
                  <p className="text-[10px] text-gray-600 font-mono italic">Adapting for {activePlatform.toUpperCase()}...</p>
                </div>
              </div>
            ) : (
              shots.map((shot, idx) => (
                <div 
                  key={shot.id}
                  onClick={() => setActiveShotId(shot.id)}
                  className={`group relative p-4 rounded-3xl border transition-all duration-300 cursor-pointer overflow-hidden ${
                    activeShotId === shot.id 
                      ? 'bg-indigo-600/10 border-indigo-500/50 shadow-2xl' 
                      : 'bg-[#111827]/30 border-gray-800 hover:border-gray-700'
                  }`}
                >
                  <div className="flex gap-4">
                    <div className="w-28 aspect-[9/16] bg-gray-900 rounded-2xl relative overflow-hidden flex-shrink-0 shadow-lg border border-white/5">
                      <img 
                        src={`https://picsum.photos/seed/editor_${shot.id}/200/355`} 
                        className="object-cover w-full h-full opacity-40 group-hover:opacity-60 transition-opacity" 
                        alt="" 
                      />
                      <div className="absolute top-2 left-2 bg-indigo-600/80 backdrop-blur px-2 py-0.5 rounded-lg text-[10px] font-black text-white shadow-lg">
                        {idx + 1}
                      </div>
                      <div className="absolute bottom-2 right-2 bg-black/60 backdrop-blur px-2 py-0.5 rounded-lg text-[10px] text-gray-300 font-mono">
                        {shot.duration}s
                      </div>
                    </div>
                    <div className="flex-1 min-w-0 flex flex-col justify-between py-1">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className={`text-[10px] font-black px-2 py-1 rounded-lg uppercase tracking-widest border ${
                            shot.type.includes('钩子') || shot.type.includes('情绪') 
                              ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' 
                              : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                          }`}>
                            {shot.type}
                          </span>
                          <div className="opacity-0 group-hover:opacity-100 transition-all flex gap-1">
                            <button onClick={(e) => { e.stopPropagation(); }} className="p-1.5 hover:bg-gray-800 rounded-lg text-gray-400"><Copy size={14}/></button>
                            <button onClick={(e) => { e.stopPropagation(); deleteShot(shot.id); }} className="p-1.5 hover:bg-red-900/50 rounded-lg text-gray-500 hover:text-red-400"><Trash2 size={14}/></button>
                          </div>
                        </div>
                        <p className="text-xs font-bold text-gray-100 line-clamp-3 leading-relaxed">
                          {shot.dialogue || shot.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-gray-500 mt-2 font-bold italic">
                         <Scissors size={12} className="text-gray-700"/>
                         <span className="truncate">{shot.transition}</span>
                      </div>
                    </div>
                  </div>
                  {activeShotId === shot.id && (
                    <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-indigo-500 rounded-full shadow-[0_0_15px_rgba(99,102,241,1)]" />
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Center: Main Editor Area */}
        <div className="flex-1 flex flex-col bg-[#0b0f1a] relative">
          <div className="flex-1 p-10 overflow-y-auto scrollbar-thin">
            {activeShot ? (
              <div className="max-w-5xl mx-auto space-y-12 animate-in fade-in slide-in-from-right-8 duration-500">
                <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                       <h3 className="text-3xl font-black tracking-tighter">镜头 #{shots.findIndex(s => s.id === activeShot.id) + 1} 编辑</h3>
                       <div className="px-3 py-1 bg-gray-900 border border-gray-800 rounded-xl flex items-center gap-2">
                         <div className={`w-2 h-2 rounded-full ${activePlatform === 'red' ? 'bg-red-500' : activePlatform === 'bilibili' ? 'bg-blue-400' : 'bg-white'}`} />
                         <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{activePlatform} Edition</span>
                       </div>
                    </div>
                    <p className="text-sm text-gray-500 font-medium italic">正在针对 <span className="text-indigo-400 font-bold">{currentStrategyInfo?.label}</span> 进行平台深度适配</p>
                  </div>
                  <div className="flex bg-gray-900/50 p-1.5 rounded-[1.5rem] border border-gray-800/50 shadow-xl">
                    {[
                      { id: 'content', label: '脚本内容', icon: Type },
                      { id: 'style', label: '视听风格', icon: Volume2 },
                      { id: 'asset', label: 'AI 资产', icon: ImageIcon }
                    ].map((tab) => (
                      <button 
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)} 
                        className={`px-6 py-2.5 rounded-2xl text-xs font-black transition-all flex items-center gap-2 ${activeTab === tab.id ? 'bg-gray-800 text-white shadow-lg border border-white/5' : 'text-gray-500 hover:text-gray-300'}`}
                      >
                        <tab.icon size={14} />
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </header>

                {activeTab === 'content' && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                    <div className="space-y-10">
                      {/* Platform Specific Tip */}
                      <div className="bg-gradient-to-r from-indigo-900/30 to-purple-900/20 p-6 rounded-[2rem] border border-indigo-500/20 space-y-3">
                         <div className="flex items-center gap-3 text-indigo-400">
                           <Zap size={18} />
                           <h4 className="text-[10px] font-black uppercase tracking-widest">AI 平台适配建议</h4>
                         </div>
                         <p className="text-xs text-indigo-100/80 leading-relaxed font-medium">
                           {activeShot.platformSpecific?.tip || (activePlatform === 'red' ? '建议在文案末尾加入 #Vlog #日常 等热门标签，并配合暖黄色调滤镜。' : activePlatform === 'douyin' ? '前1.5秒必须出现核心视觉反差点，建议台词节奏紧凑。' : '视频中段建议引导用户点击【一键三连】，增加长效权重。')}
                         </p>
                      </div>

                      {/* Dialogue/Script */}
                      <div className="space-y-4">
                        <label className="flex items-center gap-3 text-[10px] font-black text-gray-500 uppercase tracking-[0.25em]">
                          <div className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
                          配音台词与逻辑脚本 (Script)
                        </label>
                        <div className="relative group">
                          <textarea 
                            value={activeShot.dialogue}
                            onChange={(e) => updateShot(activeShot.id, { dialogue: e.target.value })}
                            className="w-full h-48 bg-[#0d111d] border border-gray-800 rounded-[2.5rem] p-8 text-sm leading-relaxed font-medium focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all resize-none shadow-2xl"
                            placeholder="在此输入台词..."
                          />
                          <div className="absolute top-6 right-6 flex flex-col gap-2">
                             <button className="p-2 bg-gray-900 border border-gray-800 rounded-xl text-gray-400 hover:text-indigo-400 transition-colors shadow-lg">
                               <Sparkles size={16} />
                             </button>
                             <button className="p-2 bg-gray-900 border border-gray-800 rounded-xl text-gray-400 hover:text-indigo-400 transition-colors shadow-lg">
                               <History size={16} />
                             </button>
                          </div>
                        </div>
                        <div className="flex justify-between items-center px-4">
                           <div className="flex items-center gap-4">
                              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">建议时长: <span className="text-indigo-400">{(activeShot.dialogue.length / 5.2).toFixed(1)}s</span></span>
                              <div className="w-1 h-1 rounded-full bg-gray-800" />
                              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">平台匹配度: <span className="text-green-400">极高</span></span>
                           </div>
                           <p className="text-[10px] font-black text-indigo-400 cursor-pointer hover:underline uppercase tracking-widest">同步优化全平台文案</p>
                        </div>
                      </div>

                      {/* Visual Description */}
                      <div className="space-y-4">
                        <label className="flex items-center gap-3 text-[10px] font-black text-gray-500 uppercase tracking-[0.25em]">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                          画面视觉提示词 (Visual Prompt)
                        </label>
                        <textarea 
                          value={activeShot.description}
                          onChange={(e) => updateShot(activeShot.id, { description: e.target.value })}
                          className="w-full h-36 bg-[#0d111d] border border-gray-800 rounded-[2.5rem] p-8 text-sm leading-relaxed font-medium focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all resize-none shadow-2xl"
                          placeholder="描述你想要的画面效果..."
                        />
                      </div>
                    </div>

                    <div className="space-y-8">
                       {/* Preview / Placeholder */}
                       <div className="space-y-4">
                        <label className="flex items-center gap-3 text-[10px] font-black text-gray-500 uppercase tracking-[0.25em]">
                          <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                          视觉概念预览 (Vision Preview)
                        </label>
                        <div className="aspect-[9/16] w-full bg-gray-900 rounded-[3rem] border border-gray-800 relative overflow-hidden group shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                           <img 
                            src={`https://picsum.photos/seed/vision_${activeShot.id}/400/711`} 
                            className="w-full h-full object-cover opacity-60 transition-transform duration-1000 group-hover:scale-110" 
                            alt="" 
                           />
                           <div className="absolute inset-0 bg-gradient-to-t from-gray-950/95 via-transparent to-transparent" />
                           <div className="absolute top-10 right-10 flex gap-2">
                              {activePlatform === 'red' && <div className="bg-red-500 p-2 rounded-xl text-white shadow-xl animate-bounce"><Send size={16}/></div>}
                              {activePlatform === 'bilibili' && <div className="bg-blue-400 p-2 rounded-xl text-white shadow-xl animate-pulse"><Globe size={16}/></div>}
                              {activePlatform === 'douyin' && <div className="bg-black border border-white/20 p-2 rounded-xl text-white shadow-xl"><Smartphone size={16}/></div>}
                           </div>
                           <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
                              <div className="w-20 h-20 bg-indigo-600 rounded-full flex items-center justify-center text-white shadow-2xl scale-90 group-hover:scale-100 transition-all cursor-pointer">
                                <Play size={32} fill="white" className="ml-1" />
                              </div>
                           </div>
                           <div className="absolute bottom-10 left-10 right-10 space-y-4">
                              <p className="text-xs text-indigo-200 font-bold leading-relaxed line-clamp-2">
                                “{activeShot.dialogue || "AI 正在理解脚本意图..."}”
                              </p>
                              <div className="flex gap-3">
                                <button className="flex-1 py-3.5 bg-white/10 hover:bg-white/20 backdrop-blur-xl border border-white/10 text-white rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all">
                                  渲染 {activePlatform} 预览
                                </button>
                                <button className="px-4 py-3.5 bg-gray-900/80 backdrop-blur-xl border border-white/5 text-white rounded-2xl transition-all">
                                  <Download size={16} />
                                </button>
                              </div>
                           </div>
                        </div>
                       </div>
                    </div>
                  </div>
                )}

                {activeTab === 'style' && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-10 py-4">
                    <div className="bg-gray-900/30 p-10 rounded-[3rem] border border-gray-800 space-y-8 shadow-2xl">
                       <h4 className="flex items-center gap-3 font-black text-sm uppercase tracking-widest text-white">
                         <div className="p-2 bg-indigo-500/10 rounded-xl text-indigo-400"><Volume2 size={20} /></div>
                         配音音色配置 (Voice)
                       </h4>
                       <div className="space-y-6">
                         <div className="flex items-center justify-between p-6 bg-gray-950 border border-gray-800 rounded-[2rem] hover:border-indigo-500/30 transition-all cursor-pointer group">
                           <div className="flex items-center gap-4">
                             <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-[1.2rem] flex items-center justify-center font-black text-xl shadow-lg">
                               {activePlatform === 'red' ? 'P' : activePlatform === 'bilibili' ? 'Z' : 'K'}
                             </div>
                             <div>
                               <p className="text-sm font-black text-white">
                                 {activePlatform === 'douyin' ? '爆款男声 - 极致快' : activePlatform === 'red' ? '温婉女声 - 治愈' : '中性男声 - 专业'}
                               </p>
                               <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest mt-1">Perfect match for {activePlatform}</p>
                             </div>
                           </div>
                           <Settings2 className="text-gray-700 group-hover:text-indigo-400 transition-colors" size={20}/>
                         </div>
                         <button className="w-full py-4 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 font-black rounded-2xl text-[10px] uppercase tracking-[0.2em] flex items-center justify-center gap-3 border border-indigo-500/20 transition-all">
                            <Mic size={16} /> 针对 {activePlatform} 语境试听
                         </button>
                       </div>
                    </div>

                    <div className="bg-gray-900/30 p-10 rounded-[3rem] border border-gray-800 space-y-8 shadow-2xl">
                       <h4 className="flex items-center gap-3 font-black text-sm uppercase tracking-widest text-white">
                         <div className="p-2 bg-blue-500/10 rounded-xl text-blue-400"><Music size={20} /></div>
                         BGM 库集成
                       </h4>
                       <div className="space-y-6">
                         <div className="p-6 bg-gray-950 border border-gray-800 rounded-[2rem] flex items-center gap-5">
                            <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-400 border border-blue-500/20">
                               <Music size={28} />
                            </div>
                            <div className="flex-1">
                               <p className="text-sm font-black text-white">{activePlatform === 'douyin' ? '抖音热门榜单 #1' : activePlatform === 'red' ? '咖啡馆午后 Lofi' : 'B站知识库专题 BGM'}</p>
                               <p className="text-[10px] text-gray-500 font-medium italic mt-1">已自动匹配该平台热度最高的配乐风格</p>
                            </div>
                         </div>
                         <div className="p-6 bg-indigo-600/5 border border-indigo-500/10 rounded-[2rem] space-y-4">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-black text-indigo-300 uppercase tracking-widest">跨平台 BGM 同步</span>
                              <div className="w-10 h-5 bg-indigo-600 rounded-full relative shadow-inner">
                                <div className="absolute right-1 top-1 w-3 h-3 bg-white rounded-full shadow-sm" />
                              </div>
                            </div>
                         </div>
                       </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-gray-800 space-y-6">
                <div className="relative">
                   <Layout size={80} className="stroke-[1] opacity-10" />
                   <Sparkles size={32} className="absolute -top-4 -right-4 text-indigo-500 opacity-20 animate-pulse" />
                </div>
                <div className="text-center">
                  <p className="font-black text-xl opacity-20 uppercase tracking-[0.3em]">请从左侧选择分镜或切换适配平台</p>
                  <p className="text-xs opacity-10 font-medium mt-2">Rubik Engine is Ready to Visualize Your Ideas</p>
                </div>
              </div>
            )}
          </div>

          {/* Bottom: Timeline View */}
          <div className="h-48 border-t border-gray-800 bg-gray-950/90 backdrop-blur-xl flex flex-col shadow-[0_-20px_50px_rgba(0,0,0,0.5)]">
             <div className="px-8 py-3 border-b border-gray-800/50 flex items-center justify-between text-[10px] font-black text-gray-600 uppercase tracking-[0.2em]">
                <div className="flex gap-8">
                  <span className="flex items-center gap-2 text-indigo-400"><Layers size={14}/> 创作时间轴</span>
                  <span className="flex items-center gap-2">
                    <Smartphone size={14} className="text-gray-700"/> 目标平台: <span className="text-white uppercase">{activePlatform}</span>
                  </span>
                </div>
                <div className="flex items-center gap-6">
                   <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse" />
                      <span>{activePlatform} 流量算法优化已开启</span>
                   </div>
                   <div className="h-3 w-[1px] bg-gray-800" />
                   <button className="hover:text-white transition-colors">分段导出</button>
                </div>
             </div>
             <div className="flex-1 p-6 relative overflow-x-auto scrollbar-none flex items-center gap-1">
                {shots.map((shot, i) => (
                  <div 
                    key={shot.id}
                    onClick={() => setActiveShotId(shot.id)}
                    style={{ width: `${shot.duration * 24}px`, minWidth: '60px' }}
                    className={`h-28 group relative rounded-[1.2rem] border transition-all duration-300 cursor-pointer flex flex-col overflow-hidden shadow-lg ${
                      activeShotId === shot.id 
                        ? 'bg-indigo-600/40 border-indigo-500 z-10 scale-105 shadow-indigo-500/20' 
                        : 'bg-[#111827] border-gray-800/50 hover:bg-gray-800/80'
                    }`}
                  >
                    <div className="flex-1 flex flex-col p-2.5">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[8px] font-black text-gray-500 uppercase">#{i + 1}</span>
                        <span className="text-[8px] font-mono text-indigo-300">{shot.duration}s</span>
                      </div>
                      <div className="flex-1 mt-1 border-t border-white/5 pt-1 overflow-hidden">
                         <p className="text-[8px] text-gray-400 line-clamp-2 leading-tight font-medium opacity-60">
                           {shot.dialogue || shot.description}
                         </p>
                      </div>
                    </div>
                  </div>
                ))}
                <button className="h-28 w-16 bg-gray-900 border-2 border-dashed border-gray-800 rounded-[1.2rem] flex items-center justify-center text-gray-700 hover:text-indigo-500 hover:border-indigo-500/50 transition-all flex-shrink-0 group">
                  <Plus size={24} className="group-hover:scale-125 transition-transform" />
                </button>
             </div>
          </div>
        </div>
      </div>

      {/* Floating Action Button */}
      <div className="fixed bottom-10 right-10 z-50 flex flex-col gap-5">
        <button className="w-16 h-16 bg-white text-gray-950 rounded-[1.8rem] shadow-2xl hover:scale-110 active:scale-95 transition-all group flex items-center justify-center">
          <Play size={28} fill="currentColor" />
          <div className="absolute right-full mr-6 top-1/2 -translate-y-1/2 bg-gray-900 text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest whitespace-nowrap opacity-0 group-hover:opacity-100 transition-all border border-gray-800 shadow-2xl">全片预览 ({activePlatform})</div>
        </button>
        <button className="w-16 h-16 bg-indigo-600 text-white rounded-[1.8rem] shadow-2xl hover:scale-110 active:scale-95 transition-all group flex items-center justify-center">
          <Download size={28} />
          <div className="absolute right-full mr-6 top-1/2 -translate-y-1/2 bg-gray-900 text-white px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest whitespace-nowrap opacity-0 group-hover:opacity-100 transition-all border border-gray-800 shadow-2xl">打包导出全平台适配包</div>
        </button>
      </div>
    </div>
  );
};

export default Editor;
