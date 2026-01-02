
import React, { useState, useEffect } from 'react';
import { AppSection, VideoAnalysis, Shot, CreationStrategy, TargetPlatform, ProjectSummary } from './types';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import AnalysisPanel from './components/AnalysisPanel';
import Editor from './components/Editor';
import KnowledgeBase from './components/KnowledgeBase';
import Settings from './components/Settings';
import Login from './components/Login';
import VideoSlideshow from './components/VideoSlideshow';
import Discovery from './components/Discovery';
import ShotAnalysis from './components/ShotAnalysis';
import { analyzeVideoConcept, generateCreativeScript } from './services/geminiService';
import { createAnalysis, pollAnalysisResult, uploadVideo } from './services/analysisService';
import { isApiError } from './services/api';
import { AlertCircle, X } from 'lucide-react';
import { ConsoleView } from './components/phone_ai/ConsoleView';
import { MobileView } from './components/phone_ai/MobileView';
import { CameraDebug } from './components/phone_ai/CameraDebug';
import { ShootingAdvisorView } from './components/phone_ai/ShootingAdvisorView';
import { ShootingConsoleView } from './components/phone_ai/ShootingConsoleView';

const RubikIcon = ({ className = "w-8 h-8" }) => (
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

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeSection, setActiveSection] = useState<AppSection>(AppSection.Dashboard);
  const [loading, setLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorToast, setErrorToast] = useState<{ message: string, type: 'error' | 'warning' } | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState({
    status: '',
    progress: 0,
    currentStep: '',
  });

  const [analysis, setAnalysis] = useState<VideoAnalysis | null>(null);
  const [shots, setShots] = useState<Shot[]>([]);

  // Mobile/Standalone View State
  const [mobileViewState, setMobileViewState] = useState<{
    type: 'mobile' | 'shooting-advisor' | 'console' | 'debug';
    sessionId?: string;
  } | null>(null);

  useEffect(() => {
    // Check for Deep Links (Hash Routing for mobile/standalone views)
    const checkHash = () => {
      const hash = window.location.hash;

      if (hash.startsWith('#/shooting-advisor/')) {
        const id = hash.split('/')[2];
        if (id) setMobileViewState({ type: 'shooting-advisor', sessionId: id });
      } else if (hash.startsWith('#/shooting-mobile/')) {
        const id = hash.split('/')[2];
        if (id) setMobileViewState({ type: 'shooting-advisor', sessionId: id });
      } else if (hash.startsWith('#/mobile/')) {
        const id = hash.split('/')[2];
        if (id) setMobileViewState({ type: 'mobile', sessionId: id });
      } else if (hash.startsWith('#/console/')) {
        const id = hash.split('/')[2];
        if (id && id !== 'new') setMobileViewState({ type: 'console', sessionId: id });
      } else if (hash.startsWith('#/shooting-console/')) {
        // If we want shooting console to be full screen standalone
        const id = hash.split('/')[2];
        if (id) setMobileViewState({ type: 'console', sessionId: id });
      } else if (hash === '#/debug') {
        setMobileViewState({ type: 'debug' });
      }
    };

    checkHash();
    window.addEventListener('hashchange', checkHash);
    return () => window.removeEventListener('hashchange', checkHash);
  }, []);

  useEffect(() => {
    const savedLogin = localStorage.getItem('rubik_auth');
    if (savedLogin === 'true') {
      setIsLoggedIn(true);
    }
  }, []);

  useEffect(() => {
    if (errorToast) {
      const timer = setTimeout(() => setErrorToast(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [errorToast]);

  useEffect(() => {
    const handleSectionChange = (e: any) => {
      if (e.detail) {
        setActiveSection(e.detail);
      }
    };
    window.addEventListener('changeSection', handleSectionChange);
    return () => window.removeEventListener('changeSection', handleSectionChange);
  }, []);

  const handleLoginSuccess = () => {
    localStorage.setItem('rubik_auth', 'true');
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('rubik_auth');
    setIsLoggedIn(false);
  };

  const generateDefaultShots = (title: string): Shot[] => {
    return [
      { id: Date.now() + 1, startTime: 0, duration: 3, type: "黄金钩子", description: "近景特写，主体表情夸张，背景通过模糊处理突出人物。", dialogue: `如果你还不知道${title}的秘密，一定要看完这30秒！`, transition: "硬切", platformSpecific: { platform: 'douyin', tip: '前3秒必须抓住用户眼球' } },
      { id: Date.now() + 2, startTime: 3, duration: 5, type: "痛点代入", description: "全景展示杂乱的现状，色调偏冷。", dialogue: "为什么你的视频点赞总是不过百？逻辑其实很简单。", transition: "叠化" },
      { id: Date.now() + 3, startTime: 8, duration: 8, type: "干货输出", description: "分屏显示，左侧操作演示，右侧文字贴纸。", dialogue: "第一步是拆解基因，第二步是重构脚本。", transition: "平移" },
      { id: Date.now() + 4, startTime: 16, duration: 4, type: "行动引导", description: "博主指着左下角组件，弹出动态关注特效。", dialogue: "点个关注，下期教你实操！", transition: "缩放" }
    ];
  };

  const handleStartAnalysis = async (url: string) => {
    if (!url.trim()) {
      setErrorToast({ message: '请输入视频链接', type: 'error' });
      return;
    }

    await startAnalysis(url);
  };

  const handleStartFileAnalysis = async (file: File) => {
    setLoading(true);
    setErrorToast(null);
    setAnalysisProgress({ status: '', progress: 0, currentStep: '正在上传视频文件...' });

    try {
      // 1. 先上传文件
      console.log('开始上传文件:', file.name, '大小:', (file.size / 1024 / 1024).toFixed(2), 'MB');
      const uploadResult = await uploadVideo(file);
      console.log('✅ 视频上传成功，返回结果:', uploadResult);
      console.log('返回的 filePath:', uploadResult.filePath);

      // 验证返回的路径格式
      if (!uploadResult.filePath) {
        throw new Error('上传接口未返回 filePath');
      }

      // 2. 使用上传后的路径进行分析
      console.log('开始创建分析任务，使用路径:', uploadResult.filePath);
      await startAnalysis(uploadResult.filePath);
    } catch (error: any) {
      console.error('❌ 文件上传/分析失败:', error);
      console.error('错误详情:', {
        message: error.message,
        code: error.code,
        response: error.response?.data
      });

      setLoading(false);
      setAnalysisProgress({ status: '', progress: 0, currentStep: '' });

      if (isApiError(error)) {
        if (error.code === 'FILE_TOO_LARGE') {
          setErrorToast({
            message: '文件过大，请上传小于 500MB 的视频',
            type: 'error'
          });
        } else if (error.code === 'UNSUPPORTED_FORMAT') {
          setErrorToast({
            message: '不支持的文件格式',
            type: 'error'
          });
        } else if (error.message?.includes('上传接口未返回')) {
          setErrorToast({
            message: '后端上传接口返回数据格式错误，请检查后端实现',
            type: 'error'
          });
        } else {
          setErrorToast({
            message: error.message || '上传失败，请稍后重试',
            type: 'error'
          });
        }
      } else {
        setErrorToast({
          message: error.message || '网络连接失败，请检查网络',
          type: 'error'
        });
      }
    }
  };

  const startAnalysis = async (url: string) => {
    setLoading(true);
    setErrorToast(null);
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
      if (result && result.title) {
        setShots(generateDefaultShots(result.title));
      } else {
        console.warn('分析结果缺少 title 字段:', result);
        setShots(generateDefaultShots('未命名视频'));
      }

      // 5. 跳转到分析页面
      setActiveSection(AppSection.Analysis);

      console.log('分析完成:', result);
    } catch (error: any) {
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
        } else if (error.code === 'ANALYSIS_FAILED') {
          setErrorToast({
            message: '视频分析失败，请稍后重试',
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

  const handleViewDetails = (project: ProjectSummary) => {
    setLoading(true);
    setTimeout(() => {
      const mockRhythm = Array.from({ length: 30 }, (_, i) => ({
        time: i,
        intensity: i < 3 ? 80 + Math.random() * 20 : 20 + Math.random() * 70
      }));

      const radarData = project.radarData || [
        { subject: '钩子强度', value: 85, fullMark: 100 },
        { subject: '情绪张力', value: 70, fullMark: 100 },
        { subject: '视觉冲击', value: 90, fullMark: 100 },
        { subject: '叙事逻辑', value: 65, fullMark: 100 },
        { subject: '转化潜力', value: 80, fullMark: 100 },
        { subject: '创新指数', value: 75, fullMark: 100 }
      ];

      setAnalysis({
        id: project.id, title: project.title, coverUrl: project.thumbnail, duration: 52,
        viralFactors: [
          { category: "视觉钩子", description: "前3秒高饱和度画面切换", intensity: 9 },
          { category: "音频卡点", description: "节奏感极强的BGM配合", intensity: 8 }
        ],
        rhythmData: mockRhythm, radarData: radarData, hookScore: project.score,
        evaluationReport: { starRating: 5, coreStrengths: ["节奏感强", "视觉冲击力大"], reusablePoints: ["3秒黄金钩子", "结尾反转话术"] },
        hookDetails: { visual: "黑白变彩色瞬间", audio: "心跳音效", text: "你绝对想不到..." },
        editingStyle: { pacing: "极速", transitionType: "遮罩转场", colorPalette: "赛博朋克" },
        audienceResponse: { sentiment: "极度兴奋", keyTriggers: ["猎奇", "认同"] },
        narrativeStructure: "经典的 AIDA 营销结构"
      } as VideoAnalysis);

      setShots(generateDefaultShots(project.title));
      setActiveSection(AppSection.Analysis);
      setLoading(false);
    }, 600);
  };

  const handleGenerateScript = async (strategy: CreationStrategy, platform: TargetPlatform) => {
    if (!analysis || isGenerating) return;
    setIsGenerating(true);
    setErrorToast(null);
    try {
      const newShots = await generateCreativeScript(analysis.title, strategy, platform);
      setShots(newShots);
    } catch (err: any) {
      console.error("生成失败", err);
      if (err.message?.includes('429')) {
        setErrorToast({ message: "API 配额已耗尽，已为您保留默认分镜数据。建议稍后重试。", type: 'warning' });
      } else {
        setErrorToast({ message: "跨平台脚本重构失败，建议重新发起请求。", type: 'error' });
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const renderSection = () => {
    switch (activeSection) {
      case AppSection.Dashboard:
        return <Dashboard onStartAnalysis={handleStartAnalysis} onStartFileAnalysis={handleStartFileAnalysis} onViewDetails={handleViewDetails} />;
      case AppSection.Analysis:
        return <AnalysisPanel analysis={analysis} />;
      case AppSection.VideoSlideshow:
        return <VideoSlideshow />;
      case AppSection.Discovery:
        return <Discovery />;
      case AppSection.ShotAnalysis:
        return <ShotAnalysis />;
      case AppSection.Editor:
        return <Editor initialShots={shots} onGenerate={handleGenerateScript} isGenerating={isGenerating} />;
      case AppSection.KnowledgeBase:
        return <KnowledgeBase />;
      case AppSection.Settings:
        return <Settings onLogout={handleLogout} />;
      case AppSection.ShootingAssistant:
        return <ShootingConsoleView initialSessionId={null} />;
      default:
        return <Dashboard onStartAnalysis={handleStartAnalysis} onViewDetails={handleViewDetails} />;
    }
  };

  if (!isLoggedIn && !mobileViewState) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // Render Standalone Mobile/Debug Views
  if (mobileViewState) {
    if (mobileViewState.type === 'debug') return <CameraDebug />;
    if (mobileViewState.type === 'mobile' && mobileViewState.sessionId) return <MobileView sessionId={mobileViewState.sessionId} />;
    if (mobileViewState.type === 'shooting-advisor' && mobileViewState.sessionId) return <ShootingAdvisorView sessionId={mobileViewState.sessionId} />;
    if (mobileViewState.type === 'console' && mobileViewState.sessionId) return <ShootingConsoleView initialSessionId={mobileViewState.sessionId} />;
  }

  return (
    <div className="flex h-screen bg-[#05070a] overflow-hidden text-gray-100 font-sans relative">
      <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />

      <main className="flex-1 relative overflow-hidden bg-[#05070a]">
        {/* Global Toast */}
        {errorToast && (
          <div className="fixed top-8 left-1/2 -translate-x-1/2 z-[100] animate-in slide-in-from-top-4 duration-300">
            <div className={`flex items-center gap-4 px-6 py-4 rounded-2xl border backdrop-blur-xl shadow-2xl ${errorToast.type === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-400' : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
              }`}>
              <AlertCircle size={20} />
              <p className="text-sm font-bold">{errorToast.message}</p>
              <button onClick={() => setErrorToast(null)} className="ml-2 p-1 hover:bg-white/10 rounded-lg">
                <X size={16} />
              </button>
            </div>
          </div>
        )}

        {loading && (
          <div className="absolute inset-0 z-[60] bg-black/90 backdrop-blur-xl flex flex-col items-center justify-center space-y-8 animate-in fade-in duration-300">
            <div className="relative">
              <div className="w-20 h-20 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
              <RubikIcon className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-indigo-400 w-8 h-8 animate-pulse" />
            </div>
            <div className="text-center space-y-4">
              <h3 className="text-2xl font-black italic text-white uppercase tracking-widest">
                {analysisProgress.currentStep || 'Analysis Active'}
              </h3>
              {analysisProgress.progress > 0 && (
                <>
                  <div className="w-80 bg-gray-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-indigo-500 h-full transition-all duration-300"
                      style={{ width: `${analysisProgress.progress}%` }}
                    />
                  </div>
                  <p className="text-indigo-400 text-sm font-bold">{analysisProgress.progress}% 完成</p>
                </>
              )}
            </div>
          </div>
        )}

        <div className="h-full overflow-hidden">
          {renderSection()}
        </div>
      </main>
    </div>
  );
};

export default App;
