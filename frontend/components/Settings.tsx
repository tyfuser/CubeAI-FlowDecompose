import React, { useState, useEffect } from 'react';
import { 
  User, Cpu, Globe, HardDrive, ShieldCheck, 
  Bell, Palette, Languages, Zap, ExternalLink,
  CheckCircle2, AlertCircle, RefreshCw, LogOut,
  Moon, Sun, Layout, Eye, MessageSquare, Volume2,
  Mail, BellRing, Settings2, Smartphone, Share2, Cloud,
  BarChart3, FileText, Check, Monitor, Key, Shield, ChevronRight
} from 'lucide-react';

type SettingsTab = 'profile' | 'ai' | 'platforms' | 'storage' | 'theme' | 'language' | 'notifications';

interface SettingsProps {
  onLogout?: () => void;
}

// 多语言字典
const translations: Record<string, any> = {
  zh: {
    settings: "系统设置",
    profile: "个人资料",
    ai: "AI 引擎",
    platforms: "平台集成",
    storage: "存储与配额",
    theme: "主题定制",
    language: "语言 / Language",
    notifications: "通知管理",
    save: "保存更改",
    logout: "退出登录",
    core: "核心",
    pref: "偏好"
  },
  en: {
    settings: "System Settings",
    profile: "Profile",
    ai: "AI Engine",
    platforms: "Integrations",
    storage: "Storage",
    theme: "Themes",
    language: "Language",
    notifications: "Notifications",
    save: "Save Changes",
    logout: "Log Out",
    core: "Core",
    pref: "Preferences"
  }
};

