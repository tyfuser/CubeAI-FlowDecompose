
import React from 'react';
import { AppSection } from '../types';
import { LayoutDashboard, BarChart3, Edit3, BookOpen, Settings, Zap, Compass, Presentation, Film } from 'lucide-react';

interface SidebarProps {
  activeSection: AppSection;
  onSectionChange: (section: AppSection) => void;
}

const RubikIcon = ({ className = "w-6 h-6" }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M12 2l9 5v10l-9 5-9-5V7l9-5z" />
    <path d="M12 22V12" />
    <path d="M12 12l9-5" />
    <path d="M12 12L3 7" />
    <path d="M7 4.75l9 5" opacity="0.3" />
    <path d="M7 19.25l9-5" opacity="0.3" />
    <path d="M16.5 4.75L7.5 9.75" opacity="0.3" />
    <path d="M16.5 19.25l-9-5" opacity="0.3" />
  </svg>
);

const Sidebar: React.FC<SidebarProps> = ({ activeSection, onSectionChange }) => {
  const navItems = [
    { id: AppSection.Dashboard, label: '总览面板', icon: LayoutDashboard },
    { id: AppSection.Analysis, label: '视频深度拆解', icon: BarChart3 },
    { id: AppSection.VideoSlideshow, label: '视频转幻灯片', icon: Presentation },
    { id: AppSection.ShotAnalysis, label: '镜头拆解分析', icon: Film },
    { id: AppSection.ShootingAssistant, label: 'AI 拍摄助手', icon: Zap },
    { id: AppSection.Editor, label: '创作中心', icon: Edit3 },
    { id: AppSection.KnowledgeBase, label: '灵感仓库', icon: BookOpen },
    { id: AppSection.Settings, label: '系统设置', icon: Settings },
  ];

  return (
    <aside className="w-72 bg-[#0d111d] border-r border-gray-800/50 flex flex-col h-full relative z-20 shadow-2xl">
      <div className="p-8 flex items-center gap-4">
        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl blur opacity-30 group-hover:opacity-75 transition duration-1000" />
          <div className="relative bg-[#0d111d] p-2.5 rounded-xl border border-white/5">
            <RubikIcon className="text-indigo-500 w-6 h-6" />
          </div>
        </div>
        <div>
          <h1 className="text-2xl font-black bg-gradient-to-br from-white via-gray-100 to-gray-500 bg-clip-text text-transparent tracking-tighter">
            魔方 AI
          </h1>
          <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest mt-0.5">RUBIK AI ENGINE</p>
        </div>
      </div>

      <nav className="flex-1 px-4 py-8 space-y-2">
        <p className="px-6 text-[10px] font-black text-gray-600 uppercase tracking-[0.25em] mb-4">主菜单</p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={`w-full flex items-center gap-4 px-6 py-4 rounded-2xl transition-all duration-300 group relative ${isActive
                  ? 'bg-indigo-600/10 text-white translate-x-1'
                  : 'text-gray-500 hover:text-gray-200 hover:bg-gray-800/30'
                }`}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-indigo-500 rounded-full shadow-[0_0_15px_rgba(99,102,241,0.8)]" />
              )}
              <Icon className={`w-5 h-5 transition-transform duration-300 ${isActive ? 'text-indigo-400 scale-110' : 'group-hover:scale-110'}`} />
              <span className="font-bold text-sm tracking-tight">{item.label}</span>
            </button>
          );
        })}

        <div className="pt-8">
          <p className="px-6 text-[10px] font-black text-gray-600 uppercase tracking-[0.25em] mb-4">创作探索</p>
          <button
            onClick={() => onSectionChange(AppSection.Discovery)}
            className={`w-full flex items-center gap-4 px-6 py-4 rounded-2xl transition-all duration-300 group relative ${activeSection === AppSection.Discovery
                ? 'bg-indigo-600/10 text-white translate-x-1'
                : 'text-gray-500 hover:text-gray-200 hover:bg-gray-800/30'
              }`}
          >
            {activeSection === AppSection.Discovery && (
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-indigo-500 rounded-full shadow-[0_0_15px_rgba(99,102,241,0.8)]" />
            )}
            <Compass className={`w-5 h-5 transition-transform duration-300 ${activeSection === AppSection.Discovery ? 'text-indigo-400 scale-110' : 'group-hover:rotate-45'}`} />
            <span className="font-bold text-sm tracking-tight">发现爆款案例</span>
          </button>
        </div>
      </nav>

      <div className="p-6">
        <div className="bg-gradient-to-br from-gray-900 to-black border border-white/5 rounded-[2rem] p-6 shadow-xl relative overflow-hidden group">
          <div className="absolute -top-10 -right-10 w-24 h-24 bg-indigo-500/10 blur-3xl group-hover:bg-indigo-500/20 transition-all" />
          <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2 font-bold">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            AI 引擎状态
          </p>
          <div className="flex items-end justify-between mb-2">
            <span className="text-sm font-black">Gemini 3 Pro</span>
            <span className="text-[9px] text-indigo-400 font-black tracking-widest bg-indigo-400/10 px-1.5 rounded">专业版</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-1.5 mb-2 overflow-hidden border border-white/5">
            <div className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full rounded-full w-[85%]" />
          </div>
          <p className="text-[10px] text-gray-600 font-bold">本月点数余额: 850 / 1,000</p>
          <button className="w-full mt-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-black rounded-xl transition-all shadow-lg shadow-indigo-600/20 uppercase tracking-widest">
            升级算力包
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
