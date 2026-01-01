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
