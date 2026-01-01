
import React, { useRef, useState } from 'react';
import { VideoAnalysis, AppSection } from '../types';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell
} from 'recharts';
import { 
  Zap, Flame, Scissors, Eye, 
  Volume2, Type, Star, FileText, Image as ImageIcon, Share2,
  CheckCircle2, Lightbulb, ArrowRight, BarChart3, Download, TrendingUp,
  Info, Target, MessageSquare, Fingerprint, FileDown, Printer, Copy, Check
} from 'lucide-react';

interface AnalysisPanelProps {
  analysis: VideoAnalysis | null;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({ analysis }) => {
  const reportRef = useRef<HTMLDivElement>(null);
  const radarRef = useRef<HTMLDivElement>(null);
  const rhythmRef = useRef<HTMLDivElement>(null);
  const [isSharing, setIsSharing] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);

  if (!analysis) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center animate-in fade-in duration-700">
        <div className="relative mb-8">
          <div className="absolute inset-0 bg-indigo-500/20 blur-[100px] rounded-full animate-pulse" />
          <div className="relative bg-gray-900/50 p-10 rounded-[3rem] border border-white/5 backdrop-blur-3xl shadow-2xl group">
             <div className="bg-indigo-600/10 p-6 rounded-[2rem] border border-indigo-500/20">
               <BarChart3 size={64} className="text-indigo-400 group-hover:scale-110 transition-transform duration-500" />
             </div>
          </div>
        </div>
        <div className="max-w-md space-y-6 relative z-10">
          <h3 className="text-3xl font-black tracking-tight text-white italic">暂无分析报告</h3>
          <p className="text-gray-400 text-sm font-medium">请前往总览面板提交视频链接，AI 将立即为您生成深度基因报告。</p>
          <button 
            onClick={() => window.dispatchEvent(new CustomEvent('changeSection', { detail: AppSection.Dashboard }))}
            className="px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-black rounded-2xl transition-all shadow-xl shadow-indigo-600/20 flex items-center justify-center gap-3 mx-auto text-xs uppercase tracking-widest"
          >
            前往工作台 <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // 环形图数据
  const hookScoreData = [
    { name: 'score', value: analysis.hookScore },
    { name: 'total', value: 100 - analysis.hookScore }
  ];

  const handleExportPDF = () => {
    // 打印前微调
    document.title = `魔方AI_爆款分析报告_${analysis.title}`;
    window.print();
  };

