import React, { useState, useRef } from 'react';
import { Upload, FileVideo, Play, Pause, History, Trash2, ChevronRight, X } from 'lucide-react';
import { Segment, Feature, JobResponse, HistoryItem } from '../types';
import { createAnalysisJob, pollJobStatus, getJobStatus, getHistory, deleteJob } from '../services/videoAnalysisService';
import { isApiError } from '../services/api';

const ShotAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'history'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [videoPath, setVideoPath] = useState<string>('');
  const [videoUrl, setVideoUrl] = useState<string>(''); // 视频播放 URL
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState({ percent: 0, message: '', stage: '' });
  const [result, setResult] = useState<JobResponse | null>(null);
  const [partialSegments, setPartialSegments] = useState<Segment[]>([]); // 部分片段
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<Segment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [failedThumbnails, setFailedThumbnails] = useState<Set<string>>(new Set());
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // 处理文件选择
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      
      // 创建本地预览 URL
      const url = URL.createObjectURL(file);
      setVideoUrl(url);
    }
  };

  // 处理拖拽上传
  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file);
      setError(null);
      
      // 创建本地预览 URL
      const url = URL.createObjectURL(file);
      setVideoUrl(url);
    }
  };

  // 开始分析
  const handleStartAnalysis = async () => {
    if (!videoPath.trim() && !selectedFile) {
      setError('请输入视频路径或选择本地文件');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setProgress({ percent: 0, message: '正在创建分析任务...' });

    try {
      // 如果是文件上传，先上传文件获取服务器路径
      let actualPath = videoPath;
      
      if (selectedFile) {
        console.log('上传文件:', selectedFile.name);
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        try {
          const uploadResponse = await fetch('http://localhost:8000/api/v1/analysis/upload', {
            method: 'POST',
            body: formData
          });
          
          const uploadResult = await uploadResponse.json();
          
          if (!uploadResult.success) {
            throw new Error(uploadResult.message || '文件上传失败');
          }
          
          actualPath = uploadResult.data.filePath;
          console.log('文件已上传到:', actualPath);
        } catch (uploadError: any) {
          throw new Error(`文件上传失败: ${uploadError.message}`);
        }
      }
      
      // 创建任务
      const videoSource = { type: 'file' as const, path: actualPath };

      const createResponse = await createAnalysisJob(videoSource, {
        frame_extract: { fps: 2.0, max_frames: 240 },
        llm: { 
          provider: 'sophnet',
          enabled_modules: ['camera_motion', 'lighting', 'color_grading']
        }
      });

      console.log('任务已创建:', createResponse.job_id);

      // 轮询状态
      const finalResult = await pollJobStatus(
        createResponse.job_id,
        (progressData) => {
          if (progressData.progress) {
            setProgress({
              percent: progressData.progress.percent,
              message: progressData.progress.message
            });
          }
          
          // 显示部分结果
          if (progressData.partial_result) {
            setResult(progressData);
          }
        },
        120,
        1000
      );

      setResult(finalResult);
      setProgress({ percent: 100, message: '分析完成！' });
      
    } catch (err: any) {
      console.error('分析失败:', err);
      if (isApiError(err)) {
        setError(err.message || '分析失败，请稍后重试');
      } else {
        setError('网络连接失败，请检查后端服务');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 加载历史记录
  const handleLoadHistory = async () => {
    try {
      const historyData = await getHistory(50);
      setHistory(historyData);
      setActiveTab('history');
      setFailedThumbnails(new Set()); // 清空失败记录
      
      // 调试：打印缩略图URL
      console.log('历史记录加载完成，缩略图URL:');
      historyData.forEach(item => {
        if (item.thumbnail_url) {
          console.log(`- ${item.title}: ${item.thumbnail_url}`);
        } else {
          console.log(`- ${item.title}: 无缩略图`);
        }
      });
    } catch (err: any) {
      console.error('加载历史记录失败:', err);
      setError('加载历史记录失败');
    }
  };

  // 加载历史记录详情
  const handleLoadHistoryDetail = async (item: HistoryItem) => {
    try {
      setError(null);
      setProgress({ percent: 0, message: '正在加载历史记录...', stage: '加载中' });
      
      // 获取完整的任务结果
      const jobResult = await getJobStatus(item.job_id);
      
      if (jobResult.status === 'succeeded' && jobResult.result) {
        setResult(jobResult);
        // 切换到上传标签页以显示结果
        setActiveTab('upload');
        
        // 清空部分片段（使用完整结果）
        setPartialSegments([]);
        
        // 设置视频URL/路径
        if (jobResult.target_video) {
          const video = jobResult.target_video;
          // 如果有本地路径，构建预览URL
          if (video.local_path) {
            // 检查是否在 data/uploads 目录
            if (video.local_path.includes('/uploads/')) {
              const baseUrl = 'http://localhost:8000';
              const filename = video.local_path.split('/uploads/').pop();
              const previewUrl = `${baseUrl}/data/uploads/${filename}`;
              setVideoUrl(previewUrl);
              console.log('设置视频预览URL:', previewUrl);
            } else if (video.local_path.includes('/jobs/')) {
              // 如果在 jobs 目录下
              const pathAfterJobs = video.local_path.split('/jobs/').pop();
              const baseUrl = 'http://localhost:8000';
              const previewUrl = `${baseUrl}/data/jobs/${pathAfterJobs}`;
              setVideoUrl(previewUrl);
              console.log('设置视频预览URL:', previewUrl);
            } else {
              // 尝试直接使用文件名
              const filename = video.local_path.split('/').pop();
              const baseUrl = 'http://localhost:8000';
              const previewUrl = `${baseUrl}/data/uploads/${filename}`;
              setVideoUrl(previewUrl);
              console.log('尝试设置视频预览URL:', previewUrl);
            }
          } else if (video.source_url) {
            setVideoUrl(video.source_url);
          } else if (video.source_path) {
            setVideoPath(video.source_path);
          }
        }
        
        setProgress({ percent: 100, message: '历史记录加载完成', stage: '完成' });
        setTimeout(() => setProgress({ percent: 0, message: '', stage: '' }), 2000);
      } else if (jobResult.status === 'failed') {
        setError('该任务分析失败，无法查看详情');
      } else if (jobResult.status === 'running') {
        setError('该任务仍在分析中，请稍后再试');
      } else {
        setError('该任务尚未完成分析');
      }
    } catch (err: any) {
      console.error('加载历史记录详情失败:', err);
      setError('加载历史记录详情失败');
    }
  };

  // 删除历史记录
  const handleDeleteHistory = async (jobId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // 阻止事件冒泡，避免触发查看详情
    if (!confirm('确定删除此记录？')) return;
    
    try {
      await deleteJob(jobId);
      setHistory(history.filter(item => item.job_id !== jobId));
    } catch (err: any) {
      console.error('删除失败:', err);
      setError('删除失败');
    }
  };

  // 格式化时间
  const formatTime = (ms: number) => {
    const seconds = ms / 1000;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const millis = Math.floor((seconds % 1) * 1000);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${millis.toString().padStart(3, '0')}`;
  };

  // 跳转到视频时间
  const seekToTime = (timeMs: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timeMs / 1000;
      videoRef.current.play();
    }
  };

  // 渲染时间轴
  const renderTimeline = () => {
    // 优先使用部分结果，如果没有则使用最终结果
    const segments = partialSegments.length > 0 
      ? partialSegments 
      : result?.result?.target.segments;
    
    if (!segments || segments.length === 0) return null;

    const totalDuration = segments[segments.length - 1]?.end_ms || 1;

    return (
      <div className="space-y-6">
        {/* 时间标尺 */}
        <div className="relative h-8 bg-gray-900 rounded-lg">
          {Array.from({ length: 11 }).map((_, i) => {
            const time = (totalDuration / 10) * i;
            return (
              <div
                key={i}
                className="absolute top-0 h-full flex items-center"
                style={{ left: `${i * 10}%` }}
              >
                <div className="w-px h-3 bg-gray-700" />
                <span className="absolute top-4 -translate-x-1/2 text-[10px] text-gray-500 font-mono">
                  {formatTime(time)}
                </span>
              </div>
            );
          })}
        </div>

        {/* 镜头片段轨道 */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-gray-400 mb-2">
            <FileVideo size={14} />
            <span>镜头片段</span>
          </div>
          <div className="relative h-20 bg-gray-900/50 rounded-lg border border-gray-800">
            {segments.map((segment) => {
              const left = (segment.start_ms / totalDuration) * 100;
              const width = (segment.duration_ms / totalDuration) * 100;
              
              const isAnalyzing = segment.analyzing;
              
              return (
                <div
                  key={segment.segment_id}
                  className={`absolute top-1 bottom-1 border-2 rounded cursor-pointer transition-all group ${
                    isAnalyzing 
                      ? 'bg-yellow-600/20 border-yellow-500 animate-pulse' 
                      : 'bg-indigo-600/20 border-indigo-500 hover:bg-indigo-600/30'
                  }`}
                  style={{ left: `${left}%`, width: `${width}%` }}
                  onClick={() => {
                    setSelectedSegment(segment);
                    seekToTime(segment.start_ms);
                  }}
                >
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-[10px] font-bold text-white">
                    {isAnalyzing ? (
                      <>
                        <span className="text-yellow-400">分析中...</span>
                        <span className="text-[8px] text-gray-500">{segment.segment_id}</span>
                      </>
                    ) : (
                      <>
                        <span>{segment.segment_id}</span>
                        <span className="text-indigo-400">{(segment.duration_ms / 1000).toFixed(1)}s</span>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 运镜轨道 */}
        {renderFeatureTrack(segments, totalDuration, 'camera_motion', '🎥 运镜', 'from-blue-600 to-cyan-600')}

        {/* 光线轨道 */}
        {renderFeatureTrack(segments, totalDuration, 'lighting', '💡 光线', 'from-yellow-600 to-orange-600')}

        {/* 调色轨道 */}
        {renderFeatureTrack(segments, totalDuration, 'color_grading', '🎨 调色', 'from-purple-600 to-pink-600')}
      </div>
    );
  };

  // 渲染特征轨道
  const renderFeatureTrack = (
    segments: Segment[],
    totalDuration: number,
    category: string,
    label: string,
    gradient: string
  ) => {
    return (
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-gray-400">
          <span>{label}</span>
        </div>
        <div className="relative h-16 bg-gray-900/50 rounded-lg border border-gray-800">
          {segments.map((segment) => {
            const features = segment.features.filter(f => f.category === category);
            if (features.length === 0) return null;

            const left = (segment.start_ms / totalDuration) * 100;
            const width = (segment.duration_ms / totalDuration) * 100;

            return features.map((feature, idx) => (
              <div
                key={`${segment.segment_id}-${idx}`}
                className={`absolute top-1 bottom-1 bg-gradient-to-r ${gradient} bg-opacity-20 border border-white/20 rounded cursor-pointer hover:scale-105 transition-transform animate-in fade-in duration-500`}
                style={{ 
                  left: `${left}%`, 
                  width: `${width}%`,
                  animationDelay: `${idx * 100}ms`
                }}
                onClick={() => {
                  setSelectedSegment(segment);
                  seekToTime(segment.start_ms);
                }}
              >
                <div className="absolute inset-0 flex flex-col items-center justify-center text-[10px] font-bold text-white">
                  <span>{feature.value}</span>
                  <span className="text-white/60">{Math.round(feature.confidence * 100)}%</span>
                </div>
              </div>
            ));
          })}
        </div>
      </div>
    );
  };

  // 渲染详情面板
  const renderDetailPanel = () => {
    if (!selectedSegment) return null;

    return (
      <div className="fixed right-0 top-0 w-[400px] h-full bg-[#0d111d] border-l border-gray-800 shadow-2xl z-50 overflow-y-auto animate-in slide-in-from-right duration-300">
        <div className="sticky top-0 bg-[#0d111d] border-b border-gray-800 p-6 flex items-center justify-between">
          <h3 className="text-lg font-black text-white">镜头详细分析</h3>
          <button
            onClick={() => setSelectedSegment(null)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X size={18} className="text-gray-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* 基本信息 */}
          <div className="bg-gray-900/50 rounded-2xl p-4 border border-gray-800">
            <h4 className="text-sm font-black text-indigo-400 mb-3">📹 镜头信息</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">片段ID:</span>
                <span className="text-white font-bold">{selectedSegment.segment_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">开始时间:</span>
                <span className="text-white font-mono">{formatTime(selectedSegment.start_ms)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">结束时间:</span>
                <span className="text-white font-mono">{formatTime(selectedSegment.end_ms)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">时长:</span>
                <span className="text-white font-bold">{(selectedSegment.duration_ms / 1000).toFixed(2)}秒</span>
              </div>
            </div>
          </div>

          {/* 特征分析 */}
          {['camera_motion', 'lighting', 'color_grading'].map((category) => {
            const features = selectedSegment.features.filter(f => f.category === category);
            if (features.length === 0) return null;

            const categoryNames = {
              camera_motion: '🎥 运镜分析',
              lighting: '💡 光线分析',
              color_grading: '🎨 调色分析'
            };

            return (
              <div key={category} className="bg-gray-900/50 rounded-2xl p-4 border border-gray-800">
                <h4 className="text-sm font-black text-indigo-400 mb-3">
                  {categoryNames[category as keyof typeof categoryNames]}
                </h4>
                <div className="space-y-3">
                  {features.map((feature, idx) => (
                    <div key={idx} className="bg-gray-950/50 rounded-xl p-3 border border-gray-700">
                      <div className="flex items-center justify-between mb-2">
                        <span className="px-2 py-1 bg-indigo-600/20 text-indigo-400 rounded text-xs font-bold">
                          {feature.value}
                        </span>
                        <span className="text-xs text-gray-500">
                          置信度: {Math.round(feature.confidence * 100)}%
                        </span>
                      </div>
                      {feature.detailed_description && (
                        <div className="mt-2 space-y-2">
                          <p className="text-xs text-gray-400">{feature.detailed_description.summary}</p>
                          {feature.detailed_description.purpose && (
                            <p className="text-xs text-gray-500">
                              <strong className="text-gray-400">用途:</strong> {feature.detailed_description.purpose}
                            </p>
                          )}
                          {feature.detailed_description.technical_terms.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {feature.detailed_description.technical_terms.map((term, i) => (
                                <span key={i} className="px-2 py-0.5 bg-gray-800 text-gray-400 rounded text-[10px]">
                                  {term}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full overflow-y-auto bg-[#05070a] text-white">
      <div className="max-w-7xl mx-auto p-8">
        {/* 头部 */}
        <div className="mb-8">
          <h1 className="text-3xl font-black mb-2">视频镜头拆解分析</h1>
          <p className="text-gray-500 text-sm">
            上传视频，自动识别镜头、运镜、光线和调色技巧
          </p>
        </div>

        {/* 标签页 */}
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-6 py-3 rounded-xl font-bold text-sm transition-all ${
              activeTab === 'upload'
                ? 'bg-indigo-600 text-white shadow-lg'
                : 'bg-gray-900 text-gray-500 hover:text-gray-300'
            }`}
          >
            <Upload size={16} className="inline mr-2" />
            开始分析
          </button>
          <button
            onClick={handleLoadHistory}
            className={`px-6 py-3 rounded-xl font-bold text-sm transition-all ${
              activeTab === 'history'
                ? 'bg-indigo-600 text-white shadow-lg'
                : 'bg-gray-900 text-gray-500 hover:text-gray-300'
            }`}
          >
            <History size={16} className="inline mr-2" />
            历史记录
          </button>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* 上传界面 */}
        {activeTab === 'upload' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 左侧：上传和控制 */}
            <div className="space-y-6">
            {/* 文件上传区 */}
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              className="relative flex flex-col items-center justify-center w-full h-48 p-6 text-center border-2 border-dashed rounded-3xl cursor-pointer border-gray-700 hover:border-indigo-500/50 bg-gray-950/80 group transition-all"
            >
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept="video/*"
                onChange={handleFileChange}
              />
              {selectedFile ? (
                <div className="flex flex-col items-center gap-2">
                  <FileVideo size={40} className="text-green-400" />
                  <p className="text-sm font-bold text-white">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload size={40} className="mx-auto text-indigo-400 group-hover:scale-110 transition-transform" />
                  <p className="text-sm font-bold text-white">点击或拖拽视频文件至此</p>
                  <p className="text-xs text-gray-500">支持 MP4, MOV, AVI 等格式，最大 500MB</p>
                </div>
              )}
            </div>

            {/* 路径输入 */}
            <div className="relative">
              <input
                type="text"
                className="w-full px-6 py-4 bg-gray-950/80 border border-gray-700 rounded-2xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all placeholder:text-gray-700 text-sm font-medium"
                placeholder="或直接输入本地文件路径（例如：/Users/tang/Videos/video.mp4）"
                value={videoPath}
                onChange={(e) => setVideoPath(e.target.value)}
              />
            </div>

            {/* 开始按钮 */}
            <button
              onClick={handleStartAnalysis}
              disabled={isAnalyzing}
              className="w-full py-5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-800 disabled:text-gray-600 text-white font-black rounded-2xl transition-all shadow-lg text-sm uppercase tracking-wider"
            >
              {isAnalyzing ? '分析中...' : '开始分析'}
            </button>

            {/* 进度条 */}
            {(isAnalyzing || progress.message) && (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className={`${progress.percent === 100 ? 'text-green-400' : 'text-gray-400'}`}>
                    {progress.message}
                  </span>
                  {progress.percent > 0 && (
                    <span className={`font-bold ${progress.percent === 100 ? 'text-green-400' : 'text-indigo-400'}`}>
                      {Math.round(progress.percent)}%
                    </span>
                  )}
                </div>
                {progress.percent > 0 && (
                  <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        progress.percent === 100 ? 'bg-green-500' : 'bg-indigo-500'
                      }`}
                      style={{ width: `${progress.percent}%` }}
                    />
                  </div>
                )}
              </div>
            )}

            </div>

            {/* 右侧：视频播放器 */}
            <div className="space-y-6">
              {videoUrl ? (
                <div className="sticky top-6">
                  <div className="bg-gray-950/80 border border-gray-800 rounded-3xl overflow-hidden shadow-2xl">
                    <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                      <h3 className="text-sm font-black text-white flex items-center gap-2">
                        <Play size={16} className="text-indigo-400" />
                        视频预览
                      </h3>
                      {selectedFile && (
                        <span className="text-xs text-gray-500">
                          {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                        </span>
                      )}
                    </div>
                    <video
                      ref={videoRef}
                      src={videoUrl}
                      controls
                      className="w-full aspect-video bg-black"
                    />
                    {selectedSegment && (
                      <div className="p-4 bg-indigo-600/10 border-t border-indigo-500/20">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-indigo-400 font-bold">
                            📍 {selectedSegment.segment_id}
                          </span>
                          <span className="text-gray-500">
                            {formatTime(selectedSegment.start_ms)} - {formatTime(selectedSegment.end_ms)}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 实时进度 */}
                  {isAnalyzing && (
                    <div className="mt-4 p-4 bg-gray-950/80 border border-gray-800 rounded-2xl">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-sm font-bold text-white">{progress.stage || '分析中'}</span>
                      </div>
                      <p className="text-xs text-gray-400 mb-3">{progress.message}</p>
                      <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full transition-all duration-300"
                          style={{ width: `${progress.percent}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-500">
                          {partialSegments.length} 个片段已识别
                        </span>
                        <span className="text-xs text-indigo-400 font-bold">
                          {Math.round(progress.percent)}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 bg-gray-950/50 border border-gray-800 border-dashed rounded-3xl">
                  <div className="text-center">
                    <Play size={48} className="mx-auto mb-3 text-gray-700" />
                    <p className="text-sm text-gray-500">选择视频后将在此显示预览</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 时间轴结果（全宽显示在底部） */}
        {activeTab === 'upload' && (partialSegments.length > 0 || result?.result) && (
          <div className="mt-8 p-6 bg-gray-950/80 border border-gray-800 rounded-3xl animate-in fade-in duration-500">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-black text-white flex items-center gap-3">
                <span className="flex items-center justify-center w-8 h-8 bg-indigo-600/20 rounded-lg">
                  🎬
                </span>
                镜头拆解时间轴
              </h2>
              {isAnalyzing && (
                <span className="px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full text-xs text-green-400 font-bold animate-pulse">
                  实时更新中
                </span>
              )}
            </div>
            {renderTimeline()}
          </div>
        )}

        {/* 历史记录界面 */}
        {activeTab === 'history' && (
          <div className="space-y-6">
            {history.length === 0 ? (
              <div className="text-center py-20 text-gray-500">
                <History size={48} className="mx-auto mb-4 opacity-20" />
                <p>暂无历史记录</p>
              </div>
            ) : (
              <>
                {/* 提示信息 */}
                <div className="p-4 bg-indigo-500/5 border border-indigo-500/20 rounded-2xl flex items-center gap-3">
                  <div className="p-2 bg-indigo-500/10 rounded-lg">
                    <History size={18} className="text-indigo-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-white mb-1">💡 点击任意记录查看完整分解详情</p>
                    <p className="text-xs text-gray-400">
                      历史记录包含完整的镜头时间轴、特征分析和学习要点
                    </p>
                  </div>
                </div>
                
                {history.map((item) => (
                <div
                  key={item.job_id}
                  onClick={() => handleLoadHistoryDetail(item)}
                  className="bg-gray-950/80 border border-gray-800 rounded-3xl hover:border-indigo-500/50 transition-all cursor-pointer group overflow-hidden"
                >
                  <div className="flex items-start gap-4">
                    {/* 缩略图或图标占位 */}
                    <div className="w-48 h-32 flex-shrink-0 bg-gray-900 relative overflow-hidden flex items-center justify-center">
                      {item.thumbnail_url && !failedThumbnails.has(item.job_id) ? (
                        <>
                          <img 
                            src={item.thumbnail_url.startsWith('http') ? item.thumbnail_url : `http://localhost:8000${item.thumbnail_url}`}
                            alt={item.title || '视频缩略图'}
                            className="w-full h-full object-cover opacity-70 group-hover:opacity-100 group-hover:scale-105 transition-all duration-300"
                            onError={() => {
                              // 图片加载失败时，记录到失败列表
                              setFailedThumbnails(prev => new Set(prev).add(item.job_id));
                            }}
                          />
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-gray-950/80" />
                          <Play size={24} className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/60 group-hover:text-white/90 transition-colors" />
                        </>
                      ) : (
                        <>
                          <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/20 to-gray-900" />
                          <FileVideo size={40} className="text-gray-600 group-hover:text-indigo-500 transition-colors relative z-10" />
                        </>
                      )}
                    </div>
                    
                    <div className="flex-1 p-6">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-bold group-hover:text-indigo-400 transition-colors">
                          {item.title || '未命名任务'}
                        </h3>
                        {item.status === 'succeeded' ? (
                          <span className="px-2 py-1 bg-green-500/10 border border-green-500/20 rounded-lg text-[10px] font-bold text-green-400">
                            ✓ 已完成
                          </span>
                        ) : item.status === 'failed' ? (
                          <span className="px-2 py-1 bg-red-500/10 border border-red-500/20 rounded-lg text-[10px] font-bold text-red-400">
                            ✗ 失败
                          </span>
                        ) : item.status === 'running' ? (
                          <span className="px-2 py-1 bg-blue-500/10 border border-blue-500/20 rounded-lg text-[10px] font-bold text-blue-400 animate-pulse">
                            ⟳ 进行中
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-gray-500/10 border border-gray-500/20 rounded-lg text-[10px] font-bold text-gray-400">
                            ⏳ 排队中
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                        <span>{item.segment_count || 0} 个镜头</span>
                        <span>·</span>
                        <span>{item.duration_sec?.toFixed(1) || 0} 秒</span>
                        <span>·</span>
                        <span>{new Date(item.created_at).toLocaleString()}</span>
                      </div>
                      {item.learning_points.length > 0 && (
                        <div className="space-y-1">
                          {item.learning_points.slice(0, 3).map((point, idx) => (
                            <p key={idx} className="text-sm text-gray-400 flex items-start gap-2">
                              <ChevronRight size={14} className="mt-0.5 text-indigo-400 flex-shrink-0" />
                              {point}
                            </p>
                          ))}
                          {item.learning_points.length > 3 && (
                            <p className="text-xs text-gray-600 italic pl-5">
                              还有 {item.learning_points.length - 3} 条学习要点...
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 pr-6">
                      <button
                        onClick={(e) => handleDeleteHistory(item.job_id, e)}
                        className="p-2 hover:bg-red-500/10 text-gray-500 hover:text-red-400 rounded-lg transition-colors"
                        title="删除记录"
                      >
                        <Trash2 size={16} />
                      </button>
                      <ChevronRight size={20} className="text-gray-600 group-hover:text-indigo-400 transition-colors" />
                    </div>
                  </div>
                </div>
              ))}
              </>
            )}
          </div>
        )}
      </div>

      {/* 详情面板 */}
      {renderDetailPanel()}
    </div>
  );
};

export default ShotAnalysis;

