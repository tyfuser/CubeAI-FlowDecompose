
import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, Flame, Star, MessageSquare, Play, Sparkles, 
  Send, X, Mic, Image as ImageIcon, Video, Zap, 
  ChevronRight, ArrowRight, TrendingUp, History, 
  Compass, Bot, User, Share2, MoreHorizontal
} from 'lucide-react';
import { ChatMessage } from '../types';
import { GoogleGenAI } from "@google/genai";

const Discovery: React.FC = () => {
  const [selectedVideo, setSelectedVideo] = useState<any>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const viralCases = [
    { 
      id: 'v1', 
      title: '2024 夏季穿搭：冷淡风极致表达', 
      cover: 'https://picsum.photos/seed/fashion_v1/400/711', 
      views: '2.4M', 
      score: 96, 
      tags: ['时尚', '穿搭', '冷淡风'],
      transcript: '大家好，今天教大家如何用简单的白色单品搭出高级感...'
    },
    { 
      id: 'v2', 
      title: '沉浸式整理：拯救强迫症的3分钟', 
      cover: 'https://picsum.photos/seed/asmr_v1/400/711', 
      views: '1.8M', 
      score: 92, 
      tags: ['生活', 'ASMR', '沉浸式'],
      transcript: '[音效：清脆的塑料声] 第一步，清空所有杂物...'
    },
    { 
      id: 'v3', 
      title: '数码测评：Gemini 3 Pro 实测表现', 
      cover: 'https://picsum.photos/seed/tech_v1/400/711', 
      views: '3.1M', 
      score: 98, 
      tags: ['科技', '测评', 'AI'],
      transcript: '目前的 AI 市场上，模型能力突飞猛进，但真正的生产力...'
    },
    { 
      id: 'v4', 
      title: '探店报告：杭州最值得去的创意餐厅', 
      cover: 'https://picsum.photos/seed/food_v1/400/711', 
      views: '950K', 
      score: 88, 
      tags: ['探店', '美食', '旅游'],
      transcript: '这家隐藏在西湖边的小店，竟然主打创意融合菜...'
    }
  ];

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    // 模拟 AI 思考和多模态分析
    setTimeout(async () => {
      try {
        // Fix: Properly initialize Gemini client and call generateContent
        const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
        const response = await ai.models.generateContent({
          model: 'gemini-3-flash-preview',
          contents: `你是一个短视频运营专家。用户正在观看视频《${selectedVideo.title}》，并提问：${userMsg.content}。
          视频关键信息：标签：${selectedVideo.tags.join(', ')}。脚本摘要：${selectedVideo.transcript}。
          请以专业且口语化的方式回答用户，帮助他们理解该视频的爆款逻辑或技术细节。`,
          config: {
             systemInstruction: "你语气专业、前卫，像一个顶级的短视频导演。"
          }
        });

        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          // Fix: Access .text property directly from response
          content: response.text || '分析出错，请稍后再试。',
          timestamp: Date.now(),
          attachments: Math.random() > 0.5 ? [
            { type: 'frame', url: `https://picsum.photos/seed/${selectedVideo.id}_frame/400/225`, videoTimestamp: '00:12' }
          ] : undefined
        };

        setMessages(prev => [...prev, assistantMsg]);
      } catch (e) {
        console.error(e);
      } finally {
        setIsTyping(false);
      }
    }, 1200);
  };

  const openChat = (video: any) => {
    setSelectedVideo(video);
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `你好！我是你的 AI 创作助手。关于《${video.title}》这个视频，你可以问我任何问题，比如：“前3秒的视觉冲击是怎么营造的？”或者“它的文案逻辑是什么？”`,
        timestamp: Date.now()
      }
    ]);
  };

  return (
    <div className="h-full flex flex-col bg-[#05070a] overflow-hidden relative">
      {/* Background patterns */}
      <div className="absolute inset-0 opacity-[0.02] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]" />
      
      {/* Header */}
      <header className="p-8 border-b border-gray-800/50 bg-gray-950/20 backdrop-blur-xl flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
        <div>
          <h2 className="text-3xl font-black tracking-tight flex items-center gap-3">
            案例探索中心 <Compass className="text-indigo-500 animate-spin-slow" />
          </h2>
          <p className="text-gray-500 text-sm mt-1 font-medium italic">Discover & Interact - 与爆款视频实时对话</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-indigo-400 transition-colors" size={18} />
            <input 
              type="text" 
              placeholder="搜索热门案例、标签..." 
              className="bg-gray-900 border border-gray-800 rounded-2xl pl-12 pr-6 py-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none w-full md:w-80 transition-all"
            />
          </div>
        </div>
      </header>

      {/* Content Grid */}
      <div className="flex-1 overflow-y-auto p-8 scrollbar-thin relative z-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {viralCases.map((video) => (
            <div 
              key={video.id} 
              className="group bg-gray-900/30 border border-gray-800 hover:border-indigo-500/50 rounded-[2.5rem] overflow-hidden transition-all shadow-xl hover:shadow-indigo-500/10 flex flex-col"
            >
              <div className="aspect-[9/16] bg-gray-950 relative overflow-hidden">
                <img src={video.cover} className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-all duration-700 group-hover:scale-110" alt={video.title} />
                <div className="absolute inset-0 bg-gradient-to-t from-[#05070a] via-transparent to-transparent opacity-90" />
                
                <div className="absolute top-6 left-6 flex flex-col gap-2">
                   <span className="flex items-center gap-1.5 px-3 py-1 bg-indigo-600 rounded-full text-[10px] font-black text-white shadow-xl">
                     <TrendingUp size={12} /> {video.score} 分
                   </span>
                </div>

                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
                  <button 
                    onClick={() => openChat(video)}
                    className="p-5 bg-white text-gray-950 rounded-full shadow-2xl scale-90 group-hover:scale-100 transition-all hover:bg-indigo-500 hover:text-white"
                  >
                    <MessageSquare size={24} fill="currentColor" />
                  </button>
                </div>

                <div className="absolute bottom-6 left-6 right-6 space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {video.tags.map(tag => (
                      <span key={tag} className="px-2 py-0.5 bg-gray-900/80 backdrop-blur border border-white/5 rounded text-[8px] font-black text-gray-400 uppercase">#{tag}</span>
                    ))}
                  </div>
                  <h3 className="text-sm font-black text-white leading-tight line-clamp-2">{video.title}</h3>
                </div>
              </div>
              <div className="p-6 border-t border-gray-800/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Play size={14} className="text-gray-500" />
                  <span className="text-[10px] font-black text-gray-400">{video.views} 播放</span>
                </div>
                <button 
                  onClick={() => openChat(video)}
                  className="text-[10px] font-black text-indigo-400 uppercase tracking-widest hover:text-white transition-colors flex items-center gap-1"
                >
                  开始对话 <ArrowRight size={12} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Chat Drawer Overlay */}
      {selectedVideo && (
        <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-8">
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300"
            onClick={() => setSelectedVideo(null)}
          />
          <div className="relative w-full max-w-6xl h-full sm:h-[85vh] bg-[#0d111d] border border-white/10 sm:rounded-[3rem] shadow-2xl flex flex-col lg:flex-row overflow-hidden animate-in slide-in-from-bottom duration-500">
             {/* Left: Video Player Area */}
             <div className="flex-1 bg-black relative flex items-center justify-center">
                <img src={selectedVideo.cover} className="w-full h-full object-cover opacity-50" />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                   <div className="w-20 h-20 bg-indigo-600 rounded-full flex items-center justify-center text-white shadow-2xl cursor-pointer hover:scale-110 transition-all">
                      <Play size={32} fill="white" className="ml-1" />
                   </div>
                </div>
                <div className="absolute bottom-8 left-8 right-8">
                   <div className="flex items-center gap-4 mb-4">
                      <span className="px-3 py-1 bg-white/10 backdrop-blur rounded-lg text-[10px] font-black text-white">CASE: {selectedVideo.id.toUpperCase()}</span>
                      <h3 className="text-xl font-black text-white">{selectedVideo.title}</h3>
                   </div>
                   <div className="h-1 w-full bg-white/20 rounded-full overflow-hidden">
                      <div className="bg-indigo-500 h-full w-[35%] shadow-[0_0_15px_rgba(99,102,241,1)]" />
                   </div>
                </div>
                <button 
                  onClick={() => setSelectedVideo(null)}
                  className="absolute top-8 left-8 p-3 bg-black/40 hover:bg-black/60 rounded-2xl text-white transition-all border border-white/10 lg:hidden"
                >
                  <X size={20} />
                </button>
             </div>

             {/* Right: AI Chat Interface */}
             <div className="w-full lg:w-[450px] bg-[#0d111d] border-l border-white/5 flex flex-col">
                <header className="p-6 border-b border-white/5 flex items-center justify-between">
                   <div className="flex items-center gap-4">
                      <div className="relative">
                        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg">
                           <Bot size={20} />
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-[#0d111d] rounded-full animate-pulse" />
                      </div>
                      <div>
                        <h4 className="text-sm font-black text-white">AI 创作导师</h4>
                        <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest italic">Video Context Aware</p>
                      </div>
                   </div>
                   <div className="flex items-center gap-2">
                      <button className="p-2 text-gray-500 hover:text-white"><Share2 size={16} /></button>
                      <button onClick={() => setSelectedVideo(null)} className="p-2 text-gray-500 hover:text-white hidden lg:block"><X size={20}/></button>
                   </div>
                </header>

                <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin">
                   {messages.map((msg) => (
                     <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] space-y-3 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                           <div className={`p-5 rounded-[2rem] text-sm leading-relaxed ${
                             msg.role === 'user' 
                               ? 'bg-indigo-600 text-white rounded-tr-none' 
                               : 'bg-gray-800/50 text-gray-300 rounded-tl-none border border-white/5'
                           }`}>
                             {msg.content}
                           </div>
                           {msg.attachments?.map((att, i) => (
                             <div key={i} className="bg-gray-900 rounded-2xl border border-white/10 overflow-hidden space-y-2 p-2 group">
                                <div className="relative aspect-video rounded-xl overflow-hidden">
                                   <img src={att.url} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                                   <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/60 rounded text-[9px] font-mono text-white">分析点: {att.videoTimestamp}</div>
                                </div>
                                <p className="px-2 pb-1 text-[10px] text-gray-500 font-black uppercase italic tracking-widest flex items-center gap-2">
                                  <Zap size={10} className="text-indigo-400" /> 视觉语义自动解析中...
                                </p>
                             </div>
                           ))}
                           <p className="text-[9px] text-gray-600 font-bold uppercase mx-4">{new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                        </div>
                     </div>
                   ))}
                   {isTyping && (
                     <div className="flex justify-start">
                        <div className="bg-gray-800/50 p-4 rounded-[2rem] rounded-tl-none border border-white/5 flex gap-1 items-center">
                           <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                           <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                           <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                     </div>
                   )}
                   <div ref={chatEndRef} />
                </div>

                <div className="p-6 border-t border-white/5 bg-gray-950/40">
                   <div className="flex gap-2 mb-4 overflow-x-auto no-scrollbar pb-1">
                      {['分析钩子', '叙事逻辑', '爆款基因', '转场学习'].map(hint => (
                        <button 
                          key={hint}
                          onClick={() => setInputValue(prev => prev + (prev ? ' ' : '') + `请帮我分析一下这个视频的${hint}。`)}
                          className="px-4 py-1.5 bg-gray-900 hover:bg-indigo-600/20 hover:text-indigo-400 border border-white/5 rounded-full text-[10px] font-black text-gray-500 whitespace-nowrap transition-all"
                        >
                          #{hint}
                        </button>
                      ))}
                   </div>
                   <div className="relative group">
                      <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                         <button className="p-2 text-gray-600 hover:text-indigo-400 transition-colors"><Mic size={18}/></button>
                         <div className="h-4 w-[1px] bg-gray-800" />
                      </div>
                      <textarea 
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSendMessage())}
                        placeholder="与视频对话..."
                        className="w-full bg-[#111827] border border-white/5 rounded-[1.8rem] pl-16 pr-14 py-4 text-sm focus:ring-2 focus:ring-indigo-500 outline-none resize-none h-14 scrollbar-none"
                      />
                      <button 
                        onClick={handleSendMessage}
                        className={`absolute right-4 top-1/2 -translate-y-1/2 p-2.5 rounded-xl transition-all ${inputValue.trim() ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-700'}`}
                      >
                        <Send size={18} />
                      </button>
                   </div>
                </div>
             </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 12s linear infinite;
        }
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
};

export default Discovery;