  const handleShare = async () => {
    const shareData = {
      title: `魔方 AI 分析报告: ${analysis.title}`,
      text: `来看看这个视频的爆款基因分析报告，Hook分高达 ${(analysis.hookScore/10).toFixed(1)} 分！`,
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        console.log('Share cancelled or failed');
      }
    } else {
      // 降级到复制链接
      try {
        await navigator.clipboard.writeText(window.location.href);
        setShareSuccess(true);
        setTimeout(() => setShareSuccess(false), 2000);
      } catch (err) {
        alert('无法复制链接，请手动复制浏览器地址栏');
      }
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-[#0b0f1a] scrollbar-thin text-gray-100 print:bg-white print:text-black">
      <div ref={reportRef} className="p-8 lg:p-12 max-w-[1600px] mx-auto space-y-10 animate-in fade-in duration-700 print:p-0">
        
        {/* Header Section */}
        <header className="flex flex-col lg:flex-row justify-between items-start gap-8 border-b border-gray-800/50 pb-12 print:border-gray-200">
          <div className="space-y-6 flex-1">
            <div className="flex items-center gap-4">
              <span className="px-4 py-1.5 bg-indigo-600/10 text-indigo-400 text-[10px] font-black uppercase tracking-[0.2em] rounded-lg border border-indigo-500/20 print:border-gray-300 print:text-indigo-700">
                AI Deep Analysis Report
              </span>
              <span className="text-gray-600 text-xs font-mono tracking-widest">#{(analysis.id || '076681').padStart(6, '0')}</span>
            </div>
            <h1 className="text-4xl lg:text-5xl font-black tracking-tight text-white leading-tight print:text-black">
              {analysis.title}
            </h1>
            <p className="text-gray-400 text-base max-w-4xl leading-relaxed font-medium print:text-gray-700">
              根据多模态模型识别，该视频采用 <span className="text-indigo-400 font-bold italic print:text-indigo-700">{analysis.editingStyle.pacing}</span> 型叙事：{analysis.narrativeStructure}
            </p>
            
            <div className="flex items-center gap-4 print:hidden">
              <button 
                onClick={handleExportPDF}
                className="group flex items-center gap-2 px-6 py-3 bg-gray-900 border border-gray-800 rounded-2xl text-xs font-black uppercase tracking-widest hover:bg-gray-800 hover:border-indigo-500/50 transition-all text-indigo-400 shadow-xl"
              >
                <FileDown size={16} className="group-hover:-translate-y-0.5 transition-transform" /> 导出分析报告
              </button>
              <button 
                onClick={handleShare}
                className={`relative p-3 bg-gray-900 border border-gray-800 rounded-2xl text-gray-500 hover:text-white transition-all hover:border-indigo-500/50 shadow-xl ${shareSuccess ? 'text-green-400 border-green-500/50' : ''}`}
              >
                {shareSuccess ? <Check size={18} /> : <Share2 size={18} />}
                {shareSuccess && (
                  <span className="absolute -top-10 left-1/2 -translate-x-1/2 bg-green-500 text-white text-[10px] font-black px-2 py-1 rounded-lg animate-in fade-in slide-in-from-bottom-2">
                    已复制
                  </span>
                )}
              </button>
            </div>
          </div>

          <div className="flex gap-10 items-center bg-gray-900/30 p-8 rounded-[3rem] border border-gray-800/50 shadow-2xl backdrop-blur-xl group print:bg-gray-50 print:border-gray-200">
            <div className="relative w-32 h-32 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={hookScoreData}
                    innerRadius={45}
                    outerRadius={55}
                    paddingAngle={0}
                    dataKey="value"
                    startAngle={90}
                    endAngle={-270}
                    stroke="none"
                  >
                    <Cell fill="#6366f1" />
                    <Cell fill={window.matchMedia('(prefers-color-scheme: light)').matches ? '#e5e7eb' : '#1f2937'} />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                 <p className="text-2xl font-black text-white group-hover:scale-110 transition-transform print:text-black">{(analysis.hookScore / 10).toFixed(1)}</p>
                 <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest">Hook Score</p>
              </div>
            </div>
            <div className="space-y-2">
               <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Viral Potential</p>
               <h2 className="text-4xl font-black text-green-400 tracking-tighter shadow-green-500/20 print:text-green-600">HIGH</h2>
            </div>
          </div>
        </header>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          
          {/* Left Column (4 cols) */}
          <div className="lg:col-span-4 space-y-10">
            {/* Radar Analysis */}
            <section className="bg-gray-900/20 p-8 rounded-[2.5rem] border border-gray-800/50 space-y-8 shadow-xl relative overflow-hidden group print:bg-white print:border-gray-200">
               <div className="flex items-center justify-between relative z-10">
                  <h3 className="font-black text-sm uppercase tracking-[0.2em] text-white flex items-center gap-3 print:text-black">
                    <TrendingUp className="w-5 h-5 text-indigo-400" />
                    六维性能评估
                  </h3>
               </div>
               <div ref={radarRef} className="h-80 w-full relative z-10">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={analysis.radarData}>
                      <PolarGrid stroke="#1f2937" strokeDasharray="3 3" />
                      <PolarAngleAxis 
                        dataKey="subject" 
                        tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: '900' }} 
                      />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                      <Radar 
                        name="Performance" 
                        dataKey="value" 
                        stroke="#6366f1" 
                        strokeWidth={3} 
                        fill="#6366f1" 
                        fillOpacity={0.25} 
                        dot={{ r: 4, fill: '#6366f1', strokeWidth: 2, stroke: '#fff' }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
               </div>
               <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-600/5 blur-3xl rounded-full print:hidden" />
            </section>

            {/* Viral Genes Card */}
            <section className="bg-gray-900/20 p-8 rounded-[2.5rem] border border-gray-800/50 space-y-8 shadow-xl print:bg-white print:border-gray-200">
              <h3 className="flex items-center gap-3 font-black text-sm uppercase tracking-[0.2em] text-white print:text-black">
                <Flame className="w-5 h-5 text-orange-500" />
                爆款基因拆解
              </h3>
              <div className="space-y-8">
                {analysis.viralFactors.map((factor, idx) => (
                  <div key={idx} className="space-y-3 group">
                    <div className="flex justify-between items-end">
                      <span className="text-xs font-black text-gray-400 uppercase tracking-widest group-hover:text-white transition-colors print:text-gray-600">{factor.category}</span>
                      <span className="text-xs font-black text-indigo-400 font-mono italic print:text-indigo-700">{factor.intensity}/10</span>
                    </div>
                    <div className="h-2 w-full bg-gray-950 rounded-full overflow-hidden border border-white/5 print:bg-gray-100">
                      <div className="h-full bg-gradient-to-r from-indigo-600 to-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.4)] transition-all duration-1000 print:shadow-none" style={{ width: `${factor.intensity * 10}%` }} />
                    </div>
                    <p className="text-[10px] text-gray-500 font-medium leading-relaxed italic opacity-80 group-hover:opacity-100 transition-opacity print:text-gray-700">
                      {factor.description}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* Audience Feedback Tags */}
            <section className="bg-gray-900/20 p-8 rounded-[2.5rem] border border-gray-800/50 space-y-6 shadow-xl print:bg-white print:border-gray-200">
              <h3 className="flex items-center gap-3 font-black text-sm uppercase tracking-[0.2em] text-white print:text-black">
                <MessageSquare className="w-5 h-5 text-purple-400" />
                受众心理反馈
              </h3>
              <div className="space-y-4">
                 <p className="text-xs text-gray-400 font-medium print:text-gray-600">主要情绪: <span className="text-white font-black print:text-black">{analysis.audienceResponse.sentiment}</span></p>
                 <div className="flex flex-wrap gap-2">
                    {analysis.audienceResponse.keyTriggers.map((tag, i) => (
                      <span key={i} className="px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-[10px] font-bold text-indigo-300 print:text-indigo-700 print:bg-indigo-50 print:border-indigo-100">
                        {tag}
                      </span>
                    ))}
                 </div>
              </div>
            </section>
          </div>

          {/* Right Column (8 cols) */}
          <div className="lg:col-span-8 space-y-10">
            {/* Hook Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { icon: Eye, label: '视觉钩子', content: analysis.hookDetails.visual, color: 'text-blue-400', bg: 'bg-blue-400/5', printBg: 'bg-blue-50' },
                { icon: Volume2, label: '音频钩子', content: analysis.hookDetails.audio, color: 'text-purple-400', bg: 'bg-purple-400/5', printBg: 'bg-purple-50' },
                { icon: Type, label: '文案钩子', content: analysis.hookDetails.text, color: 'text-orange-400', bg: 'bg-orange-400/5', printBg: 'bg-orange-50' },
              ].map((hook, i) => (
                <div key={i} className={`${hook.bg} p-8 rounded-[2.5rem] border border-gray-800/50 flex flex-col gap-5 hover:border-gray-600 hover:scale-[1.02] transition-all print:bg-white print:border-gray-200`}>
                  <div className={`p-3 rounded-2xl bg-gray-950 w-fit ${hook.color} shadow-lg print:bg-gray-100 print:shadow-none`}>
                    <hook.icon size={24} />
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.25em]">{hook.label}</h4>
                    <p className="text-sm text-gray-300 leading-relaxed font-medium print:text-black">{hook.content}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Rhythm Chart Module */}
            <section className="bg-gray-950 p-10 rounded-[3rem] border border-gray-800/50 shadow-2xl space-y-10 relative overflow-hidden group print:bg-white print:border-gray-200 print:shadow-none">
               <div className="flex items-center justify-between relative z-10">
                  <h3 className="font-black text-base uppercase tracking-[0.1em] flex flex-col sm:flex-row sm:items-center gap-3 print:text-black">
                    剪辑节奏与信息密度热力图
                    <div className="flex gap-4 ml-0 sm:ml-8">
                       <span className="flex items-center gap-2 text-[10px] text-gray-500 font-black uppercase tracking-widest print:text-gray-600">
                         <div className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> 有效信息量
                       </span>
                       <span className="flex items-center gap-2 text-[10px] text-gray-500 font-black uppercase tracking-widest print:text-gray-600">
                         <div className="w-2.5 h-2.5 rounded-full bg-orange-500" /> 节奏卡点
                       </span>
                    </div>
                  </h3>
               </div>
               
               <div ref={rhythmRef} className="h-[400px] w-full relative z-10">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={analysis.rhythmData}>
                      <defs>
                        <linearGradient id="rhythmGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f2937" opacity={0.3} />
                      <XAxis dataKey="time" hide />
                      <YAxis hide domain={[0, 100]} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#0d111d', 
                          border: '1px solid #374151', 
                          borderRadius: '16px', 
                          fontSize: '11px',
                          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
                        }}
                        itemStyle={{ color: '#818cf8', fontWeight: 'bold' }}
                        labelStyle={{ color: '#6b7280', fontSize: '9px' }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="intensity" 
                        stroke="#6366f1" 
                        strokeWidth={4} 
                        fill="url(#rhythmGradient)" 
                        animationDuration={1500}
                        activeDot={{ r: 8, fill: '#fff', stroke: '#6366f1', strokeWidth: 3 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                  
                  {/* Chart Annotations */}
                  <div className="absolute bottom-4 left-4 right-4 flex justify-between px-10 text-[9px] font-black text-gray-700 uppercase tracking-[0.4em] print:text-gray-400">
                     <span className="bg-gray-900/50 px-3 py-1 rounded-full border border-white/5 print:bg-gray-100 print:border-gray-200">Intro Hook</span>
                     <span className="bg-gray-900/50 px-3 py-1 rounded-full border border-white/5 print:bg-gray-100 print:border-gray-200">Climax / Pivot</span>
                     <span className="bg-gray-900/50 px-3 py-1 rounded-full border border-white/5 print:bg-gray-100 print:border-gray-200">CTA / Engagement</span>
                  </div>
               </div>
               <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(99,102,241,0.03),transparent)] pointer-events-none print:hidden" />
            </section>

            {/* Bottom Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
               {/* Style Analysis Card */}
               <section className="bg-gray-900/20 p-8 rounded-[2.5rem] border border-gray-800/50 space-y-8 print:bg-white print:border-gray-200">
                  <h3 className="flex items-center gap-3 font-black text-sm uppercase tracking-[0.2em] text-white print:text-black">
                    <Scissors className="w-5 h-5 text-indigo-400" />
                    剪辑手法分析
                  </h3>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                       <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">转场类型</p>
                       <p className="text-sm font-bold text-gray-200 bg-gray-900/50 p-2 rounded-xl border border-white/5 print:text-black print:bg-gray-50">{analysis.editingStyle.transitionType}</p>
                    </div>
                    <div className="space-y-2">
                       <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">剪辑节奏</p>
                       <p className="text-sm font-bold text-gray-200 bg-gray-900/50 p-2 rounded-xl border border-white/5 print:text-black print:bg-gray-50">{analysis.editingStyle.pacing}</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">配色方案建议</p>
                    <div className="flex items-center gap-3">
                       <div className="flex-1 h-3 rounded-full bg-gradient-to-r from-orange-500 via-yellow-400 to-indigo-600 shadow-inner" />
                       <span className="text-[10px] text-gray-400 font-mono italic font-bold print:text-gray-600">{analysis.editingStyle.colorPalette}</span>
                    </div>
                  </div>
               </section>

               {/* CTA Creator Card */}
               <section className="bg-gradient-to-br from-indigo-600 to-purple-700 p-10 rounded-[3rem] shadow-2xl shadow-indigo-600/20 flex flex-col justify-between relative overflow-hidden group print:bg-indigo-50 print:from-white print:to-white print:shadow-none print:border-gray-200 print:border">
                  <div className="absolute top-0 right-0 p-10 opacity-10 group-hover:scale-125 transition-transform duration-1000 print:hidden">
                    <Zap size={120} />
                  </div>
                  <div className="relative z-10 space-y-4">
                    <h3 className="text-3xl font-black text-white leading-tight print:text-black">
                      基于拆解结果<br/>生成二次创作脚本
                    </h3>
                    <p className="text-indigo-100 text-sm font-medium opacity-80 print:text-indigo-900">
                      已自动匹配 <span className="font-black text-white underline decoration-2 underline-offset-4 print:text-indigo-700">AIDA 营销模型</span>，完美复刻该爆款的叙事路径。
                    </p>
                  </div>
                  <div className="relative z-10 flex gap-4 mt-8 print:hidden">
                    <button 
                      onClick={() => window.dispatchEvent(new CustomEvent('changeSection', { detail: AppSection.Editor }))}
                      className="flex-1 py-4 bg-white text-gray-950 font-black rounded-2xl text-xs uppercase tracking-widest hover:scale-105 active:scale-95 transition-all flex items-center justify-center gap-3 shadow-2xl"
                    >
                      立即生成脚本 <ArrowRight size={16} />
                    </button>
                    <button 
                      onClick={handleShare}
                      className="p-4 bg-indigo-500/30 backdrop-blur-md border border-white/20 text-white rounded-2xl hover:bg-indigo-500/50 transition-all shadow-xl"
                    >
                      <Share2 size={18} />
                    </button>
                  </div>
               </section>
            </div>
          </div>
        </div>
      </div>
      
      <style>{`
        @media print {
          body { background: white !important; color: black !important; }
          .print\\:hidden, aside, nav, button { display: none !important; }
          main { width: 100% !important; margin: 0 !important; }
          .max-w-[1600px] { max-width: 100% !important; }
          .bg-gray-900\\/20, .bg-gray-900\\/30, .bg-gray-950, .glass { background: #fdfdfd !important; border: 1px solid #e5e7eb !important; color: #111827 !important; }
          .text-white, h1, h2, h3, h4 { color: #111827 !important; }
          .text-gray-400, .text-gray-500, .text-indigo-100 { color: #4b5563 !important; }
          .text-indigo-400 { color: #4f46e5 !important; }
          .border-gray-800, .border-indigo-500\\/20 { border-color: #e5e7eb !important; }
          svg text { fill: #111827 !important; }
          .shadow-xl, .shadow-2xl, .shadow-indigo-600\\/20 { box-shadow: none !important; }
          .rounded-[3rem], .rounded-[2.5rem] { border-radius: 1rem !important; }
          .h-full { height: auto !important; overflow: visible !important; }
          .scrollbar-thin { overflow: visible !important; }
          canvas { max-width: 100% !important; height: auto !important; }
        }
      `}</style>
    </div>
  );
};

export default AnalysisPanel;
