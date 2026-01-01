
import React, { useState, useEffect } from 'react';
import { 
  Search, Link, Upload, Clock, Star, Play, 
  TrendingUp, FileVideo, Zap, ArrowRight,
  Filter, MoreHorizontal, CheckCircle2, Timer,
  Globe, Sparkles, Flame, Fingerprint, MousePointer2,
  Calendar, Layers, Plus, ExternalLink
} from 'lucide-react';
import { 
  BarChart, Bar, ResponsiveContainer, Cell, Tooltip as RechartsTooltip, XAxis, YAxis
} from 'recharts';
import { ProjectSummary, ProjectStatus, AppSection } from '../types';
import { getDashboardStats, getProjects, getSchedule, DashboardStat, ScheduleDay, ScheduleTask } from '../services/dashboardService';
import { isApiError } from '../services/api';

interface DashboardProps {
  onStartAnalysis: (url: string) => void;
  onStartFileAnalysis: (file: File) => void;
  onViewDetails: (project: ProjectSummary) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onStartAnalysis, onStartFileAnalysis, onViewDetails }) => {
  const [url, setUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [inputMode, setInputMode] = useState<'url' | 'file' | 'path'>('url');
  const [localPath, setLocalPath] = useState('');
  
  // 从后端获取的数据
  const [stats, setStats] = useState<DashboardStat[]>([]);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [scheduleHeatmap, setScheduleHeatmap] = useState<ScheduleDay[]>([]);
  const [scheduleTasks, setScheduleTasks] = useState<ScheduleTask[]>([]);
  
  // 加载状态
  const [statsLoading, setStatsLoading] = useState(true);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [scheduleLoading, setScheduleLoading] = useState(true);

  // 图片加载状态
  const [imageLoadErrors, setImageLoadErrors] = useState<Set<string>>(new Set());

  // 组件挂载时加载数据
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    // 并行加载所有数据
    await Promise.all([
      loadStats(),
      loadProjects(),
      loadSchedule()
    ]);
  };

  const loadStats = async () => {
    try {
      setStatsLoading(true);
      const data = await getDashboardStats();
      setStats(data);
    } catch (error) {
      console.error('加载统计数据失败:', error);
      if (isApiError(error)) {
        console.error('错误详情:', error.message);
      }
      // 失败时使用默认数据
      setStats([
        { label: '已分析视频', value: '0', icon: 'FileVideo', color: 'text-blue-400', bg: 'bg-blue-400/10' },
        { label: '爆款基因库', value: '0', icon: 'Zap', color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
        { label: '节省创作时长', value: '0h', icon: 'Timer', color: 'text-green-400', bg: 'bg-green-400/10' },
        { label: '平均爆款分', value: '0', icon: 'TrendingUp', color: 'text-purple-400', bg: 'bg-purple-400/10' },
      ]);
    } finally {
      setStatsLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      setProjectsLoading(true);
      const data = await getProjects({ page: 1, limit: 4, sortBy: 'timestamp' });
      setProjects(data.projects);
    } catch (error) {
      console.error('加载项目列表失败:', error);
      // 失败时使用默认数据
      setProjects([
        { id: '1', title: "暂无项目数据", thumbnail: "https://picsum.photos/seed/default/400/225", timestamp: "刚刚", type: "示例", score: 0, status: 'draft', tags: ['示例'] },
      ]);
    } finally {
      setProjectsLoading(false);
    }
  };

  const loadSchedule = async () => {
    try {
      setScheduleLoading(true);
      const data = await getSchedule();
      setScheduleHeatmap(data.schedule);
      setScheduleTasks(data.tasks);
    } catch (error) {
      console.error('加载日程数据失败:', error);
      // 失败时使用默认数据
      setScheduleHeatmap([
        { day: 'Mon', intensity: 0 },
        { day: 'Tue', intensity: 0 },
        { day: 'Wed', intensity: 0 },
        { day: 'Thu', intensity: 0 },
        { day: 'Fri', intensity: 0 },
        { day: 'Sat', intensity: 0 },
        { day: 'Sun', intensity: 0 },
      ]);
      setScheduleTasks([]);
    } finally {
      setScheduleLoading(false);
    }
  };

  // Mock 数据（趋势和模板暂不从后端获取）

  // Mock 数据：趋势和模板（暂不从后端获取）
  const trends = [
    { title: '#AI数码测评', growth: '+240%', category: '科技', chart: [40, 60, 45, 90, 65, 80, 100] },
    { title: '#沉浸式收纳', growth: '+180%', category: '家居', chart: [30, 40, 70, 50, 85, 90, 95] },
    { title: '#三分钟看电影', growth: '+155%', category: '影视', chart: [50, 45, 60, 55, 70, 75, 80] },
  ];

  const templates = [
    { title: 'AIDA 经典复刻', color: 'bg-blue-500', heat: 92, desc: '注意、兴趣、欲望、行动' },
    { title: 'PAS 测评流', color: 'bg-purple-500', heat: 85, desc: '痛点、放大、解决方案' },
    { title: '情绪极限反转', color: 'bg-orange-600', heat: 78, desc: '预期偏差、情感爆发、结局收口' },
  ];

  // 获取图标组件
  const getIconComponent = (iconName: string) => {
    const iconMap: Record<string, any> = {
      FileVideo, Zap, Timer, TrendingUp
    };
    return iconMap[iconName] || FileVideo;
  };

  // 获取图片URL（处理相对路径）
  const getImageUrl = (thumbnail: string) => {
    if (thumbnail.startsWith('http')) {
      return thumbnail;
    }
    if (thumbnail.startsWith('/')) {
      const baseUrl = import.meta.env.VITE_SHOT_ANALYSIS_BASE_URL || 'http://localhost:8000';
      return `${baseUrl}${thumbnail}`;
    }
    return thumbnail;
  };

  // 处理图片加载错误
  const handleImageError = (projectId: string, e: React.SyntheticEvent<HTMLImageElement>) => {
    const target = e.target as HTMLImageElement;
    // 避免无限循环
    if (!imageLoadErrors.has(projectId)) {
      setImageLoadErrors(prev => new Set(prev).add(projectId));
      target.src = `https://picsum.photos/seed/${projectId}/400/225`;
    }
  };

  // 处理文件选择
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // 验证文件类型
      const validTypes = ['video/mp4', 'video/mov', 'video/avi', 'video/mkv', 'video/webm'];
      if (!validTypes.includes(file.type)) {
        alert('不支持的视频格式，请上传 MP4、MOV、AVI、MKV 或 WEBM 格式的视频');
        return;
      }
      // 验证文件大小（限制 500MB）
      const maxSize = 500 * 1024 * 1024;
      if (file.size > maxSize) {
        alert('文件过大，请上传小于 500MB 的视频');
        return;
      }
      setSelectedFile(file);
    }
  };

  // 处理分析提交
  const handleSubmit = () => {
    if (inputMode === 'url') {
      if (url.trim()) {
        onStartAnalysis(url);
      } else {
        alert('请输入视频链接');
      }
    } else if (inputMode === 'file') {
      if (selectedFile) {
        onStartFileAnalysis(selectedFile);
      } else {
        alert('请选择视频文件');
      }
    } else if (inputMode === 'path') {
      if (localPath.trim()) {
        onStartAnalysis(localPath);
      } else {
        alert('请输入本地文件路径');
      }
    }
  };

  const StatusBadge = ({ status }: { status: ProjectStatus }) => {
    switch (status) {
      case 'completed':
        return <span className="flex items-center gap-1.5 text-[9px] font-black text-green-400 bg-green-400/10 px-2.5 py-1 rounded-lg border border-green-500/20 uppercase tracking-widest">已解析</span>;
      case 'analyzing':
        return <span className="flex items-center gap-1.5 text-[9px] font-black text-blue-400 bg-blue-400/10 px-2.5 py-1 rounded-lg border border-blue-500/20 animate-pulse uppercase tracking-widest">分析中</span>;
      case 'draft':
        return <span className="flex items-center gap-1.5 text-[9px] font-black text-gray-400 bg-gray-400/10 px-2.5 py-1 rounded-lg border border-gray-500/20 uppercase tracking-widest">草稿</span>;
      default:
        return null;
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-[#0b0f1a] scrollbar-thin">
      <div className="p-8 lg:p-12 max-w-[1600px] mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
        
        {/* Top Navigation & Stats Bar */}
        <header className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-8">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
               <h2 className="text-4xl font-black tracking-tighter text-white italic">
                 Dashboard <span className="text-indigo-500">.</span>
               </h2>
               <div className="px-3 py-1 bg-indigo-600/10 border border-indigo-500/20 rounded-full flex items-center gap-2">
                 <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                 <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">System Active</span>
               </div>
            </div>
            <p className="text-gray-400 font-medium text-sm">欢迎回来，创作者。AI 已检测到 24 条新的爆款趋势，建议立即开始拆解。</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full xl:w-auto">
            {statsLoading ? (
              // 加载骨架屏
              [1, 2, 3, 4].map(i => (
                <div key={i} className="bg-gray-900/40 border border-gray-800/50 p-5 rounded-[2rem] min-w-[150px] animate-pulse">
                  <div className="w-8 h-8 bg-gray-800 rounded-xl mb-2" />
                  <div className="h-6 bg-gray-800 rounded mb-1" />
                  <div className="h-3 bg-gray-800 rounded w-3/4" />
                </div>
              ))
            ) : (
              stats.map((stat, i) => {
                const IconComponent = getIconComponent(stat.icon);
                return (
                  <div key={i} className="bg-gray-900/40 border border-gray-800/50 p-5 rounded-[2rem] flex flex-col gap-2 min-w-[150px] shadow-xl hover:border-indigo-500/30 transition-all group">
                    <div className={`p-2 rounded-xl w-fit ${stat.bg} ${stat.color} group-hover:scale-110 transition-transform`}>
                      <IconComponent size={16} />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-2xl font-black tracking-tighter text-white">{stat.value}</span>
                      <span className="text-[9px] text-gray-500 font-black uppercase tracking-[0.2em]">{stat.label}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </header>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
          
          {/* Left Column (8 cols) */}
          <div className="xl:col-span-8 space-y-10">
            <section className="relative overflow-hidden bg-gradient-to-br from-indigo-600/10 via-[#111827] to-[#0d111d] border border-indigo-500/20 p-10 lg:p-14 rounded-[4rem] shadow-2xl group">
              <div className="relative z-10 space-y-8">
                <div className="flex items-center gap-4">
                  <div className="bg-indigo-600 p-3 rounded-2xl shadow-2xl shadow-indigo-600/30">
                    <Zap className="text-white w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-3xl font-black text-white tracking-tight">智能基因拆解引擎</h3>
                    <p className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] mt-1">Multi-Modal Viral Analysis Engine 3.0</p>
                  </div>
                </div>

                <div className="space-y-6">
                  {/* 输入模式切换 */}
                  <div className="flex gap-2 bg-gray-950/60 p-1.5 rounded-[2rem] border border-gray-800 w-fit overflow-x-auto">
                    <button
                      onClick={() => { setInputMode('url'); setSelectedFile(null); setLocalPath(''); }}
                      className={`px-5 py-2 rounded-[1.5rem] text-xs font-black uppercase tracking-wider transition-all whitespace-nowrap ${
                        inputMode === 'url' 
                          ? 'bg-indigo-600 text-white shadow-lg' 
                          : 'text-gray-500 hover:text-gray-300'
                      }`}
                    >
                      <Link className="inline w-4 h-4 mr-2" />
                      在线链接
                    </button>
                    <button
                      onClick={() => { setInputMode('file'); setUrl(''); setLocalPath(''); }}
                      className={`px-5 py-2 rounded-[1.5rem] text-xs font-black uppercase tracking-wider transition-all whitespace-nowrap ${
                        inputMode === 'file' 
                          ? 'bg-indigo-600 text-white shadow-lg' 
                          : 'text-gray-500 hover:text-gray-300'
                      }`}
                    >
                      <Upload className="inline w-4 h-4 mr-2" />
                      文件上传
                    </button>
                    <button
                      onClick={() => { setInputMode('path'); setUrl(''); setSelectedFile(null); }}
                      className={`px-5 py-2 rounded-[1.5rem] text-xs font-black uppercase tracking-wider transition-all whitespace-nowrap ${
                        inputMode === 'path' 
                          ? 'bg-indigo-600 text-white shadow-lg' 
                          : 'text-gray-500 hover:text-gray-300'
                      }`}
                    >
                      <FileVideo className="inline w-4 h-4 mr-2" />
                      本地路径
                    </button>
                  </div>

                  <div className="flex flex-col md:flex-row gap-4">
                    {inputMode === 'url' ? (
                      <div className="relative flex-1">
                        <div className="absolute inset-y-0 left-6 flex items-center pointer-events-none text-gray-500 group-focus-within:text-indigo-400 transition-colors">
                          <Link className="h-6 w-6" />
                        </div>
                        <input
                          type="text"
                          className="block w-full pl-16 pr-8 py-6 bg-gray-950/80 border border-gray-700 rounded-[2.5rem] focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-gray-700 shadow-inner text-sm font-medium"
                          placeholder="支持抖音、小红书、B站等短视频链接..."
                          value={url}
                          onChange={(e) => setUrl(e.target.value)}
                        />
                      </div>
                    ) : inputMode === 'path' ? (
                      <div className="relative flex-1">
                        <div className="absolute inset-y-0 left-6 flex items-center pointer-events-none text-gray-500 group-focus-within:text-indigo-400 transition-colors">
                          <FileVideo className="h-6 w-6" />
                        </div>
                        <input
                          type="text"
                          className="block w-full pl-16 pr-8 py-6 bg-gray-950/80 border border-gray-700 rounded-[2.5rem] focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-gray-700 shadow-inner text-sm font-medium font-mono"
                          placeholder="输入服务器本地文件路径，如: /path/to/video.mp4"
                          value={localPath}
                          onChange={(e) => setLocalPath(e.target.value)}
                        />
                      </div>
                    ) : (
                      <div className="relative flex-1">
                        <input
                          type="file"
                          id="video-upload"
                          accept="video/mp4,video/mov,video/avi,video/mkv,video/webm"
                          onChange={handleFileChange}
                          className="hidden"
                        />
                        <label
                          htmlFor="video-upload"
                          className="flex items-center justify-between w-full px-6 py-6 bg-gray-950/80 border border-gray-700 rounded-[2.5rem] cursor-pointer hover:border-indigo-500/50 transition-all shadow-inner"
                        >
                          <div className="flex items-center gap-4">
                            <Upload className="h-6 w-6 text-gray-500" />
                            <span className="text-sm font-medium text-gray-300">
                              {selectedFile ? selectedFile.name : '点击选择视频文件...'}
                            </span>
                          </div>
                          {selectedFile && (
                            <span className="text-xs text-gray-500 font-mono">
                              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                            </span>
                          )}
                        </label>
                      </div>
                    )}
                    <button 
                      onClick={handleSubmit}
                      className="px-10 py-6 bg-white text-gray-950 font-black rounded-[2.5rem] transition-all shadow-2xl flex items-center justify-center gap-4 hover:scale-105 active:scale-95 text-xs uppercase tracking-[0.2em]"
                    >
                      立即开始 <ArrowRight className="w-5 h-5" />
                    </button>
                  </div>
                  
                  {/* 提示信息 */}
                  {inputMode === 'file' && (
                    <p className="text-xs text-gray-600 italic px-2">
                      支持格式: MP4, MOV, AVI, MKV, WEBM | 最大文件: 500MB
                    </p>
                  )}
                  {inputMode === 'path' && (
                    <div className="text-xs text-yellow-600/80 italic px-2 bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-3">
                      <p className="font-bold mb-1">⚠️ 临时方案：直接使用服务器本地文件</p>
                      <p>输入服务器上视频文件的绝对路径，如: <code className="text-yellow-400 font-mono">/Users/username/Videos/video.mp4</code></p>
                      <p className="mt-1 text-gray-500">注意：文件必须在后端服务器可访问的路径上</p>
                    </div>
                  )}
                </div>

                  <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="flex items-center gap-6">
                    <div className="flex -space-x-3">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="w-10 h-10 rounded-full border-4 border-[#0b0f1a] overflow-hidden bg-gray-800 shadow-lg">
                          <img 
                            src={`https://i.pravatar.cc/100?u=dashboard_${i}`} 
                            alt="用户头像" 
                            className="w-full h-full object-cover"
                            loading="lazy"
                          />
                        </div>
                      ))}
                    </div>
                    <p className="text-[11px] text-gray-500 font-medium">已有 <span className="text-white font-black">4,592+</span> 创作者正在使用同款引擎</p>
                  </div>
                </div>
              </div>
            </section>

            <section className="space-y-8">
              <div className="flex items-center justify-between border-b border-gray-800 pb-6">
                <div className="flex items-center gap-4">
                  <div className="bg-indigo-500 w-1.5 h-8 rounded-full shadow-[0_0_15px_rgba(99,102,241,0.5)]" />
                  <h3 className="text-2xl font-black text-white uppercase tracking-tight italic">最近分析记录</h3>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                {projectsLoading ? (
                  // 加载骨架屏
                  [1, 2, 3, 4].map(i => (
                    <div key={i} className="bg-gray-900/30 border border-gray-800/50 rounded-[3rem] overflow-hidden animate-pulse">
                      <div className="aspect-[16/9] bg-gray-950" />
                      <div className="p-8 space-y-4">
                        <div className="h-4 bg-gray-800 rounded w-3/4" />
                        <div className="h-3 bg-gray-800 rounded w-1/2" />
                      </div>
                    </div>
                  ))
                ) : projects.length > 0 ? (
                  projects.map(project => (
                  <div 
                    key={project.id} 
                    onClick={() => onViewDetails(project)}
                    className="group bg-gray-900/30 border border-gray-800/50 rounded-[3rem] overflow-hidden hover:border-indigo-500/50 transition-all flex flex-col cursor-pointer shadow-xl hover:shadow-indigo-500/20 active:scale-[0.98]"
                  >
                    <div className="aspect-[16/9] bg-gray-950 relative overflow-hidden">
                      <img 
                        src={getImageUrl(project.thumbnail)} 
                        alt={project.title} 
                        className="object-cover w-full h-full opacity-40 group-hover:opacity-100 transition-all duration-700 group-hover:scale-105"
                        onError={(e) => handleImageError(project.id, e)}
                        loading="lazy"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-[#0b0f1a] via-transparent to-transparent opacity-90" />
                      
                      <div className="absolute top-6 left-6 flex flex-col gap-2">
                        <StatusBadge status={project.status} />
                      </div>

                      <div className="absolute bottom-6 left-6 right-6 flex items-center justify-between">
                         <div className="flex gap-2">
                            <span className="text-[10px] font-black text-gray-400 bg-gray-900/80 px-2 py-1 rounded-lg border border-white/5">#{project.tags[0]}</span>
                         </div>
                         <div className="flex items-center gap-1.5 bg-indigo-600 px-2 py-1 rounded-lg text-[10px] font-black shadow-xl">
                           <Star size={12} className="fill-current text-white" />
                           {project.score}
                         </div>
                      </div>
                    </div>

                    <div className="p-8 space-y-4">
                      <h4 className="font-black text-white text-base group-hover:text-indigo-400 transition-colors leading-tight line-clamp-1">{project.title}</h4>
                      <div className="flex items-center justify-between text-[11px] font-bold text-gray-600 border-t border-white/5 pt-4">
                        <span className="flex items-center gap-1.5"><Clock size={14}/> {project.timestamp}</span>
                        <ArrowRight size={14} className="text-indigo-400" />
                      </div>
                    </div>
                  </div>
                  ))
                ) : (
                  <div className="col-span-2 flex flex-col items-center justify-center py-16 text-center opacity-50">
                    <FileVideo size={48} className="mb-4" />
                    <p className="text-gray-500">暂无项目数据</p>
                  </div>
                )}
              </div>
            </section>
          </div>

          {/* Right Column (4 cols) - Visualization Focus */}
          <div className="xl:col-span-4 space-y-10">
            
            {/* 实时爆款趋势 - 柱状图可视化 */}
            <section className="bg-gray-950 p-8 rounded-[3.5rem] border border-gray-800/50 shadow-2xl space-y-8 relative overflow-hidden group">
               <div className="flex items-center justify-between relative z-10">
                  <h3 className="font-black text-sm uppercase tracking-[0.2em] flex items-center gap-3 text-white">
                    <Globe className="text-indigo-500 animate-spin-slow" size={18} />
                    实时爆款趋势
                  </h3>
                  <button className="text-[10px] font-black text-indigo-400 uppercase tracking-widest hover:text-white transition-colors">查看全部</button>
               </div>
               
               <div className="space-y-6 relative z-10">
                 {trends.map((trend, i) => (
                   <div key={i} className="flex flex-col gap-3 p-5 bg-[#111827]/40 rounded-[2rem] border border-white/5 hover:border-indigo-500/40 transition-all cursor-pointer group shadow-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center font-black text-indigo-400 text-[10px] border border-white/5">
                            {i+1}
                          </div>
                          <div>
                            <p className="text-xs font-black text-white tracking-tight">{trend.title}</p>
                            <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">{trend.category}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-[10px] font-black text-green-400">{trend.growth}</p>
                        </div>
                      </div>
                      {/* Fix: Explicit height for chart container */}
                      <div className="h-10 w-full mt-1 min-h-[40px]">
                        <ResponsiveContainer width="99%" height="100%">
                          <BarChart data={trend.chart.map((v, idx) => ({ v, idx }))}>
                            <Bar dataKey="v" radius={[2, 2, 0, 0]}>
                              {trend.chart.map((entry, index) => (
                                <Cell key={index} fill={index === trend.chart.length - 1 ? '#6366f1' : '#374151'} fillOpacity={0.6} />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                   </div>
                 ))}
               </div>
            </section>

            {/* 常用叙事模版 - 热量表/刻度可视化 */}
            <section className="bg-gradient-to-br from-indigo-900/10 to-[#0d111d] p-8 rounded-[3.5rem] border border-indigo-500/10 space-y-8 shadow-xl relative overflow-hidden">
               <div className="flex items-center gap-3 relative z-10">
                  <Sparkles className="text-yellow-500" size={18} />
                  <h3 className="font-black text-sm uppercase tracking-[0.2em] text-white">常用叙事模版</h3>
               </div>
               <div className="space-y-6 relative z-10">
                  {templates.map((tpl, i) => (
                    <div key={i} className="p-6 bg-black/40 rounded-[2.5rem] border border-white/5 hover:bg-gray-800/60 transition-all cursor-pointer group shadow-inner space-y-4">
                       <div className="flex justify-between items-center">
                          <span className="text-xs font-black text-gray-200">{tpl.title}</span>
                          <span className="text-[10px] font-black text-indigo-400">{tpl.heat}% 成功率</span>
                       </div>
                       {/* Intensity / Heat Meter */}
                       <div className="relative h-1.5 w-full bg-gray-900 rounded-full overflow-hidden border border-white/5">
                          <div 
                            className={`absolute left-0 top-0 h-full ${tpl.color} opacity-80 shadow-[0_0_10px_rgba(99,102,241,0.5)] transition-all duration-1000`} 
                            style={{ width: `${tpl.heat}%` }} 
                          />
                          {/* Scale marks */}
                          <div className="absolute inset-0 flex justify-between px-2">
                             {[...Array(10)].map((_, idx) => (
                               <div key={idx} className="w-[1px] h-full bg-black/40" />
                             ))}
                          </div>
                       </div>
                       <p className="text-[9px] text-gray-600 font-medium uppercase tracking-widest">{tpl.desc}</p>
                    </div>
                  ))}
               </div>
            </section>

            {/* 本周创作计划 - 任务强度热力分布 */}
            <section className="bg-gray-900/40 p-10 rounded-[3.5rem] border border-gray-800/50 space-y-8 shadow-2xl relative">
               <div className="flex items-center justify-between">
                 <div className="flex items-center gap-3">
                    <Calendar className="text-gray-500" size={18} />
                    <h3 className="font-black text-sm uppercase tracking-[0.2em] text-gray-400">本周创作计划</h3>
                 </div>
                 <button className="p-2 bg-white/5 hover:bg-white/10 rounded-xl border border-white/5">
                   <Plus size={14} className="text-gray-400" />
                 </button>
               </div>

               {/* Task Intensity Heatmap (Mon-Sun) */}
               <div className="space-y-6">
                 {scheduleLoading ? (
                   <div className="animate-pulse">
                     <div className="h-16 bg-gray-800 rounded mb-4" />
                     <div className="space-y-2">
                       <div className="h-4 bg-gray-800 rounded" />
                       <div className="h-4 bg-gray-800 rounded w-3/4" />
                     </div>
                   </div>
                 ) : (
                   <>
                 <div className="flex justify-between items-end h-16 gap-1.5 min-h-[64px]">
                    {scheduleHeatmap.map((day, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center gap-2 group cursor-help h-full">
                         {/* Tooltip for Intensity */}
                         <div className="relative w-full flex-1 flex items-end">
                           <div 
                            className={`w-full rounded-lg transition-all duration-700 ${day.intensity > 70 ? 'bg-indigo-500' : day.intensity > 40 ? 'bg-indigo-700' : 'bg-gray-800'}`}
                            style={{ height: `${day.intensity}%`, opacity: day.intensity / 100 + 0.2 }}
                           />
                         </div>
                         <span className="text-[8px] font-black text-gray-600 group-hover:text-indigo-400 transition-colors uppercase">{day.day}</span>
                      </div>
                    ))}
                 </div>
                 
                 <div className="space-y-4 pt-4 border-t border-white/5">
                    {scheduleTasks.length > 0 ? scheduleTasks.map((task, i) => (
                      <div key={i} className="flex items-center gap-4 group cursor-pointer">
                        <div className={`w-2 h-2 rounded-full ${task.color} ${task.active ? 'animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.5)]' : ''}`} />
                        <span className={`text-[11px] font-black transition-colors ${task.active ? 'text-gray-300' : 'text-gray-600'}`}>
                          {task.label}
                        </span>
                      </div>
                    )) : (
                      <div className="text-center text-gray-600 text-xs py-4">暂无任务</div>
                    )}
                 </div>
                   </>
                 )}
               </div>
            </section>
          </div>
        </div>

      </div>

      <style>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 12s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
