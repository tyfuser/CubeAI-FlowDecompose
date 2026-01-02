
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
  ShootingAssistant = 'shooting-assistant',
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
export interface ActionPayload {
  action: string;
  intention: string;
  ui_hint: 'dialogue' | 'input' | 'alert' | 'success' | 'scan';
  dialogue: string;
  reason: string;
  timestamp: number;
}

export interface SessionData {
  sessionId: string;
  startTime: number;
}

export const MOCK_ACTIONS: Omit<ActionPayload, 'timestamp'>[] = [
  {
    action: "INIT_SYSTEM",
    intention: "Establish neural link",
    ui_hint: "alert",
    dialogue: "Initializing Story Galaxy Interface... Connection stable.",
    reason: "System startup sequence initiated."
  },
  {
    action: "SCAN_SECTOR",
    intention: "Locate corrupted fragments",
    ui_hint: "scan",
    dialogue: "Scanning Sector 7... Anomalies detected in the narrative flow.",
    reason: "User entered a new zone."
  },
  {
    action: "ENCOUNTER_GLITCH",
    intention: "Present challenge",
    ui_hint: "dialogue",
    dialogue: "The Silence is overwhelming here. 'I... cannot remember the color of the rose.'",
    reason: "Narrative conflict introduction."
  },
  {
    action: "REQUEST_INPUT",
    intention: "Solicit player creativity",
    ui_hint: "input",
    dialogue: "We need a spark. What color was the rose? Transmit your memory now.",
    reason: "Interactive puzzle element."
  },
  {
    action: "RESTORE_FRAGMENT",
    intention: "Reward player action",
    ui_hint: "success",
    dialogue: "Data received. Reconstructing... It's beautiful. The sector is stabilizing.",
    reason: "Puzzle solved successfully."
  }
];


// Realtime Shooting Advisor Types

export type AdvicePriority = 'critical' | 'warning' | 'info' | 'positive';

export type AdviceCategory = 'stability' | 'speed' | 'composition' | 'beat' | 'equipment';

export interface RealtimeAdvicePayload {
  type: 'advice';
  priority: AdvicePriority;
  category: AdviceCategory;
  message: string;
  advanced_message?: string | null;
  timestamp: number;
  suppress_duration_ms: number;
  trigger_haptic: boolean;
}

export interface FrameBufferPayload {
  type: 'frames';
  session_id: string;
  frames: string[];  // Base64-encoded JPEG images
  fps: number;
  timestamp: number;
}

export interface ShootingSessionData {
  session_id: string;
  join_url: string;
  ws_url: string;
}

export interface ShootingSessionStats {
  session_id: string;
  created_at: number;
  active_clients: number;
  total_frames_received: number;
  total_advice_sent: number;
  last_heartbeat: number;
}

export interface WebSocketErrorPayload {
  type: 'error';
  code: string;
  message: string;
  recoverable: boolean;
  timestamp: number;
}
