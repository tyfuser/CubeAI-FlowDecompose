import React from 'react';
import { User, Settings, Shield, Smartphone, Mail, Key, LogOut, X, ChevronRight, Zap } from 'lucide-react';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogout: () => void;
}

const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose, onLogout }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex">
      {/* Background Mask */}
      <div 
        className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-in fade-in duration-300"
        onClick={onClose}
      />
      
      {/* Panel Content */}
      <div className="relative w-full max-w-[400px] h-full bg-[#0d111d]/90 backdrop-blur-2xl border-r border-white/5 shadow-2xl animate-in slide-in-from-left duration-500 overflow-y-auto scrollbar-none">
        <div className="p-8 space-y-10">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-black italic tracking-tight text-white uppercase">个人中心 <span className="text-indigo-500">.</span></h2>
            <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-colors text-gray-500 hover:text-white">
              <X size={20} />
            </button>
          </div>

          {/* User Info Card */}
          <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/10 p-8 rounded-[2.5rem] border border-indigo-500/20 shadow-xl relative overflow-hidden group">
            <div className="absolute -top-10 -right-10 w-32 h-32 bg-indigo-500/10 blur-[50px] group-hover:bg-indigo-500/20 transition-all duration-700" />
            <div className="relative z-10 flex flex-col items-center text-center space-y-4">
              <div className="relative">
                <div className="w-24 h-24 rounded-[2rem] border-4 border-gray-950 overflow-hidden shadow-2xl">
                  <img src="https://i.pravatar.cc/150?u=rubikai" alt="Avatar" className="w-full h-full object-cover" />
                </div>
                <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 border-4 border-gray-950 rounded-full" />
              </div>
              <div>
                <h3 className="text-2xl font-black text-white">智创先锋</h3>
                <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mt-1 italic">Rubik VIP Member</p>
              </div>
              <div className="flex gap-4 pt-2">
                 <div className="bg-white/5 px-4 py-2 rounded-xl border border-white/5 flex flex-col items-center">
                    <span className="text-sm font-black text-white">128</span>
                    <span className="text-[8px] text-gray-500 font-bold uppercase">作品</span>
                 </div>
                 <div className="bg-white/5 px-4 py-2 rounded-xl border border-white/5 flex flex-col items-center">
                    <span className="text-sm font-black text-white">2.4k</span>
                    <span className="text-[8px] text-gray-500 font-bold uppercase">算力</span>
                 </div>
              </div>
            </div>
          </div>

          {/* Account Settings */}
          <div className="space-y-6">
            <p className="px-4 text-[10px] font-black text-gray-600 uppercase tracking-widest">账户设置 / Account Settings</p>
            <div className="space-y-2">
              {[
                { label: '修改登录密码', icon: Key, color: 'text-orange-400' },
                { label: '绑定手机号', icon: Smartphone, color: 'text-indigo-400', val: '138****8888' },
                { label: '关联电子邮箱', icon: Mail, color: 'text-purple-400', val: '未绑定' },
                { label: '安全中心', icon: Shield, color: 'text-green-400' },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between p-5 hover:bg-white/5 rounded-2xl border border-transparent hover:border-white/5 transition-all group cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 bg-gray-900 rounded-xl ${item.color} border border-white/5 shadow-inner`}>
                      <item.icon size={18} />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-gray-300 group-hover:text-white transition-colors">{item.label}</p>
                      {item.val && <p className="text-[10px] text-gray-600 font-mono">{item.val}</p>}
                    </div>
                  </div>
                  <ChevronRight size={16} className="text-gray-700 group-hover:text-gray-400 group-hover:translate-x-1 transition-all" />
                </div>
              ))}
            </div>
          </div>

          {/* Logout Section */}
          <div className="pt-10">
            <button 
              onClick={onLogout}
              className="w-full py-5 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/20 rounded-[2rem] text-xs font-black uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-4 shadow-xl active:scale-95"
            >
              <LogOut size={18} /> 退出当前登录
            </button>
            <p className="text-center text-[9px] text-gray-700 font-medium mt-8 italic uppercase tracking-widest">Powered by Rubik AI Security Protocol</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileModal;