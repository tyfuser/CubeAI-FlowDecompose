/**
 * AdviceDisplay Component
 * 
 * Displays realtime shooting advice with priority-based styling.
 * Implements auto-dismiss (3s for non-critical) per Requirements 10.1-10.5.
 */
import React, { useEffect, useState, useCallback } from 'react';

export interface AdvicePayload {
  type: 'advice';
  priority: 'critical' | 'warning' | 'info' | 'positive';
  category: string;
  message: string;
  advanced_message?: string | null;
  timestamp: number;
  suppress_duration_ms: number;
  trigger_haptic: boolean;
}

export interface EnvironmentData {
  environment_tags: string[];
  shootability_score: number;
  constraints: string[];
  recommended_risk_level: string;
  theme_candidates: string[];
  confidence: number;
  timestamp: number;
}

export interface TaskData {
  task_id: string;
  task_name: string;
  description: string;
  target_duration_s: number;
  risk_level: string;
  success_criteria: string;
  target_motion?: string;
  target_speed_range?: [number, number];
  state: string;
  progress: number;
  timestamp: number;
}

interface AdviceDisplayProps {
  advice: AdvicePayload | null;
  onDismiss?: () => void;
  showAdvanced?: boolean;
  environment?: EnvironmentData | null;
  currentTask?: TaskData | null;
}

// Priority-based styling configuration
const PRIORITY_STYLES: Record<AdvicePayload['priority'], {
  bgColor: string;
  borderColor: string;
  textColor: string;
  icon: string;
  animation: string;
}> = {
  critical: {
    bgColor: 'bg-red-600/90',
    borderColor: 'border-red-400',
    textColor: 'text-white',
    icon: '⚠️',
    animation: 'animate-pulse',
  },
  warning: {
    bgColor: 'bg-yellow-500/80',
    borderColor: 'border-yellow-300',
    textColor: 'text-black',
    icon: '⚡',
    animation: '',
  },
  info: {
    bgColor: 'bg-blue-500/70',
    borderColor: 'border-blue-300',
    textColor: 'text-white',
    icon: '💡',
    animation: '',
  },
  positive: {
    bgColor: 'bg-green-500/70',
    borderColor: 'border-green-300',
    textColor: 'text-white',
    icon: '✓',
    animation: '',
  },
};

// Auto-dismiss duration (3s for non-critical per Requirement 10.5)
const AUTO_DISMISS_MS = 3000;