const Settings: React.FC<SettingsProps> = ({ onLogout }) => {
  const [hasApiKey, setHasApiKey] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [selectedTheme, setSelectedTheme] = useState('dark');
  const [selectedLanguage, setSelectedLanguage] = useState('zh');
  const [isSaving, setIsSaving] = useState(false);
  const [notifSettings, setNotifSettings] = useState({
    analysisDone: true,
    weeklyReport: false,
    systemAlert: true,
    marketing: false
  });

  const t = (key: string) => (translations[selectedLanguage] && translations[selectedLanguage][key]) || key;

  useEffect(() => {
    checkApiKey();
  }, []);

  // 监听主题变化并应用到文档
  useEffect(() => {
    const root = document.documentElement;
    if (selectedTheme === 'cyberpunk') {
      root.style.setProperty('--primary-glow', 'rgba(168, 85, 247, 0.4)');
      root.style.setProperty('--accent-color', '#a855f7');
    } else if (selectedTheme === 'professional') {
      root.style.setProperty('--primary-glow', 'rgba(75, 85, 99, 0.2)');
      root.style.setProperty('--accent-color', '#9ca3af');
    } else {
      root.style.setProperty('--primary-glow', 'rgba(99, 102, 241, 0.2)');
      root.style.setProperty('--accent-color', '#6366f1');
    }
  }, [selectedTheme]);

  const checkApiKey = async () => {
    const win = window as any;
    if (win.aistudio) {
      const selected = await win.aistudio.hasSelectedApiKey();
      setHasApiKey(selected);
    }
  };

  const handleOpenKeyDialog = async () => {
    const win = window as any;
    if (win.aistudio) {
      await win.aistudio.openSelectKey();
      setHasApiKey(true); 
    }
  };

  const toggleNotif = (key: keyof typeof notifSettings) => {
    setNotifSettings(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => setIsSaving(false), 1500);
  };

  const menuItems = [
    { id: 'profile', label: t('profile'), icon: User },
    { id: 'ai', label: t('ai'), icon: Cpu },
    { id: 'platforms', label: t('platforms'), icon: Globe },
    { id: 'storage', label: t('storage'), icon: HardDrive },
  ];

  const prefItems = [
    { id: 'theme', label: t('theme'), icon: Palette },
    { id: 'language', label: t('language'), icon: Languages },
    { id: 'notifications', label: t('notifications'), icon: Bell },
  ];

  return (
    <div className={`h-full flex flex-col transition-colors duration-500 ${selectedTheme === 'professional' ? 'bg-[#1a1c23]' : selectedTheme === 'cyberpunk' ? 'bg-[#000510]' : 'bg-gray-900'} text-gray-100 overflow-hidden`}>
      <header className="p-8 border-b border-gray-800 bg-gray-950/50 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div>
            <h2 className="text-3xl font-black tracking-tight flex items-center gap-3">
              {t('settings')} <span className="text-gray-600 font-light hidden sm:inline">Settings</span>
            </h2>
            <p className="text-gray-500 text-sm mt-1 font-medium">管理您的创作偏好、账户安全及 AI 引擎配置。</p>
          </div>
          {isSaving && (
            <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 text-green-400 rounded-2xl animate-in fade-in zoom-in duration-300">
              <RefreshCw size={14} className="animate-spin" />
              <span className="text-[10px] font-black uppercase tracking-widest">保存中...</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleSave}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-all font-black text-xs uppercase tracking-widest shadow-lg shadow-indigo-600/20 active:scale-95"
          >
            {t('save')}
          </button>
          <button 
            onClick={onLogout}
            className="flex items-center gap-2 px-4 py-2.5 text-gray-400 hover:text-red-400 hover:bg-red-400/10 rounded-xl transition-all font-bold text-xs"
          >
            <LogOut size={16} /> {t('logout')}
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar Menu */}
        <div className="w-64 border-r border-gray-800 p-6 space-y-2 bg-gray-950/20">
          <p className="px-4 text-[10px] font-black text-gray-600 uppercase tracking-widest mb-2">{t('core')}</p>
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as SettingsTab)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                activeTab === item.id 
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' 
                  : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'
              }`}
            >
              <item.icon size={18} />
              {item.label}
            </button>
          ))}
          <div className="pt-8 space-y-2">
            <p className="px-4 text-[10px] font-black text-gray-600 uppercase tracking-widest mb-2">{t('pref')}</p>
            {prefItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as SettingsTab)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                  activeTab === item.id 
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' 
                    : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'
                }`}
              >
                <item.icon size={18} />
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-10 scrollbar-thin">
          <div className="max-w-4xl space-y-12 animate-in fade-in slide-in-from-right-4 duration-500">
            
            {activeTab === 'profile' && (
              <section className="space-y-10">
                {/* Header User Card */}
                <div className="flex flex-col md:flex-row items-center gap-10 bg-gradient-to-br from-indigo-600/10 to-purple-600/5 p-10 rounded-[3rem] border border-white/5 shadow-2xl relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-[100px] pointer-events-none" />
                  <div className="relative group">
                    <img src="https://i.pravatar.cc/150?u=rubikai" alt="Avatar" className="w-32 h-32 rounded-[2.5rem] object-cover border-4 border-gray-900 group-hover:scale-105 transition-transform shadow-2xl" />
                    <button className="absolute -bottom-2 -right-2 bg-indigo-600 p-2.5 rounded-2xl border-4 border-gray-900 text-white shadow-xl hover:bg-indigo-700 transition-colors"><RefreshCw size={16}/></button>
                  </div>
                  <div className="flex-1 space-y-4 text-center md:text-left">
                    <div className="space-y-1">
                      <h3 className="text-3xl font-black text-white italic tracking-tight flex items-center justify-center md:justify-start gap-3">
                        智创先锋 
                        <span className="px-3 py-1 bg-indigo-600 text-white text-[10px] uppercase font-black rounded-lg border border-white/10 tracking-[0.2em] shadow-lg">PRO MEMBER</span>
                      </h3>
                      <p className="text-gray-500 text-sm font-medium">短视频架构师 / 视觉内容创作者 / 增长黑客</p>
                    </div>
                    
                    <div className="flex items-center justify-center md:justify-start gap-6 pt-2">
                       <div className="bg-white/5 px-6 py-3 rounded-2xl border border-white/5 flex flex-col items-center shadow-inner">
                          <span className="text-xl font-black text-white">128</span>
                          <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-1">作品总数</span>
                       </div>
                       <div className="bg-white/5 px-6 py-3 rounded-2xl border border-white/5 flex flex-col items-center shadow-inner">
                          <span className="text-xl font-black text-white">2.4k</span>
                          <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-1">可用算力</span>
                       </div>
                       <div className="bg-white/5 px-6 py-3 rounded-2xl border border-white/5 flex flex-col items-center shadow-inner">
                          <span className="text-xl font-black text-indigo-400">98</span>
                          <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-1">爆款评分</span>
                       </div>
                    </div>
                  </div>
                </div>

                {/* Account Fields */}
                <div className="grid grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-4">账户昵称 / Nickname</label>
                    <input type="text" defaultValue="智创先锋" className="w-full bg-gray-950 border border-gray-800 rounded-[1.8rem] px-8 py-5 text-sm font-bold focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all shadow-inner" />
                  </div>
                  <div className="space-y-3">
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] px-4">绑定邮箱 / Email</label>
                    <input type="email" defaultValue="rubik@example.ai" className="w-full bg-gray-950 border border-gray-800 rounded-[1.8rem] px-8 py-5 text-sm font-bold focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all shadow-inner" />
                  </div>
                </div>

                {/* Account Security - Migrated from ProfileModal */}
                <div className="space-y-6 pt-6">
                  <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em] px-4">安全与设置 / Security & Settings</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { label: '修改登录密码', icon: Key, color: 'text-orange-400', desc: '定期更换密码保障账户安全' },
                      { label: '手机号绑定', icon: Smartphone, color: 'text-indigo-400', val: '138****8888', desc: '用于登录验证及安全告警' },
                      { label: '安全中心', icon: Shield, color: 'text-green-400', desc: '查看最近登录记录与设备' },
                      { label: '双重身份验证', icon: ShieldCheck, color: 'text-purple-400', desc: '开启 2FA 提升安全等级', val: '未开启' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-6 bg-gray-950 border border-gray-800 rounded-[2.2rem] hover:border-indigo-500/30 transition-all group cursor-pointer shadow-lg">
                        <div className="flex items-center gap-5">
                          <div className={`p-3 bg-gray-900 rounded-2xl ${item.color} border border-white/5`}>
                            <item.icon size={20} />
                          </div>
                          <div>
                            <p className="text-sm font-black text-white group-hover:text-indigo-400 transition-colors">{item.label}</p>
                            <p className="text-[10px] text-gray-500 mt-1 font-medium">{item.desc}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                           {item.val && <span className="text-[10px] font-mono text-gray-600 bg-white/5 px-2 py-1 rounded-md">{item.val}</span>}
                           <ChevronRight size={16} className="text-gray-800 group-hover:text-white group-hover:translate-x-1 transition-all" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {activeTab === 'theme' && (
              <section className="space-y-8">
                <div>
                  <h3 className="text-2xl font-black mb-2 flex items-center gap-3">
                    <Palette className="text-indigo-500" /> {t('theme')}
                  </h3>
                  <p className="text-gray-500 text-sm">选择最适合您创作心境的视觉风格。</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {[
                    { id: 'dark', label: '深邃空间', icon: Moon, bg: 'bg-[#0b0f1a]' },
                    { id: 'cyberpunk', label: '赛博霓虹', icon: Zap, bg: 'bg-[#000510]', accent: 'text-purple-400', ring: 'shadow-purple-500/20' },
                    { id: 'professional', label: '专业灰色', icon: Layout, bg: 'bg-[#1a1c23]' },
                  ].map((theme) => (
                    <div 
                      key={theme.id}
                      onClick={() => setSelectedTheme(theme.id)}
                      className={`relative p-1 rounded-[2rem] border-2 transition-all cursor-pointer group hover:scale-[1.02] ${selectedTheme === theme.id ? 'border-indigo-500 scale-105 shadow-2xl' : 'border-gray-800 hover:border-gray-700'}`}
                    >
                      <div className={`h-32 rounded-[1.8rem] ${theme.bg} border border-white/5 flex flex-col items-center justify-center gap-2 overflow-hidden`}>
                         <theme.icon className={`w-8 h-8 ${selectedTheme === theme.id ? (theme.accent || 'text-indigo-400') : 'text-gray-600'}`} />
                         {selectedTheme === theme.id && <div className="absolute top-4 right-4 bg-indigo-500 p-1 rounded-full"><Check size={12}/></div>}
                      </div>
                      <div className="p-4 text-center">
                        <p className={`text-sm font-black ${selectedTheme === theme.id ? 'text-white' : 'text-gray-500'}`}>{theme.label}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-gray-800/30 p-8 rounded-[2.5rem] border border-gray-700/50 space-y-6">
                  <h4 className="text-sm font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                    <Monitor size={16} /> 界面元素微调
                  </h4>
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                       <span className="text-sm font-bold text-gray-300">侧边栏毛玻璃效果</span>
                       <div 
                        onClick={() => handleSave()}
                        className="w-12 h-6 bg-indigo-600 rounded-full relative shadow-inner cursor-pointer"
                       >
                         <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
                       </div>
                    </div>
                    <div className="flex items-center justify-between">
                       <span className="text-sm font-bold text-gray-300">高对比度文本</span>
                       <div className="w-12 h-6 bg-gray-700 rounded-full relative shadow-inner cursor-pointer">
                         <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full" />
                       </div>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {activeTab === 'language' && (
              <section className="space-y-8">
                <div>
                  <h3 className="text-2xl font-black mb-2 flex items-center gap-3">
                    <Languages className="text-indigo-500" /> {t('language')}
                  </h3>
                  <p className="text-gray-500 text-sm">选择您更偏好的操作界面语言。</p>
                </div>

                <div className="space-y-4">
                  {[
                    { id: 'zh', label: '简体中文 (Simplified Chinese)', icon: 'CN' },
                    { id: 'en', label: 'English (US)', icon: 'US' },
                  ].map((lang) => (
                    <div 
                      key={lang.id}
                      onClick={() => setSelectedLanguage(lang.id)}
                      className={`flex items-center justify-between p-6 rounded-[2rem] border transition-all cursor-pointer ${selectedLanguage === lang.id ? 'bg-indigo-600/10 border-indigo-500/50' : 'bg-gray-800/30 border-gray-700/50 hover:bg-gray-800/50'}`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gray-900 rounded-xl flex items-center justify-center font-black text-xs border border-white/5">
                          {lang.icon}
                        </div>
                        <span className={`font-bold ${selectedLanguage === lang.id ? 'text-white' : 'text-gray-400'}`}>{lang.label}</span>
                      </div>
                      {selectedLanguage === lang.id && (
                        <div className="bg-indigo-600 p-1.5 rounded-full">
                          <Check className="text-white" size={18} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {activeTab === 'notifications' && (
              <section className="space-y-8">
                <div>
                  <h3 className="text-2xl font-black mb-2 flex items-center gap-3">
                    <Bell className="text-indigo-500" /> {t('notifications')}
                  </h3>
                  <p className="text-gray-500 text-sm">定义系统何时以及如何向您发送关键提醒。</p>
                </div>

                <div className="bg-gray-800/30 rounded-[2.5rem] border border-gray-700/50 overflow-hidden divide-y divide-gray-800">
                  {[
                    { id: 'analysisDone', label: '视频分析完成', desc: '当 AI 引擎完成爆款基因拆解时通知我', icon: BarChart3 },
                    { id: 'weeklyReport', label: '周度创作报告', desc: '每周一发送上周的爆款趋势总结', icon: FileText },
                    { id: 'systemAlert', label: '系统与安全警报', desc: '包含账号登录异常、算力余额预警等', icon: AlertCircle },
                    { id: 'marketing', label: '新功能与活动', desc: '推送最新的 AI 模型迭代与创作者大赛信息', icon: Zap },
                  ].map((item) => (
                    <div key={item.id} className="p-8 flex items-center justify-between hover:bg-gray-800/20 transition-colors">
                      <div className="flex items-center gap-6">
                        <div className="p-3 bg-gray-900 rounded-2xl text-indigo-400 border border-white/5">
                           <item.icon size={20} />
                        </div>
                        <div>
                          <p className="font-black text-white">{item.label}</p>
                          <p className="text-xs text-gray-500 mt-1">{item.desc}</p>
                        </div>
                      </div>
                      <div 
                        onClick={() => toggleNotif(item.id as keyof typeof notifSettings)}
                        className={`w-14 h-7 rounded-full relative transition-all cursor-pointer shadow-inner ${notifSettings[item.id as keyof typeof notifSettings] ? 'bg-indigo-600' : 'bg-gray-700'}`}
                      >
                        <div className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow-md transition-all ${notifSettings[item.id as keyof typeof notifSettings] ? 'right-1' : 'left-1'}`} />
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {activeTab === 'ai' && (
              <section className="space-y-8">
                <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/10 p-8 rounded-[2.5rem] border border-indigo-500/20 shadow-2xl">
                  <div className="flex items-start justify-between mb-8">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-indigo-400 font-black text-xs uppercase tracking-widest">
                        <Cpu size={14} /> AI Engine Configuration
                      </div>
                      <h3 className="text-2xl font-black">智能计算引擎管理</h3>
                    </div>
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-2xl font-bold text-xs ${hasApiKey ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                      {hasApiKey ? <Check size={14} /> : <AlertCircle size={14} />}
                      {hasApiKey ? 'API Key 已就绪' : '需要配置 API Key'}
                    </div>
                  </div>

                  <div className="bg-gray-950/50 rounded-3xl p-6 border border-gray-800 space-y-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-bold">自定义付费 API Key</p>
                        <p className="text-xs text-gray-500 mt-1">针对 Veo 视频生成及 4K 图像渲染，您需要选择自己的付费项目 Key。</p>
                        <a href="https://ai.google.dev/gemini-api/docs/billing" target="_blank" className="text-[10px] text-indigo-400 hover:underline mt-2 inline-flex items-center gap-1 font-black">了解计费规则 <ExternalLink size={10}/></a>
                      </div>
                      <button 
                        onClick={handleOpenKeyDialog}
                        className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-black rounded-xl transition-all shadow-lg shadow-indigo-600/20"
                      >
                        {hasApiKey ? '更换密钥' : '立即选择密钥'}
                      </button>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {activeTab === 'platforms' && (
              <section className="space-y-6">
                <h3 className="text-xl font-black mb-6">平台账号授权管理</h3>
                <div className="grid grid-cols-1 gap-4">
                  {[
                    { name: '抖音 (Douyin)', icon: Smartphone, status: '已授权', expiry: '2025-06-12', color: 'text-pink-500' },
                    { name: '哔哩哔哩 (Bilibili)', icon: Globe, status: '未授权', expiry: '-', color: 'text-blue-400' },
                    { name: 'YouTube / Shorts', icon: Share2, status: '已授权', expiry: '2025-08-01', color: 'text-red-500' },
                  ].map((platform, i) => (
                    <div key={i} className="flex items-center justify-between p-6 bg-gray-800/30 rounded-[2rem] border border-gray-700/50 hover:border-gray-600 transition-all">
                      <div className="flex items-center gap-4">
                         <div className={`w-12 h-12 bg-gray-900 rounded-2xl flex items-center justify-center ${platform.color} border border-white/5`}>
                           <platform.icon size={24} />
                         </div>
                         <div>
                           <p className="font-black">{platform.name}</p>
                           <p className="text-[10px] text-gray-500 font-medium">状态: <span className={platform.status === '已授权' ? 'text-green-400 font-bold' : 'text-gray-600'}>{platform.status}</span></p>
                         </div>
                      </div>
                      <div className="flex items-center gap-6">
                         <div className="text-right hidden sm:block">
                           <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest">有效期至</p>
                           <p className="text-xs font-mono text-gray-400">{platform.expiry}</p>
                         </div>
                         <button className={`px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 ${platform.status === '已授权' ? 'bg-gray-800 text-gray-400 hover:text-red-400' : 'bg-indigo-600 text-white'}`}>
                           {platform.status === '已授权' ? '取消授权' : '立即绑定'}
                         </button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {activeTab === 'storage' && (
              <section className="space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                   <div className="p-8 bg-gray-800/30 rounded-[2.5rem] border border-gray-700/50 space-y-6 shadow-xl">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20"><Cloud size={20}/></div>
                        <h4 className="font-black text-sm uppercase tracking-widest">云存储空间</h4>
                      </div>
                      <div className="space-y-3">
                         <div className="flex justify-between text-xs">
                           <span className="text-gray-400 font-bold">42.5 GB / 100 GB</span>
                           <span className="text-blue-400 font-black">42.5%</span>
                         </div>
                         <div className="h-2 w-full bg-gray-900 rounded-full overflow-hidden border border-gray-800">
                           <div className="h-full bg-blue-500 transition-all duration-1000" style={{width: '42.5%'}} />
                         </div>
                      </div>
                      <button className="w-full py-3 bg-gray-900 hover:bg-gray-800 border border-gray-700 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">
                        管理存储文件
                      </button>
                   </div>

                   <div className="p-8 bg-gray-800/30 rounded-[2.5rem] border border-gray-700/50 space-y-6 shadow-xl">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-purple-500/10 text-purple-400 rounded-xl border border-purple-500/20"><Zap size={20}/></div>
                        <h4 className="font-black text-sm uppercase tracking-widest">Gemini 算力配额</h4>
                      </div>
                      <div className="space-y-3">
                         <div className="flex justify-between text-xs">
                           <span className="text-gray-400 font-bold">12,450 / 50,000 Tokens</span>
                           <span className="text-purple-400 font-black">24.9%</span>
                         </div>
                         <div className="h-2 w-full bg-gray-900 rounded-full overflow-hidden border border-gray-800">
                           <div className="h-full bg-purple-500 transition-all duration-1000" style={{width: '24.9%'}} />
                         </div>
                      </div>
                      <button className="w-full py-3 bg-indigo-600/10 hover:bg-indigo-600 text-indigo-400 hover:text-white border border-indigo-500/20 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">
                        充值 Tokens
                      </button>
                   </div>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;