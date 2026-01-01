
export type ProjectStatus = 'analyzing' | 'completed' | 'draft' | 'failed';

export type CreationStrategy = 'remake' | 'explainer' | 'review' | 'collection' | 'mashup';

export type TargetPlatform = 'douyin' | 'red' | 'bilibili';

export interface ProjectSummary {
  id: string;
  title: string;
  thumbnail: string;
  timestamp: string;
  type: string;
  score: number;
  status: ProjectStatus;
  tags: string[];
  radarData?: {
    subject: string;
    value: number;
    fullMark: number;
  }[];
}

export interface VideoAnalysis {
  id: string;
  title: string;
  coverUrl: string;
  duration: number;
  viralFactors: ViralFactor[];
  rhythmData: RhythmPoint[];
  radarData: {
    subject: string;
    value: number;
    fullMark: number;
  }[];
  narrativeStructure: string;
  hookScore: number;
  evaluationReport: {
    starRating: number;
    coreStrengths: string[];
    reusablePoints: string[];
  };
  hookDetails: {
    visual: string;
    audio: string;
    text: string;
  };
  editingStyle: {
    pacing: string;
    transitionType: string;
    colorPalette: string;
  };
  audienceResponse: {
    sentiment: string;
    keyTriggers: string[];
  };
}

export interface ViralFactor {
  category: string;
  description: string;
  intensity: number; // 1-10
}

export interface RhythmPoint {
  time: number;
  intensity: number;
  label?: string;
}

export interface Shot {
  id: number;
  startTime: number;
  duration: number;
  type: string;
  description: string;
  dialogue: string;
  transition: string;
  placeholderUrl?: string;
  tags?: string[];
  platformSpecific?: {
    platform: TargetPlatform;
    tip: string;
  };
}

export interface SlideData {
  id: string;
  title: string;
  summary: string;
  timestamp: string;
  imageUrl: string;
  layoutType: 'title' | 'chapter' | 'content';
}

export interface Script {
  id: string;
  title: string;
  shots: Shot[];
  strategy: CreationStrategy;
  styleProfile: {
    tone: string;
    speed: number;
    emotion: string;
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  attachments?: {
    type: 'frame';
    url: string;
    videoTimestamp: string;
  }[];
}

export enum AppSection {
  Dashboard = 'dashboard',
  Analysis = 'analysis',
  VideoSlideshow = 'slideshow',
  Discovery = 'discovery',
  Editor = 'editor',
  ShotAnalysis = 'shot-analysis',
  KnowledgeBase = 'kb',
  Settings = 'settings'
}

// ============ 视频镜头拆解分析相关类型 ============

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed';

export interface VideoSource {
  type: 'file' | 'url';
  path: string;
}

export interface AnalysisOptions {
  frame_extract?: {
    fps?: number;
    max_frames?: number;
  };
  llm?: {
    provider?: string;
    enabled_modules?: string[];
  };
}

export interface JobProgress {
  stage: string;
  percent: number;
  message: string;
}

export interface Feature {
  category: 'camera_motion' | 'lighting' | 'color_grading';
  type: string;
  value: string;
  confidence: number;
  detailed_description?: {
    summary: string;
    technical_terms: string[];
    purpose: string;
    parameters?: Record<string, any>;
  };
}

export interface Segment {
  segment_id: string;
  start_ms: number;
  end_ms: number;
  duration_ms: number;
  analyzing?: boolean;
  features: Feature[];
}

export interface AnalysisResult {
  target: {
    segments: Segment[];
  };
}

export interface VideoSourceInfo {
  source_type: string;
  source_url?: string;
  source_path?: string;
  local_path?: string;
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  status_url?: string;
  mode?: string;
  progress?: JobProgress;
  partial_result?: AnalysisResult;
  result?: AnalysisResult;
  error?: {
    code: string;
    message: string;
  };
  target_video?: VideoSourceInfo;
  user_video?: VideoSourceInfo;
}

export interface HistoryItem {
  job_id: string;
  title?: string;
  status: JobStatus;
  learning_points: string[];
  segment_count?: number;
  duration_sec?: number;
  thumbnail_url?: string;
  created_at: string;
}
