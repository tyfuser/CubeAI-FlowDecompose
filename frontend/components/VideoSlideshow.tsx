
import React, { useState, useRef, useMemo } from 'react';
import { 
  Upload, FileVideo, Zap, Presentation, Download, Share2, 
  CheckCircle2, RefreshCw, Layers, Clock, Type, ChevronRight, 
  Layout, Edit3, Sparkles, Loader2, Save, FileType
} from 'lucide-react';
import { SlideData } from '../types';
import { regenerateSlideSummary } from '../services/geminiService';

const VideoSlideshow: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeStep, setActiveStep] = useState(0);
  const [mode, setMode] = useState<'concise' | 'detailed'>('detailed');
  const [slides, setSlides] = useState<SlideData[]>([]);
  const [selectedSlideId, setSelectedSlideId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const steps = [
    '提取关键帧素材',
    'AI 语义内容识别',
    '幻灯片布局自动化',
    'PPTX 结构渲染'
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const startAnalysis = () => {
    if (!file) return;
    setIsProcessing(true);
    setActiveStep(0);
    setProgress(0);

    let currentStep = 0;
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          finishAnalysis();
          return 100;
        }
        const newProgress = prev + 1;
        if (newProgress % 25 === 0 && currentStep < steps.length - 1) {
          currentStep++;
          setActiveStep(currentStep);
        }
        return newProgress;
      });
    }, 30);
  };

  const finishAnalysis = () => {
    const mockSlides: SlideData[] = [
      { id: '1', title: '视频概览：2024 夏季穿搭趋势', summary: '本幻灯片深度剖析了该爆款视频的叙事路径。封面通过高饱和度色彩瞬间锁定用户视线，通过“避雷”提示引发好奇。', timestamp: '00:00', imageUrl: 'https://picsum.photos/seed/slide1/800/450', layoutType: 'title' },
      { id: '2', title: '核心钩子：前3秒的视觉冲击', summary: '前3秒采用快切剪辑，平均每0.5秒一个画面转场。通过展示极端的“穿搭前后对比”，建立强烈的视觉落差，显著提升了留存率。', timestamp: '00:03', imageUrl: 'https://picsum.photos/seed/slide2/800/450', layoutType: 'content' },
      { id: '3', title: '痛点剖析：梨形身材的常见误区', summary: '视频进入中段，AI 识别出博主开始进行专业解说。针对梨形身材的三个痛点进行深度拆解，配合结构化文字贴纸，信息密度极高。', timestamp: '00:15', imageUrl: 'https://picsum.photos/seed/slide3/800/450', layoutType: 'content' },
      { id: '4', title: '逻辑总结与行动引导', summary: '收尾阶段，博主通过三句总结话术快速复盘。结尾巧妙留白并引导用户点击左下角同款，转化路径极短且自然。', timestamp: '00:45', imageUrl: 'https://picsum.photos/seed/slide4/800/450', layoutType: 'chapter' }
    ];
    setSlides(mockSlides);
    setSelectedSlideId(mockSlides[0].id);
    setIsProcessing(false);
  };

  // 根据模式过滤幻灯片
  const displaySlides = useMemo(() => {
    if (mode === 'concise') {
      return slides.filter(s => s.layoutType === 'title' || s.layoutType === 'chapter');
    }
    return slides;
  }, [slides, mode]);

  const currentSlide = slides.find(s => s.id === selectedSlideId);

  const updateCurrentSlide = (updates: Partial<SlideData>) => {
    if (!selectedSlideId) return;
    setSlides(prev => prev.map(s => s.id === selectedSlideId ? { ...s, ...updates } : s));
  };

  const handleRegenerateSummary = async () => {
    if (!currentSlide) return;
    setIsGeneratingSummary(true);
    try {
      const newSummary = await regenerateSlideSummary(currentSlide.title, currentSlide.summary);
      updateCurrentSlide({ summary: newSummary });
    } catch (e) {
      console.error(e);
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      // 模拟下载
      const link = document.createElement('a');
      link.href = '#';
      link.download = 'RubikAI_Presentation.pptx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      alert('幻灯片导出成功！');
    }, 2000);
  };

  return (
    <div className="h-full flex flex-col bg-[#05070a] overflow-hidden relative">
      {/* Background stardust */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]" />

      {/* Header */}
      <div className="p-8 border-b border-gray-800 bg-gray-950/50 backdrop-blur-xl flex items-center justify-between relative z-10">
        <div>
          <h2 className="text-3xl font-black tracking-tight flex items-center gap-3 italic">
            视频转幻灯片 <Presentation className="text-indigo-500" />
          </h2>
          <p className="text-gray-500 text-[10px] mt-1 font-black uppercase tracking-[0.3em]">Video to Presentation - AI Layout Engine</p>
        </div>
        
        {slides.length > 0 && (
          <div className="flex items-center gap-4">
            <div className="flex bg-gray-900/80 p-1 rounded-2xl border border-gray-800 shadow-inner">
               <button 
                 onClick={() => setMode('concise')}
                 className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase transition-all ${mode === 'concise' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-500 hover:text-gray-300'}`}
               >
                 精简版
               </button>
               <button 
                 onClick={() => setMode('detailed')}
                 className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase transition-all ${mode === 'detailed' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-500 hover:text-gray-300'}`}
               >
                 详细版
               </button>
            </div>
            <button 
              onClick={handleExport}
              disabled={isExporting}
              className="flex items-center gap-3 px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-black rounded-2xl transition-all shadow-2xl shadow-indigo-600/20 active:scale-95 disabled:opacity-50"
            >
               {isExporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />} 
               {isExporting ? '导出中...' : '导出 PPTX'}
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-hidden relative z-10">
        {slides.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-12">
            {!isProcessing ? (
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="w-full max-w-3xl aspect-video border-2 border-dashed border-gray-800 hover:border-indigo-500/50 rounded-[4rem] bg-gray-900/10 backdrop-blur-sm flex flex-col items-center justify-center gap-8 cursor-pointer group transition-all duration-700"
              >
                <input type="file" ref={fileInputRef} className="hidden" accept="video/*" onChange={handleFileChange} />
                <div className="relative">
                  <div className="absolute inset-0 bg-indigo-500/20 blur-[80px] rounded-full animate-pulse" />
                  <div className="relative bg-gray-950 p-10 rounded-[3rem] border border-white/5 shadow-2xl group-hover:scale-110 transition-transform">
                    {file ? <CheckCircle2 size={64} className="text-green-500" /> : <FileVideo size={64} className="text-indigo-400" />}
                  </div>
                </div>
                <div className="text-center space-y-3">
                  <h3 className="text-2xl font-black text-white">{file ? file.name : '点击或拖拽视频至此处'}</h3>
                  <p className="text-sm text-gray-500 font-medium italic">AI 将自动识别关键帧、生成脚本摘要并排版幻灯片</p>
                </div>
                {file && (
                  <button 
                    onClick={(e) => { e.stopPropagation(); startAnalysis(); }}
                    className="mt-4 px-12 py-5 bg-white text-gray-950 font-black rounded-[2.5rem] hover:scale-105 active:scale-95 transition-all shadow-2xl flex items-center gap-4 uppercase tracking-[0.2em] text-xs"
                  >
                    开始 AI 转换引擎 <Zap size={18} fill="currentColor" />
                  </button>
                )}
              </div>
            ) : (
              <div className="w-full max-w-2xl space-y-16 animate-in fade-in zoom-in duration-500">
                <div className="flex flex-col items-center gap-10">
                  <div className="relative">
                    <div className="w-40 h-40 border-8 border-indigo-500/5 border-t-indigo-500 rounded-full animate-spin shadow-[0_0_50px_rgba(99,102,241,0.2)]" />
                    <Presentation className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-indigo-400 w-14 h-14 animate-pulse" />
                  </div>
                  <div className="text-center space-y-6">
                    <h3 className="text-3xl font-black text-white tracking-widest uppercase italic">
                      AI Processing <span className="text-indigo-500 animate-pulse">...</span>
                    </h3>
                    <div className="w-[500px] bg-gray-900 rounded-full h-3 border border-white/5 overflow-hidden shadow-inner">
                      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 h-full transition-all duration-300 shadow-[0_0_20px_rgba(99,102,241,0.6)]" style={{ width: `${progress}%` }} />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-8">
                  {steps.map((step, idx) => (
                    <div key={idx} className={`flex flex-col items-center gap-4 transition-all duration-500 ${idx <= activeStep ? 'opacity-100 scale-105' : 'opacity-20 scale-95'}`}>
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border-2 font-black text-xs ${idx < activeStep ? 'bg-green-500 border-green-400 text-white' : idx === activeStep ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-gray-950 border-gray-800 text-gray-600'}`}>
                        {idx < activeStep ? <CheckCircle2 size={20} /> : idx + 1}
                      </div>
                      <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest text-center">{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex">
            {/* Slide List Sidebar */}
            <div className="w-[420px] border-r border-gray-800 bg-gray-950/20 overflow-y-auto scrollbar-thin p-8 space-y-6">
              <div className="flex items-center justify-between mb-4 border-b border-gray-800 pb-4">
                 <span className="text-[10px] font-black text-gray-600 uppercase tracking-[0.3em]">
                   幻灯片结构 / {displaySlides.length} PAGES
                 </span>
                 <button className="p-2 text-gray-600 hover:text-white transition-colors"><RefreshCw size={14}/></button>
              </div>
              {displaySlides.map((slide, idx) => (
                <div 
                  key={slide.id}
                  onClick={() => setSelectedSlideId(slide.id)}
                  className={`group relative p-4 rounded-[2.5rem] border transition-all cursor-pointer overflow-hidden ${selectedSlideId === slide.id ? 'bg-indigo-600/10 border-indigo-500 shadow-2xl scale-105' : 'bg-gray-900/30 border-gray-800 hover:border-gray-700'}`}
                >
                  <div className="flex gap-4">
                    <div className="w-36 aspect-video bg-gray-950 rounded-[1.2rem] relative overflow-hidden flex-shrink-0 border border-white/5">
                      <img src={slide.imageUrl} className="w-full h-full object-cover opacity-60 group-hover:opacity-100 group-hover:scale-110 transition-all duration-700" />
                      <div className="absolute top-2 left-2 px-2 py-0.5 bg-indigo-600/90 backdrop-blur rounded-lg text-[10px] font-black text-white shadow-lg">{idx + 1}</div>
                    </div>
                    <div className="flex-1 min-w-0 space-y-2 py-1 flex flex-col justify-center">
                      <h4 className="text-xs font-black text-white line-clamp-1">{slide.title}</h4>
                      <div className="flex items-center justify-between">
                         <p className="text-[9px] text-gray-500 font-black italic flex items-center gap-1 uppercase tracking-widest">
                           <Clock size={10} /> {slide.timestamp}
                         </p>
                         <span className="px-2 py-0.5 bg-gray-800 rounded-md text-[8px] font-black text-gray-500 uppercase border border-white/5">{slide.layoutType}</span>
                      </div>
                    </div>
                  </div>
                  {selectedSlideId === slide.id && (
                    <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-indigo-500 rounded-full" />
                  )}
                </div>
              ))}
            </div>

            {/* Main Preview Area */}
            <div className="flex-1 bg-[#05070a] p-12 overflow-y-auto scrollbar-thin">
              {currentSlide ? (
                <div className="max-w-5xl mx-auto space-y-12 animate-in fade-in slide-in-from-right-8 duration-500">
                  {/* PPT Preview Box */}
                  <div className="aspect-video bg-gray-900 rounded-[3.5rem] border border-gray-800 shadow-2xl relative overflow-hidden group">
                     <img src={currentSlide.imageUrl} className="w-full h-full object-cover opacity-30 group-hover:scale-105 transition-transform duration-[3000ms]" />
                     <div className="absolute inset-0 bg-gradient-to-t from-[#05070a] via-transparent to-transparent opacity-90" />
                     
                     {/* Text Overlay Simulation */}
                     <div className="absolute inset-0 p-16 md:p-24 flex flex-col justify-end gap-8 relative z-10">
                        {currentSlide.layoutType === 'title' ? (
                          <div className="space-y-6">
                            <div className="w-24 h-1.5 bg-indigo-500 rounded-full" />
                            <h3 className="text-6xl font-black text-white tracking-tighter italic uppercase leading-tight drop-shadow-2xl">{currentSlide.title}</h3>
                            <div className="flex items-center gap-4">
                               <p className="text-indigo-400 font-black text-sm uppercase tracking-[0.4em]">Video Case Analysis Report</p>
                            </div>
                          </div>
                        ) : currentSlide.layoutType === 'chapter' ? (
                          <div className="space-y-8">
                             <div className="flex items-center gap-6">
                                <span className="px-5 py-2 bg-indigo-600 text-white text-xs font-black rounded-xl shadow-2xl">CHAPTER {slides.findIndex(s => s.id === currentSlide.id) + 1}</span>
                                <div className="h-[1px] flex-1 bg-white/10" />
                             </div>
                             <h3 className="text-4xl font-black text-white italic tracking-tight">{currentSlide.title}</h3>
                             <p className="text-gray-400 text-base font-medium leading-relaxed max-w-2xl italic border-l-4 border-indigo-500/30 pl-8">
                               {currentSlide.summary}
                             </p>
                          </div>
                        ) : (
                          <div className="space-y-6">
                             <div className="flex items-center gap-3">
                                <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Detail Insight</span>
                                <div className="w-12 h-[1px] bg-indigo-500/50" />
                             </div>
                             <h3 className="text-3xl font-black text-white">{currentSlide.title}</h3>
                             <div className="grid grid-cols-2 gap-10">
                                <p className="text-gray-400 text-sm font-medium leading-relaxed italic opacity-80">
                                  {currentSlide.summary}
                                </p>
                                <div className="bg-white/5 rounded-3xl p-6 border border-white/5 backdrop-blur-md">
                                   <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-3">Key Frames Detection</p>
                                   <div className="grid grid-cols-3 gap-2">
                                      {[1, 2, 3].map(i => <div key={i} className="aspect-square bg-gray-800 rounded-xl overflow-hidden border border-white/5"><img src={`https://picsum.photos/seed/thumb${i}/100/100`} className="w-full h-full object-cover opacity-50" /></div>)}
                                   </div>
                                </div>
                             </div>
                          </div>
                        )}
                     </div>
                     
                     <div className="absolute top-10 right-10 flex gap-4 z-20">
                        <button className="p-4 bg-black/40 hover:bg-indigo-600/80 backdrop-blur border border-white/10 rounded-2xl text-white transition-all shadow-xl group">
                          <Edit3 size={20} className="group-hover:scale-110 transition-transform"/>
                        </button>
                        <button className="p-4 bg-black/40 hover:bg-indigo-600/80 backdrop-blur border border-white/10 rounded-2xl text-white transition-all shadow-xl group">
                          <Layout size={20} className="group-hover:rotate-90 transition-transform duration-500"/>
                        </button>
                     </div>
                  </div>

                  {/* Editing Controls - Functional Area */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div className="space-y-8">
                       <div className="space-y-4">
                          <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] flex items-center gap-3 px-4">
                            <Type size={14} className="text-indigo-500" /> 幻灯片标题 (Editable)
                          </label>
                          <input 
                            type="text" 
                            value={currentSlide.title}
                            onChange={(e) => updateCurrentSlide({ title: e.target.value })}
                            className="w-full bg-gray-950 border border-gray-800 rounded-[2rem] px-8 py-6 text-sm font-black text-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all shadow-inner"
                          />
                       </div>
                       
                       <div className="flex items-center gap-6">
                          <div className="flex-1 space-y-4">
                             <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-4">布局风格</label>
                             <div className="flex bg-gray-900/50 p-1.5 rounded-[1.5rem] border border-gray-800 shadow-inner">
                                {['title', 'chapter', 'content'].map(l => (
                                  <button 
                                    key={l} 
                                    onClick={() => updateCurrentSlide({ layoutType: l as any })}
                                    className={`flex-1 py-3 rounded-xl text-[9px] font-black uppercase transition-all ${currentSlide.layoutType === l ? 'bg-indigo-600 text-white shadow-xl' : 'text-gray-600 hover:text-gray-400'}`}
                                  >
                                    {l}
                                  </button>
                                ))}
                             </div>
                          </div>
                          <div className="space-y-4">
                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-4">时间点</label>
                            <div className="px-8 py-4 bg-gray-950 border border-gray-800 rounded-[1.5rem] text-xs font-mono text-indigo-400 font-black shadow-inner">
                              {currentSlide.timestamp}
                            </div>
                          </div>
                       </div>
                    </div>

                    <div className="space-y-6">
                       <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] flex items-center gap-3 px-4">
                         <Zap size={14} className="text-indigo-400" /> AI 逻辑摘要 (50-100字)
                       </label>
                       <div className="relative group">
                          <textarea 
                            value={currentSlide.summary}
                            onChange={(e) => updateCurrentSlide({ summary: e.target.value })}
                            className="w-full h-44 bg-gray-950 border border-gray-800 rounded-[2.5rem] p-8 text-sm leading-relaxed font-medium text-gray-400 focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all resize-none shadow-inner"
                            placeholder="AI 分析内容..."
                          />
                          <div className="absolute top-4 right-4 flex flex-col gap-2">
                             <button className="p-2.5 bg-gray-900 border border-gray-800 rounded-xl text-gray-500 hover:text-indigo-400 transition-all shadow-xl">
                               <Save size={16} />
                             </button>
                          </div>
                       </div>
                       <div className="flex gap-4">
                          <button className="p-5 bg-gray-900 border border-gray-800 rounded-2xl text-gray-500 hover:text-white transition-all shadow-xl active:scale-95"><Share2 size={20}/></button>
                          <button 
                            onClick={handleRegenerateSummary}
                            disabled={isGeneratingSummary}
                            className="flex-1 py-5 bg-white/5 hover:bg-indigo-600/10 border border-white/5 hover:border-indigo-500/30 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] text-white transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                          >
                            {isGeneratingSummary ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />} 
                            {isGeneratingSummary ? '正在构思中...' : '重新生成摘要'}
                          </button>
                       </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center space-y-8 opacity-20 grayscale">
                   <div className="relative">
                      <Presentation size={120} className="stroke-[1]" />
                      <Sparkles className="absolute -top-4 -right-4 animate-bounce" size={40} />
                   </div>
                   <div className="text-center">
                     <h3 className="text-2xl font-black uppercase tracking-[0.4em]">请选择幻灯片页码</h3>
                     <p className="text-sm font-medium mt-2 italic">Select a slide to start intelligent editing</p>
                   </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <style>{`
        .scrollbar-none::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-none {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
};

export default VideoSlideshow;
