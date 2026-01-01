
import React, { useState, useEffect, useRef } from 'react';
// Changed MessageCircleText to MessageSquare to fix the import error
import { Smartphone, ShieldCheck, Zap, ArrowRight, RefreshCw, MessageSquare } from 'lucide-react';

interface LoginProps {
  onLoginSuccess: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (countdown > 0) {
      timerRef.current = window.setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
    } else {
      if (timerRef.current) clearTimeout(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [countdown]);

  const handleSendCode = () => {
    if (phone.length !== 11) {
      alert('请输入正确的11位手机号');
      return;
    }
    setIsSending(true);
    // 模拟发送请求
    setTimeout(() => {
      setIsSending(false);
      setCountdown(60);
    }, 800);
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (phone.length !== 11 || code.length < 4) {
      alert('请输入完整的登录信息');
      return;
    }
    setIsLoading(true);
    // 模拟登录
    setTimeout(() => {
      setIsLoading(false);
      onLoginSuccess();
    }, 1500);
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-[#0b0f1a] overflow-hidden">
      {/* 动态背景背景 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-indigo-600/20 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute top-[60%] -right-[5%] w-[35%] h-[35%] bg-purple-600/20 blur-[100px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
        {/* 背景粒子感效果 */}
        <div className="absolute inset-0 opacity-[0.03] bg-[url('https://www.transparenttextures.com/patterns/stardust.png')]" />
      </div>

      <div className="relative w-full max-w-[480px] p-8 sm:p-12 animate-in fade-in zoom-in slide-in-from-bottom-8 duration-700">
        <div className="glass rounded-[3rem] border border-white/10 p-10 shadow-2xl glow-indigo relative overflow-hidden">
          {/* 装饰图标 */}
          <div className="absolute top-0 right-0 p-8 opacity-5">
            <Zap size={160} className="rotate-12" />
          </div>

          <div className="relative z-10 space-y-10">
            {/* Logo & Title */}
            <div className="text-center space-y-3">
              <div className="inline-flex items-center justify-center p-3 bg-indigo-600 rounded-2xl shadow-xl shadow-indigo-600/30 mb-2">
                <Zap className="text-white w-8 h-8 fill-white/10" />
              </div>
              <h1 className="text-4xl font-black bg-gradient-to-br from-white via-gray-100 to-gray-400 bg-clip-text text-transparent tracking-tighter">
                魔方 AI
              </h1>
              <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.4em]">Viral Creation Engine</p>
            </div>

            {/* Form */}
            <form onSubmit={handleLogin} className="space-y-6">
              <div className="space-y-2">
                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest ml-4">手机号码 / Mobile Number</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-6 flex items-center pointer-events-none text-gray-500 group-focus-within:text-indigo-400 transition-colors">
                    <Smartphone size={18} />
                  </div>
                  <input
                    type="tel"
                    maxLength={11}
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                    className="w-full pl-16 pr-8 py-5 bg-gray-950/50 border border-gray-800 rounded-[2rem] text-sm font-medium focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-gray-700 shadow-inner"
                    placeholder="请输入手机号"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest ml-4">验证码 / Verification Code</label>
                <div className="flex gap-3">
                  <div className="relative flex-1 group">
                    <div className="absolute inset-y-0 left-6 flex items-center pointer-events-none text-gray-500 group-focus-within:text-indigo-400 transition-colors">
                      <ShieldCheck size={18} />
                    </div>
                    <input
                      type="text"
                      maxLength={6}
                      value={code}
                      onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                      className="w-full pl-16 pr-8 py-5 bg-gray-950/50 border border-gray-800 rounded-[2rem] text-sm font-medium focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all placeholder:text-gray-700 shadow-inner"
                      placeholder="验证码"
                      required
                    />
                  </div>
                  <button
                    type="button"
                    disabled={countdown > 0 || isSending || phone.length !== 11}
                    onClick={handleSendCode}
                    className={`min-w-[120px] px-4 py-5 rounded-[2rem] text-[10px] font-black uppercase tracking-widest border transition-all ${
                      countdown > 0 
                      ? 'bg-gray-900 border-gray-800 text-gray-600' 
                      : 'bg-indigo-600/10 border-indigo-500/20 text-indigo-400 hover:bg-indigo-600 hover:text-white'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {isSending ? <RefreshCw size={14} className="animate-spin mx-auto" /> : countdown > 0 ? `${countdown}s` : '获取验证码'}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-5 bg-white text-gray-950 font-black rounded-[2rem] transition-all shadow-2xl flex items-center justify-center gap-4 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 text-xs uppercase tracking-[0.2em]"
              >
                {isLoading ? <RefreshCw size={16} className="animate-spin" /> : <>开启创作之旅 <ArrowRight size={18} /></>}
              </button>
            </form>

            {/* Footer */}
            <div className="text-center pt-4">
               <p className="text-[10px] text-gray-600 font-medium">
                 登录即代表您同意 <span className="text-gray-400 hover:text-indigo-400 cursor-pointer underline underline-offset-4">服务协议</span> 与 <span className="text-gray-400 hover:text-indigo-400 cursor-pointer underline underline-offset-4">隐私政策</span>
               </p>
               <div className="flex items-center justify-center gap-6 mt-8">
                  <div className="w-10 h-10 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-center text-gray-500 hover:text-white hover:border-gray-600 transition-all cursor-pointer">
                    {/* Replaced non-existent MessageCircleText with MessageSquare */}
                    <MessageSquare size={20} />
                  </div>
               </div>
            </div>
          </div>
        </div>
        
        {/* 系统提示 */}
        <div className="mt-8 text-center animate-in fade-in duration-1000 delay-500">
          <p className="text-[9px] font-black text-gray-700 uppercase tracking-[0.5em]">Powered by Gemini 3.0 Pro Engine</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