export const AdviceDisplay: React.FC<AdviceDisplayProps> = ({
  advice,
  onDismiss,
  showAdvanced = false,
  environment,
  currentTask,
}) => {
  const [visible, setVisible] = useState(false);
  const [currentAdvice, setCurrentAdvice] = useState<AdvicePayload | null>(null);

  // Handle new advice
  useEffect(() => {
    if (advice) {
      setCurrentAdvice(advice);
      setVisible(true);

      // Auto-dismiss for non-critical advice (Requirement 10.5)
      if (advice.priority !== 'critical') {
        const dismissTime = advice.suppress_duration_ms || AUTO_DISMISS_MS;
        const timer = setTimeout(() => {
          setVisible(false);
          onDismiss?.();
        }, dismissTime);
        return () => clearTimeout(timer);
      }
    }
  }, [advice, onDismiss]);

  // Handle manual dismiss
  const handleDismiss = useCallback(() => {
    setVisible(false);
    onDismiss?.();
  }, [onDismiss]);

  if (!visible || !currentAdvice) {
    return null;
  }

  const style = PRIORITY_STYLES[currentAdvice.priority];

  // Critical advice: prominent red banner (Requirement 10.1)
  if (currentAdvice.priority === 'critical') {
    return (
      <div
        className={`fixed top-0 left-0 right-0 z-50 ${style.bgColor} ${style.borderColor} border-b-2 ${style.animation}`}
        onClick={handleDismiss}
      >
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{style.icon}</span>
            <div>
              <p className={`${style.textColor} font-bold text-sm`}>
                {currentAdvice.message}
              </p>
              {showAdvanced && currentAdvice.advanced_message && (
                <p className={`${style.textColor} text-xs opacity-80 mt-1`}>
                  {currentAdvice.advanced_message}
                </p>
              )}
            </div>
          </div>
          <button
            className={`${style.textColor} text-xl font-bold px-2`}
            onClick={handleDismiss}
          >
            ×
          </button>
        </div>
      </div>
    );
  }

  // Warning advice: yellow indicator at screen edge (Requirement 10.2)
  if (currentAdvice.priority === 'warning') {
    return (
      <div
        className={`fixed top-16 right-2 z-40 max-w-[280px] ${style.bgColor} ${style.borderColor} border rounded-lg shadow-lg`}
        onClick={handleDismiss}
      >
        <div className="px-3 py-2 flex items-start gap-2">
          <span className="text-lg">{style.icon}</span>
          <div className="flex-1">
            <p className={`${style.textColor} font-medium text-sm`}>
              {currentAdvice.message}
            </p>
            {showAdvanced && currentAdvice.advanced_message && (
              <p className={`${style.textColor} text-xs opacity-80 mt-1`}>
                {currentAdvice.advanced_message}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Info advice: subtle blue text overlay (Requirement 10.3)
  if (currentAdvice.priority === 'info') {
    return (
      <div
        className={`fixed bottom-24 left-1/2 transform -translate-x-1/2 z-30 max-w-[90%] ${style.bgColor} ${style.borderColor} border rounded-full shadow-md`}
        onClick={handleDismiss}
      >
        <div className="px-4 py-2 flex items-center gap-2">
          <span className="text-base">{style.icon}</span>
          <p className={`${style.textColor} text-sm`}>
            {currentAdvice.message}
          </p>
        </div>
      </div>
    );
  }

  // Positive advice: brief green checkmark animation (Requirement 10.4)
  if (currentAdvice.priority === 'positive') {
    return (
      <div
        className={`fixed top-16 left-1/2 transform -translate-x-1/2 z-30 ${style.bgColor} ${style.borderColor} border rounded-full shadow-md animate-bounce`}
        onClick={handleDismiss}
      >
        <div className="px-4 py-2 flex items-center gap-2">
          <span className="text-xl">{style.icon}</span>
          <p className={`${style.textColor} text-sm font-medium`}>
            {currentAdvice.message}
          </p>
        </div>
      </div>
    );
  }

  // Environment and Task Status Display
  return (
    <div className="fixed bottom-4 left-4 z-30 space-y-2 max-w-xs">
      {/* Environment Status */}
      {environment && (
        <div className="bg-black/60 backdrop-blur-md rounded-lg p-3 border border-white/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white text-xs font-medium">环境分析</span>
            <span className={`text-xs px-2 py-1 rounded ${
              environment.shootability_score > 0.7 ? 'bg-green-500/20 text-green-400' :
              environment.shootability_score > 0.5 ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-red-500/20 text-red-400'
            }`}>
              {(environment.shootability_score * 100).toFixed(0)}%
            </span>
          </div>
          {environment.environment_tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {environment.environment_tags.slice(0, 3).map((tag, index) => (
                <span key={index} className="text-white/70 text-xs bg-white/10 px-2 py-1 rounded">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Task Status */}
      {currentTask && (
        <div className="bg-black/60 backdrop-blur-md rounded-lg p-3 border border-white/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white text-xs font-medium">{currentTask.task_name}</span>
            <span className={`text-xs px-2 py-1 rounded ${
              currentTask.state === 'done' ? 'bg-green-500/20 text-green-400' :
              currentTask.state === 'recovery' ? 'bg-orange-500/20 text-orange-400' :
              currentTask.state === 'executing' ? 'bg-blue-500/20 text-blue-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>
              {currentTask.state === 'executing' ? `${(currentTask.progress * 100).toFixed(0)}%` : currentTask.state}
            </span>
          </div>
          <div className="w-full bg-gray-600 rounded-full h-1 mb-2">
            <div
              className="bg-cyan-400 h-1 rounded-full transition-all duration-300"
              style={{ width: `${currentTask.progress * 100}%` }}
            />
          </div>
          <p className="text-white/80 text-xs">
            {currentTask.description}
          </p>
        </div>
      )}
    </div>
  );
};

export default AdviceDisplay;
