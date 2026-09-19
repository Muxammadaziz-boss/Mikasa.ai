// ========== backendService.ts ==========
// Mikasa AI 8.0.0 — Desktop Frontend to Python Backend Connector
// Connects to local aiohttp API Server at http://127.0.0.1:18420

import { supabase, isSupabaseConfigured } from "./supabaseClient";

function formatAuthError(err: any): string {
  const msg = (err && (err.message || String(err))) || "";
  if (
    msg.includes("Failed to fetch") ||
    msg.includes("NetworkError") ||
    msg.includes("ENOTFOUND") ||
    msg.includes("ERR_NAME_NOT_RESOLVED") ||
    msg.includes("fetch failed")
  ) {
    return "Supabase serveriga ulanib bo'lmadi. Internet aloqangiz yoki loyiha URL manzilini tekshiring.";
  }
  if (msg.includes("provider is not enabled") || msg.includes("Unsupported provider")) {
    return "Google orqali kirish Supabase Dashboard'da yoqilmagan. Supabase -> Authentication -> Providers bo'limida Google'ni yoqing va Client ID/Secret'ni kiriting.";
  }
  if (msg.includes("email_address_invalid") || msg.includes("Email address") && msg.includes("is invalid")) {
    return "Kiritilgan email manzili noto'g'ri yoki qabul qilinmadi. Iltimos, haqiqiy email kiriting (masalan: example@gmail.com).";
  }
  if (msg.includes("Invalid login credentials")) {
    return "Foydalanuvchi nomi yoki parol noto'g'ri.";
  }
  if (msg.includes("User already registered") || msg.includes("already registered")) {
    return "Bu foydalanuvchi yoki email bilan allaqachon ro'yxatdan o'tilgan.";
  }
  if (msg.includes("Password should be at least")) {
    return "Parol kamida 6-8 ta belgidan iborat bo'lishi kerak.";
  }
  return msg || "Autentifikatsiya jarayonida xatolik yuz berdi";
}

export interface BackendStatus {
  status: "online" | "offline" | "connecting";
  app?: string;
  version?: string;
  user?: string;
  ai_available?: boolean;
  voice_state?: "idle" | "listening" | "thinking" | "speaking";
  tools_count?: number;
  scheduled_tasks?: number;
  timestamp?: string;
}

export interface ChatResponse {
  ok: boolean;
  response: string;
  user?: string;
  mode?: string;
  timestamp?: string;
  error?: string;
}

export interface CommandItem {
  id: string;
  name: string;
  tool_name?: string;
  query: string;
  category: string;
  icon: string;
  desc: string;
  parameters?: Record<string, any>;
  is_tool?: boolean;
}

export interface CommandsResponse {
  ok: boolean;
  categories: string[];
  commands: CommandItem[];
  total_commands: number;
}

export interface KnowledgeItem {
  id?: string;
  key: string;
  value: string;
  content?: string;
  type?: "fact" | "preference" | "work_context" | "task" | "note" | string;
  source?: "user" | "conversation" | "system" | string;
  importance?: number;
  confidence?: number;
  pinned?: boolean;
  is_active?: boolean;
  saved_at?: string;
  created_at?: string;
  updated_at?: string;
  last_used_at?: string | null;
  access_count?: number;
  superseded_by?: string | null;
}

export interface MemoryPolicyConfig {
  do_not_remember_all: boolean;
  do_not_remember?: boolean;
  blocked_types: string[];
  blocked_keys: string[];
}

export interface MemoryMetrics {
  total_memories: number;
  active_memories: number;
  pinned_memories: number;
  superseded_memories: number;
  retrieval_requests_total: number;
  total_retrieval_requests?: number;
  memories_retrieved_total: number;
  average_selected_per_request: number;
  memory_hit_count: number;
  memory_hit_rate: number;
  hit_rate?: number;
  rejected_writes_total: number;
  rejected_writes_sensitive: number;
  rejected_writes_policy: number;
  deleted_items_total: number;
  user_deletions?: number;
}

export interface ContextTraceStageItem {
  stage: string;
  status: string;
  duration_ms: number;
  details: Record<string, any>;
  data?: Record<string, any>;
}

export interface ContextTraceItem {
  trace_id: string;
  query?: string;
  timestamp: string;
  total_duration_ms: number;
  duration_ms?: number;
  stage_count: number;
  stages: ContextTraceStageItem[];
  success?: boolean;
}

export interface ContextTurn {
  role: string;
  content: string;
  time: string;
}

export interface MemoryResponse {
  ok: boolean;
  profile: Record<string, any>;
  knowledge: KnowledgeItem[];
  conversations: Array<{ user: string; agent: string; time: string }>;
  context?: ContextTurn[];
  stats: {
    kontekst_hajmi?: number;
    suhbatlar_soni?: number;
    bilimlar_soni?: number;
    faol_bilimlar_soni?: number;
    pinned_bilimlar_soni?: number;
    profil_toliq?: boolean;
  };
}

export type TaskStatus = "active" | "completed" | "repeating" | "failed" | "cancelled";

export interface ScheduledTaskItem {
  id: string;
  task_id?: string;
  type: string;
  task_type?: string;
  run_at: string;
  run_at_iso?: string;
  data: { text?: string; [key: string]: any };
  completed: boolean;
  enabled: boolean;
  cancelled?: boolean;
  repeat: boolean;
  repeat_seconds?: number;
  last_run?: string | null;
  last_error?: string | null;
  status: TaskStatus;
  created_at?: string;
}

export interface SchedulerResponse {
  ok: boolean;
  tasks: ScheduledTaskItem[];
  active_count: number;
}

export type PluginStatus = "installed" | "available" | "disabled" | "error" | "updates";

export interface PluginItem {
  id?: string;
  name: string;
  description: string;
  parameters: Record<string, any>;
  category: string;
  enabled: boolean;
  version: string;
  status: PluginStatus;
  type?: "builtin" | "json" | "python" | "url" | "command";
  author?: string;
  error?: string;
  has_update?: boolean;
  file_name?: string;
  capabilities?: string[];
  required_parameters?: string[];
  risk_level?: "low" | "medium" | "high";
  timeout?: number;
  idempotent?: boolean;
  destructive?: boolean;
  aliases?: string[];
  health?: "available" | "unavailable" | "degraded" | "disabled";
  metrics?: {
    success_count?: number;
    failure_count?: number;
    last_duration_ms?: number;
    last_executed?: string;
  };
}

export interface PluginStats {
  total: number;
  installed: number;
  available: number;
  disabled: number;
  error: number;
  updates: number;
}

export interface PluginsResponse {
  ok: boolean;
  plugins?: PluginItem[];
  tools?: PluginItem[];
  stats?: PluginStats;
  total_count: number;
  categories: string[];
}

export interface AccountNotificationSettings {
  scheduler: boolean;
  voice: boolean;
  sound_effects: boolean;
  system_status: boolean;
}

export interface AccountPrivacySettings {
  local_storage_only: boolean;
  telemetry_disabled: boolean;
  save_conversations: boolean;
}

export interface AccountAppInfo {
  name: string;
  version: string;
  codename: string;
  engine: string;
  architecture: string;
  developer: string;
  license?: string;
}

export interface AccountSettings {
  ok: boolean;
  name: string;
  avatar?: string;
  role?: string;
  bio?: string;
  language?: string;
  voice_type: "ayol" | "erkak";
  tts_speed: number;
  tts_engine?: string;
  auto_speak?: boolean;
  vad_enabled?: boolean;
  theme: string;
  color_scheme?: string;
  animations?: boolean;
  compact_mode?: boolean;
  glassmorphism?: boolean;
  ai_model: string;
  ai_mode?: string;
  thinking_enabled?: boolean;
  has_gemini_key?: boolean;
  version: string;
  app_info?: AccountAppInfo;
  notifications?: AccountNotificationSettings;
  privacy?: AccountPrivacySettings;
  voices_available: Array<{ id: string; name: string; lang: string; desc?: string }>;
  ai_models_available?: Array<{ id: string; name: string; provider: string; badge: string; desc: string }>;
}

export type VoiceState =
  | "idle"
  | "listening"
  | "thinking"
  | "planning"
  | "acting"
  | "verifying"
  | "replanning"
  | "speaking"
  | "completed"
  | "error";

export interface SystemMetrics {
  ok?: boolean;
  cpu_percent: number;
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  disk_percent: number;
  disk_free_gb?: number;
  network_sent_kb: number;
  network_recv_kb: number;
  upload_mb_s?: number;
  download_mb_s?: number;
  gpu_percent?: number;
  cpu_temp?: number;
  battery_percent?: number | null;
  battery_plugged?: boolean | null;
  timestamp: string;
}

export interface PlanStepData {
  step_id: string;
  order: number;
  intent: string;
  tool: string;
  selected_tool?: string;
  description?: string;
  purpose?: string;
  dependencies?: string[];
  required_capability?: string;
  parameters: Record<string, any>;
  expected_result?: string;
  risk_level: "low" | "medium" | "high";
  status: "pending" | "running" | "completed" | "failed" | "skipped" | "waiting_confirmation";
  retry_count: number;
  max_retries: number;
  observed_result?: any;
  verification_policy?: string;
  failure_reason?: string;
  verification?: {
    verified: boolean;
    status: "success" | "failure" | "unknown";
    reason: string;
    details: Record<string, any>;
  };
  error?: string;
}

export interface AgentPlanData {
  plan_id: string;
  goal: string;
  intent?: string;
  desired_outcome?: string;
  assumptions?: string[];
  constraints?: string[];
  steps: PlanStepData[];
  dependencies?: Record<string, string[]>;
  execution_order?: string[];
  required_capabilities?: string[];
  risk_level?: "low" | "medium" | "high";
  status: "pending" | "running" | "paused" | "completed" | "failed" | "aborted";
  created_at?: string;
  updated_at?: string;
  current_step_index: number;
  max_steps: number;
  plan_version?: number;
  replan_count?: number;
  max_replans?: number;
  replan_history?: Array<{
    version: number;
    reason: string;
    timestamp: string;
    changed_steps: string[];
  }>;
  metadata?: Record<string, any>;
}

export interface AgentExecutionStateData {
  state: string;
  current_plan?: AgentPlanData | null;
  completed_steps: PlanStepData[];
  failed_steps: PlanStepData[];
  active_step?: PlanStepData | null;
  total_execution_time: number;
  trace_id?: string | null;
}

export interface AgentEventData {
  type: string;
  data: Record<string, any>;
  timestamp?: string;
}

// ========== Phase 38 Remote Control & Permissions Interfaces ==========
export interface RemoteDevice {
  device_id: string;
  hostname: string;
  os: string;
  mac_address: string;
  local_ip: string;
  state: "online" | "offline" | "waking" | "unknown";
  agent_version: string;
  is_paired: boolean;
  telegram_user_id?: string | null;
  permissions?: Record<string, boolean>;
}

export interface PermissionDefinitionItem {
  id: string;
  category: "system" | "apps" | "files" | "network" | "power" | "advanced";
  name: string;
  description: string;
  danger_level: "low" | "medium" | "high" | "critical";
  requires_confirmation: boolean;
}

export interface PermissionProfileData {
  user_id: string;
  device_id: string;
  permissions: Record<string, boolean>;
  capabilities: string[];
  version: number;
  updated_at: number;
}

export interface PairingCodeResponse {
  ok: boolean;
  code?: string;
  expires_in?: number;
  instruction?: string;
  error?: string;
}

export interface RemoteAuditItem {
  event_id: string;
  timestamp: string;
  event_type: string;
  telegram_user_id?: string;
  device_id?: string;
  status: string;
  details?: Record<string, any>;
}

const API_BASE = "http://127.0.0.1:18420";
const WS_BASE = "ws://127.0.0.1:18420/api/ws";

class BackendService {
  private ws: WebSocket | null = null;
  private wsReconnectTimer: number | null = null;
  private isConnectingWs = false;
  private currentStatus: BackendStatus = { status: "connecting" };
  private currentVoiceState: VoiceState = "idle";

  private statusListeners: Set<(status: BackendStatus) => void> = new Set();
  private voiceStateListeners: Set<(state: VoiceState) => void> = new Set();
  private responseListeners: Set<(data: { text: string; mode: string }) => void> = new Set();
  private alarmListeners: Set<(data: { id: string; text: string; type: string }) => void> = new Set();
  private transcriptListeners: Set<(data: { text: string; sender: "user" | "mikasa" }) => void> = new Set();
  private accountListeners: Set<(data: any) => void> = new Set();
  private agentListeners: Set<(event: AgentEventData) => void> = new Set();
  private metricsListeners: Set<(metrics: SystemMetrics) => void> = new Set();
  private remoteListeners: Set<(event: { type: string; data: any }) => void> = new Set();
  private generalListeners: Set<(event: any) => void> = new Set();
  private authListeners: Set<(user: MikasaAuthUser | null) => void> = new Set();
  private clientVoiceStopFn: (() => void) | null = null;
  private authToken: string | null = null;

  constructor() {
    this.authToken = this.getAuthToken();
    this.connectWs();
    this.startHealthPolling();
  }

  // ========== Listeners ==========
  public subscribe(cb: (event: any) => void): () => void {
    this.generalListeners.add(cb);
    return () => this.generalListeners.delete(cb);
  }

  public onStatusChange(cb: (status: BackendStatus) => void): () => void {
    this.statusListeners.add(cb);
    cb(this.currentStatus);
    return () => this.statusListeners.delete(cb);
  }

  public onAccountChange(cb: (data: any) => void): () => void {
    this.accountListeners.add(cb);
    return () => this.accountListeners.delete(cb);
  }

  public onVoiceStateChange(cb: (state: VoiceState) => void): () => void {
    this.voiceStateListeners.add(cb);
    cb(this.currentVoiceState);
    return () => this.voiceStateListeners.delete(cb);
  }

  public onResponse(cb: (data: { text: string; mode: string }) => void): () => void {
    this.responseListeners.add(cb);
    return () => this.responseListeners.delete(cb);
  }

  public onSchedulerAlarm(cb: (data: { id: string; text: string; type: string }) => void): () => void {
    this.alarmListeners.add(cb);
    return () => this.alarmListeners.delete(cb);
  }

  public onTranscript(cb: (data: { text: string; sender: "user" | "mikasa" }) => void): () => void {
    this.transcriptListeners.add(cb);
    return () => this.transcriptListeners.delete(cb);
  }

  public onAgentEvent(cb: (event: AgentEventData) => void): () => void {
    this.agentListeners.add(cb);
    return () => this.agentListeners.delete(cb);
  }

  public onSystemMetrics(cb: (metrics: SystemMetrics) => void): () => void {
    this.metricsListeners.add(cb);
    return () => this.metricsListeners.delete(cb);
  }

  public onRemoteEvent(cb: (event: { type: string; data: any }) => void): () => void {
    this.remoteListeners.add(cb);
    return () => this.remoteListeners.delete(cb);
  }

  public onWsMessage(cb: (event: { type: string; data?: any }) => void): () => void {
    this.remoteListeners.add(cb);
    return () => this.remoteListeners.delete(cb);
  }

  private notifyStatus(status: BackendStatus) {
    this.currentStatus = status;
    this.statusListeners.forEach((cb) => {
      try {
        cb(status);
      } catch (err) {
        console.error("Error in status listener", err);
      }
    });
  }

  private notifyVoiceState(state: VoiceState) {
    this.currentVoiceState = state;
    this.voiceStateListeners.forEach((cb) => {
      try {
        cb(state);
      } catch (err) {
        console.error("Error in voice listener", err);
      }
    });
  }

  // ========== WebSocket Connection ==========
  private connectWs() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    if (this.isConnectingWs) return;
    this.isConnectingWs = true;
    try {
      this.ws = new WebSocket(WS_BASE);

      this.ws.onopen = () => {
        this.isConnectingWs = false;
        this.notifyStatus({ ...this.currentStatus, status: "online" });
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.generalListeners.forEach((cb) => {
            try {
              cb(payload);
            } catch (e) {
              console.error(e);
            }
          });
          if (payload.type === "voice_state" && payload.data?.state) {
            this.notifyVoiceState(payload.data.state);
          } else if (payload.type === "ai_response" && payload.data?.text) {
            this.responseListeners.forEach((cb) => {
              try {
                cb(payload.data);
              } catch (e) {
                console.error(e);
              }
            });
          } else if (payload.type === "scheduler_alarm" && payload.data) {
            this.alarmListeners.forEach((cb) => {
              try {
                cb(payload.data);
              } catch (e) {
                console.error(e);
              }
            });
          } else if (payload.type === "voice_transcript" && payload.data?.text) {
            this.transcriptListeners.forEach((cb) => {
              try {
                cb(payload.data);
              } catch (e) {
                console.error(e);
              }
            });
          } else if (payload.type && payload.type.startsWith("agent_")) {
            this.agentListeners.forEach((cb) => {
              try {
                cb({ type: payload.type, data: payload.data || {}, timestamp: payload.timestamp });
              } catch (e) {
                console.error("Error in agent listener", e);
              }
            });
          } else if (payload.type === "account_updated" && payload.data) {
            if (payload.data.name) {
              try {
                localStorage.setItem("mikasa_user_name", payload.data.name);
              } catch {}
              this.notifyStatus({ ...this.currentStatus, user: payload.data.name });
            }
            if (payload.data.avatar) {
              try {
                localStorage.setItem("mikasa_user_avatar", payload.data.avatar);
              } catch {}
            }
            this.accountListeners.forEach((cb) => {
              try {
                cb(payload.data);
              } catch (e) {
                console.error(e);
              }
            });
          } else if (payload.type === "system_metrics" && payload.data) {
            this.metricsListeners.forEach((cb) => {
              try {
                cb(payload.data);
              } catch (e) {
                console.error(e);
              }
            });
          } else if (
            [
              "permission_changed", "pairing_code_generated", "device_paired", "device_unpaired",
              "session_locked", "session_logout",
              "PAIRING_CREATED", "PAIRING_WAITING", "PAIRING_VERIFIED", "PAIRING_FAILED", "PAIRING_EXPIRED",
              "TELEGRAM_CONNECTED", "TELEGRAM_DISCONNECTED",
              "DEVICE_ADDED", "DEVICE_RENAMED", "DEVICE_SELECTED", "DEVICE_REVOKED",
              "SESSION_CREATED", "SESSION_LOCKED", "SESSION_LOGOUT",
            ].includes(payload.type)
          ) {
            this.remoteListeners.forEach((cb) => {
              try {
                cb({ type: payload.type, data: payload.data || {} });
              } catch (e) {
                console.error(e);
              }
            });
          }
        } catch (e) {
          console.debug("WS parse error", e);
        }
      };

      this.ws.onerror = () => {
        this.isConnectingWs = false;
      };

      this.ws.onclose = () => {
        this.isConnectingWs = false;
        this.scheduleWsReconnect();
      };
    } catch {
      this.isConnectingWs = false;
      this.scheduleWsReconnect();
    }
  }

  private scheduleWsReconnect() {
    if (this.wsReconnectTimer) return;
    this.wsReconnectTimer = window.setTimeout(() => {
      this.wsReconnectTimer = null;
      this.connectWs();
    }, 4000);
  }

  // ========== Periodic Health Polling ==========
  private startHealthPolling() {
    this.checkStatus();
    setInterval(() => {
      this.checkStatus();
    }, 5000);
  }

  // ========== 1. STATUS & CHAT & VOICE ==========
  public async checkStatus(): Promise<BackendStatus> {
    try {
      const res = await fetch(`${API_BASE}/api/status`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error("Status HTTP " + res.status);
      const data: BackendStatus = await res.json();
      if (data.user) {
        try {
          localStorage.setItem("mikasa_user_name", data.user);
        } catch {}
      }
      this.notifyStatus(data);
      if (data.voice_state) {
        this.notifyVoiceState(data.voice_state);
      }
      return data;
    } catch {
      const cachedUser = localStorage.getItem("mikasa_user_name") || undefined;
      // Agar HTTP hali javob bermasa, Rust Tauri supervisoridan xizmat ishga tushayotganini tekshirish
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        const tauriStatus = await invoke<{ running: boolean; port: number; pid?: number; managed: boolean }>("backend_get_status");
        if (tauriStatus && tauriStatus.managed && !tauriStatus.running) {
          const connectingStatus: BackendStatus = { status: "connecting", user: cachedUser };
          this.notifyStatus(connectingStatus);
          return connectingStatus;
        }
      } catch {}

      const offlineStatus: BackendStatus = { status: "offline", user: cachedUser };
      this.notifyStatus(offlineStatus);
      return offlineStatus;
    }
  }

  public async restartBackend(): Promise<boolean> {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      return await invoke<boolean>("backend_restart");
    } catch {
      return false;
    }
  }

  public async sendChat(
    text: string,
    mode: "ask" | "command" | "summary" = "ask"
  ): Promise<ChatResponse> {
    this.notifyVoiceState("thinking");
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, mode }),
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || "Chat xatoligi: " + res.status);
      }
      const data: ChatResponse = await res.json();
      this.notifyVoiceState("idle");
      return data;
    } catch (err: any) {
      this.notifyVoiceState("idle");
      return {
        ok: false,
        response: "Backend bilan bog'lanishda xatolik: " + (err.message || String(err)),
        error: String(err),
      };
    }
  }

  public async startVoice(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/voice/start`, { method: "POST" });
      if (res.ok) {
        this.notifyVoiceState("listening");
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  public async stopVoice(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/voice/stop`, { method: "POST" });
      if (res.ok) {
        this.notifyVoiceState("idle");
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  // ========== Real System Metrics ==========
  public async getSystemMetrics(): Promise<SystemMetrics | null> {
    try {
      const res = await fetch(`${API_BASE}/api/system/metrics`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  // ========== Voice AI Client-Side Microphone & Web Speech ==========
  public async startClientVoice(
    onTranscript: (text: string, isFinal: boolean) => void,
    onError: (err: string) => void,
    onAudioLevelOrState?: ((level: number) => void) | ((state: VoiceState) => void)
  ): Promise<(() => void) | null> {
    // 1. Microphone permission check
    try {
      if (navigator?.mediaDevices?.getUserMedia) {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }
    } catch {
      const errMsg = "Tovushli boshqaruv uchun mikrofon ruxsati kerak.";
      onError(errMsg);
      if (typeof onAudioLevelOrState === "function" && onAudioLevelOrState.length === 1) {
        try { (onAudioLevelOrState as any)("error"); } catch {}
      }
      return null;
    }

    // 2. Web Speech Recognition check
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      // Fallback to backend voice recognition
      try {
        const started = await this.startVoice();
        if (started) {
          if (typeof onAudioLevelOrState === "function") {
            try { (onAudioLevelOrState as any)("listening"); } catch {}
          }
          const stopper = () => this.stopVoice();
          this.clientVoiceStopFn = stopper;
          return stopper;
        }
        onError("Ovozli boshqaruvni ishga tushirib bo'lmadi.");
        return null;
      } catch {
        onError("Ovozli boshqaruvni ishga tushirib bo'lmadi.");
        return null;
      }
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "uz-UZ";
      recognition.continuous = false;
      recognition.interimResults = true;

      recognition.onstart = () => {
        this.notifyVoiceState("listening");
        if (typeof onAudioLevelOrState === "function") {
          try { (onAudioLevelOrState as any)("listening"); } catch {}
        }
      };

      recognition.onresult = (event: any) => {
        let interim = "";
        let final = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        if (final) {
          onTranscript(final.trim(), true);
        } else if (interim) {
          onTranscript(interim.trim(), false);
        }
      };

      recognition.onerror = (event: any) => {
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
          onError("Tovushli boshqaruv uchun mikrofon ruxsati kerak.");
        } else if (event.error !== "no-speech") {
          onError(`Ovozni tinglashda xatolik: ${event.error}`);
        }
        this.notifyVoiceState("idle");
      };

      recognition.onend = () => {
        this.notifyVoiceState("idle");
      };

      recognition.start();

      const stopper = () => {
        try {
          recognition.stop();
        } catch {}
      };
      this.clientVoiceStopFn = stopper;
      return stopper;
    } catch {
      onError("Ovozli boshqaruvni ishga tushirib bo'lmadi.");
      return null;
    }
  }

  public stopClientVoice(): void {
    if (this.clientVoiceStopFn) {
      try {
        this.clientVoiceStopFn();
      } catch {}
      this.clientVoiceStopFn = null;
    }
    this.stopVoice();
    this.notifyVoiceState("idle");
  }

  // ========== AgentLoop 2.0 Integration ==========
  public async executeAgent(goal: string): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/agent/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal }),
      });
      return await res.json();
    } catch (e: any) {
      return { ok: false, error: e.message || "Agent ijrosi amalga oshmadi" };
    }
  }

  public async confirmAgentStep(planId: string, stepId: string, approve: boolean): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/agent/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId, step_id: stepId, approve }),
      });
      return await res.json();
    } catch (e: any) {
      return { ok: false, error: e.message || "Tasdiqlashda xatolik" };
    }
  }

  public async abortAgent(planId?: string): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/agent/abort`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId }),
      });
      return await res.json();
    } catch (e: any) {
      return { ok: false, error: e.message || "To'xtatishda xatolik" };
    }
  }

  public async clearChat(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/chat/clear`, { method: "POST" });
      return res.ok;
    } catch {
      return false;
    }
  }

  // ========== 2. BUYRUQLAR (COMMANDS) ==========
  public async getCommands(): Promise<CommandsResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/commands`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch {
      return {
        ok: false,
        categories: ["Barchasi", "Ilovalar", "Tizim", "Multimedia", "Ovoz"],
        commands: [],
        total_commands: 0,
      };
    }
  }

  public async executeCommand(
    command: string,
    parameters?: Record<string, any>
  ): Promise<{ ok: boolean; result: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/commands/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command, parameters }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch (err: any) {
      return { ok: false, result: "Xatolik yuz berdi: " + (err.message || String(err)) };
    }
  }

  // ========== 3. XOTIRA (MEMORY) ==========
  public async getMemory(): Promise<MemoryResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/memory`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch {
      return {
        ok: false,
        profile: {},
        knowledge: [],
        conversations: [],
        stats: {},
      };
    }
  }

  public async saveKnowledge(
    key: string,
    value: string,
    type?: string,
    importance?: number,
    pinned?: boolean
  ): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/knowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value, type, importance, pinned }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async deleteKnowledge(key: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/knowledge?key=${encodeURIComponent(key)}`, {
        method: "DELETE",
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async updateKnowledgeItem(
    id: string,
    data: { key?: string; value?: string; content?: string; type?: string; importance?: number; pinned?: boolean }
  ): Promise<{ ok: boolean; message?: string; item?: KnowledgeItem; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/knowledge/${encodeURIComponent(id)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: err.message || "Ulanish xatosi" };
    }
  }

  public async deleteKnowledgeItem(idOrKey: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/knowledge/${encodeURIComponent(idOrKey)}`, {
        method: "DELETE",
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async togglePinKnowledge(idOrKey: string, pinned: boolean): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/pin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: idOrKey, pinned }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async getMemoryPolicy(): Promise<MemoryPolicyConfig> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/policy`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      return data.policy || { do_not_remember_all: false, blocked_types: [], blocked_keys: [] };
    } catch {
      return { do_not_remember_all: false, blocked_types: [], blocked_keys: [] };
    }
  }

  public async saveMemoryPolicy(config: Partial<MemoryPolicyConfig>): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/policy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async getMemoryMetrics(): Promise<MemoryMetrics | null> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/metrics`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      return data.metrics || null;
    } catch {
      return null;
    }
  }

  public async getContextTraces(): Promise<ContextTraceItem[]> {
    try {
      const res = await fetch(`${API_BASE}/api/context/traces`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      return data.traces || [];
    } catch {
      return [];
    }
  }

  public async getLastContextTrace(): Promise<ContextTraceItem | null> {
    try {
      const res = await fetch(`${API_BASE}/api/context/last-trace`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      return data.trace || null;
    } catch {
      return null;
    }
  }

  public async saveProfile(data: Record<string, any>): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async clearKnowledge(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/knowledge/clear`, {
        method: "POST",
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async clearContext(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/context/clear`, {
        method: "POST",
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async clearHistory(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/history/clear`, {
        method: "POST",
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  // ========== 4. REJALASHTIRUVCHI (SCHEDULER) ==========
  public async getScheduler(): Promise<SchedulerResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/scheduler`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch {
      return { ok: false, tasks: [], active_count: 0 };
    }
  }

  public async addSchedulerTask(
    text: string,
    delayMinutes = 15,
    repeatMinutes = 0,
    type = "reminder"
  ): Promise<{ ok: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/scheduler/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, delay_minutes: delayMinutes, repeat_minutes: repeatMinutes, type }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, message: String(err) };
    }
  }

  public async editSchedulerTask(
    taskId: string,
    text?: string,
    delayMinutes?: number,
    repeatMinutes?: number
  ): Promise<{ ok: boolean; message?: string }> {
    try {
      const body: Record<string, any> = { task_id: taskId };
      if (text !== undefined) body.text = text;
      if (delayMinutes !== undefined) body.delay_minutes = delayMinutes;
      if (repeatMinutes !== undefined) body.repeat_minutes = repeatMinutes;

      const res = await fetch(`${API_BASE}/api/scheduler/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, message: String(err) };
    }
  }

  public async enableSchedulerTask(taskId: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/scheduler/enable`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async disableSchedulerTask(taskId: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/scheduler/disable`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async executeSchedulerTask(taskId: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/scheduler/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async removeSchedulerTask(taskId: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/scheduler/task?task_id=${encodeURIComponent(taskId)}`, {
        method: "DELETE",
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async clearCompletedTasks(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/scheduler/clear-completed`, {
        method: "POST",
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  // ========== 5. PLAGINLAR VA TOOLS ==========
  public async getPlugins(): Promise<PluginsResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/plugins`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch {
      return { ok: false, tools: [], plugins: [], total_count: 0, categories: [] };
    }
  }

  public async getToolsCatalog(): Promise<{ ok: boolean; version?: string; total_tools?: number; tools?: PluginItem[]; capabilities?: Record<string, string[]> }> {
    try {
      const res = await fetch(`${API_BASE}/api/tools/catalog`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch {
      return { ok: false, tools: [], capabilities: {} };
    }
  }

  public async togglePlugin(name: string, enabled: boolean): Promise<{ ok: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/plugins/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, enabled }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, message: String(err) };
    }
  }

  public async installPlugin(name: string, data?: any): Promise<{ ok: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/plugins/install`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, data }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, message: String(err) };
    }
  }

  public async uninstallPlugin(name: string): Promise<{ ok: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/plugins/uninstall`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, message: String(err) };
    }
  }

  public async updatePlugin(name: string): Promise<{ ok: boolean; message?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/plugins/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, message: String(err) };
    }
  }

  public async executePlugin(name: string, params: Record<string, any> = {}): Promise<any> {
    try {
      const res = await fetch(`${API_BASE}/api/plugins/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, params }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  // ========== 6. HISOB VA SOZLAMALAR ==========
  public async getAccount(): Promise<AccountSettings> {
    const cachedName = localStorage.getItem("mikasa_user_name") || "Ustoz";
    try {
      const res = await fetch(`${API_BASE}/api/account`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data: AccountSettings = await res.json();
      if (data.name) {
        try {
          localStorage.setItem("mikasa_user_name", data.name);
        } catch {}
      }
      return data;
    } catch {
      return {
        ok: false,
        name: cachedName,
        voice_type: "ayol",
        theme: "dark",
        tts_speed: 2.0,
        ai_model: "gemini",
        version: "8.0.0",
        voices_available: [
          { id: "ayol", name: "Madina (Ayol)", lang: "uz-UZ-MadinaNeural" },
          { id: "erkak", name: "Sardor (Erkak)", lang: "uz-UZ-SardorNeural" },
        ],
      };
    }
  }

  public async speakText(text: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/voice/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      return res.ok;
    } catch {
      return false;
    }
  }

  public async updateAccount(
    data: Partial<AccountSettings> & { gemini_api_key?: string }
  ): Promise<{ ok: boolean; message: string; [key: string]: any }> {
    if (data.name) {
      try {
        localStorage.setItem("mikasa_user_name", data.name);
      } catch {}
      this.currentStatus.user = data.name;
      this.notifyStatus({ ...this.currentStatus, user: data.name });
    }
    if (data.avatar) {
      try {
        localStorage.setItem("mikasa_user_avatar", data.avatar);
      } catch {}
    }
    try {
      const res = await fetch(`${API_BASE}/api/account`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const result = await res.json();
      if (result.name) {
        try {
          localStorage.setItem("mikasa_user_name", result.name);
        } catch {}
        this.currentStatus.user = result.name;
        this.notifyStatus({ ...this.currentStatus, user: result.name });
      }
      if (result.avatar) {
        try {
          localStorage.setItem("mikasa_user_avatar", result.avatar);
        } catch {}
      }
      return result;
    } catch (err: any) {
      return { ok: false, message: String(err) };
    }
  }

  // ========== Agentic Multi-Step Intelligence ==========
  public async executeAgentGoal(
    goal: string
  ): Promise<{ ok: boolean; type?: string; content?: string; plan?: AgentPlanData; metadata?: any; error_code?: string; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/agent/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async abortAgentPlan(planId?: string): Promise<{ ok: boolean; message: string }> {
    return this.abortAgent(planId);
  }

  public async getSchedulerTasks(): Promise<SchedulerResponse> {
    return this.getScheduler();
  }

  public async getAgentState(): Promise<{ ok: boolean; state: string; execution: AgentExecutionStateData; timestamp?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/agent/state`, { method: "GET" });
      return await res.json();
    } catch (err: any) {
      return { ok: false, state: "error", execution: {} as any };
    }
  }

  public getStatus(): BackendStatus {
    return this.currentStatus;
  }

  public getUserName(): string {
    return this.currentStatus.user || localStorage.getItem("mikasa_user_name") || "Ustoz";
  }

  // ========== Phase 38: Masofaviy Boshqaruv & Ruxsatlar Markazi ==========
  public async getRemoteDevices(): Promise<{ ok: boolean; devices: RemoteDevice[]; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/remote/devices`);
      return await res.json();
    } catch (err: any) {
      return { ok: false, devices: [], error: String(err) };
    }
  }

  public async getDevicePermissions(deviceId: string, userId?: string): Promise<DevicePermissionsResponse> {
    try {
      const url = userId
        ? `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}/permissions?user_id=${encodeURIComponent(userId)}`
        : `${API_BASE}/api/remote/permissions/${encodeURIComponent(deviceId)}`;
      const res = await fetch(url);
      return await res.json();
    } catch (err: any) {
      return { ok: false, device_id: deviceId, profile: {} as any, catalog: {}, error: String(err) };
    }
  }

  public async updateDevicePermissions(
    deviceId: string,
    permissions: Record<string, boolean>,
    capabilities?: string[]
  ): Promise<{ ok: boolean; message?: string; profile?: PermissionProfileData; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/remote/permissions/${deviceId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ permissions, capabilities }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async generatePairingCode(deviceId: string = "local_pc"): Promise<PairingCodeResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/remote/pair`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "generate", device_id: deviceId }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async unpairTelegram(deviceId: string): Promise<{ ok: boolean; message?: string; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/remote/unpair`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async lockRemoteSession(deviceId: string): Promise<{ ok: boolean; message?: string; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/remote/session/lock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async logoutRemoteSession(deviceId: string): Promise<{ ok: boolean; message?: string; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/remote/session/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async getRemoteAudit(): Promise<{ ok: boolean; total: number; events: RemoteAuditItem[]; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/remote/audit`);
      return await res.json();
    } catch (err: any) {
      return { ok: false, total: 0, events: [], error: String(err) };
    }
  }

  // ========== Phase 39: Universal Telegram Identity & OTP Linking API ==========

  public async startTelegramLink(mikasaUserId: string = "admin"): Promise<TelegramLinkStartResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/telegram/link/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mikasa_user_id: mikasaUserId }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async verifyTelegramLink(
    otp: string,
    telegramUserId: number,
    username?: string,
    firstName?: string,
    requestId?: string
  ): Promise<TelegramLinkVerifyResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/telegram/link/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          otp,
          telegram_user_id: telegramUserId,
          username,
          first_name: firstName,
          request_id: requestId,
        }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async getTelegramLinkStatus(
    requestId?: string,
    mikasaUserId: string = "admin"
  ): Promise<TelegramLinkStatusResponse> {
    try {
      const params = new URLSearchParams();
      if (requestId) params.append("request_id", requestId);
      if (mikasaUserId) params.append("mikasa_user_id", mikasaUserId);
      const res = await fetch(`${API_BASE}/api/telegram/link/status?${params.toString()}`);
      return await res.json();
    } catch (err: any) {
      return { ok: false, status: "ERROR", is_linked: false, error: String(err) };
    }
  }

  public async unlinkTelegramAccount(
    mikasaUserId: string = "admin",
    telegramUserId?: number
  ): Promise<{ ok: boolean; message?: string; error?: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/telegram/unlink`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mikasa_user_id: mikasaUserId, telegram_user_id: telegramUserId }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async getTelegramAccount(mikasaUserId: string = "admin"): Promise<TelegramAccountResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/telegram/account?mikasa_user_id=${encodeURIComponent(mikasaUserId)}`);
      return await res.json();
    } catch (err: any) {
      return { ok: false, is_linked: false, error: String(err) };
    }
  }

  public async getTelegramBotStatus(): Promise<TelegramBotStatusResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/telegram/status`);
      return await res.json();
    } catch (err: any) {
      return {
        ok: false,
        configured: false,
        bot_username: "MikasaUniversalBot",
        active_links_count: 0,
        pending_requests_count: 0,
        error: String(err),
      };
    }
  }

  // ==========================================
  // Phase 40: Universal Account & Device Management
  // ==========================================

  public async getDevices(userId?: string): Promise<DevicesListResponse> {
    try {
      const url = userId ? `${API_BASE}/api/devices?user_id=${encodeURIComponent(userId)}` : `${API_BASE}/api/devices`;
      const res = await fetch(url);
      return await res.json();
    } catch (err: any) {
      return { ok: false, devices: [], error: String(err) };
    }
  }

  public async getDevice(deviceId: string, userId?: string): Promise<DeviceDetailResponse> {
    try {
      const url = userId
        ? `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}?user_id=${encodeURIComponent(userId)}`
        : `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}`;
      const res = await fetch(url);
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async renameDevice(deviceId: string, name: string, userId?: string): Promise<DeviceRenameResponse> {
    try {
      const url = userId
        ? `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}?user_id=${encodeURIComponent(userId)}`
        : `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}`;
      const res = await fetch(url, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async revokeDevice(deviceId: string, userId?: string): Promise<{ ok: boolean; message?: string; error?: string }> {
    try {
      const url = userId
        ? `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}?user_id=${encodeURIComponent(userId)}`
        : `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}`;
      const res = await fetch(url, { method: "DELETE" });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async selectDevice(deviceId: string, userId?: string): Promise<DeviceSelectResponse> {
    try {
      const url = userId
        ? `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}/select?user_id=${encodeURIComponent(userId)}`
        : `${API_BASE}/api/devices/${encodeURIComponent(deviceId)}/select`;
      const res = await fetch(url, { method: "POST" });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  public async getAccountSessions(userId?: string): Promise<AccountSessionsResponse> {
    try {
      const url = userId ? `${API_BASE}/api/account/sessions?user_id=${encodeURIComponent(userId)}` : `${API_BASE}/api/account/sessions`;
      const res = await fetch(url);
      return await res.json();
    } catch (err: any) {
      return { ok: false, sessions: [], total: 0, error: String(err) };
    }
  }

  public async logoutAllSessions(userId?: string): Promise<{ ok: boolean; message?: string; terminated_count?: number; error?: string }> {
    try {
      const url = userId
        ? `${API_BASE}/api/account/sessions/logout-all?user_id=${encodeURIComponent(userId)}`
        : `${API_BASE}/api/account/sessions/logout-all`;
      const res = await fetch(url, { method: "POST" });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: String(err) };
    }
  }

  // ========== Phase 41: Account Registration & Authentication ==========
  public setAuthToken(token: string | null) {
    this.authToken = token;
    try {
      if (token) {
        localStorage.setItem("mikasa_session_token", token);
      } else {
        localStorage.removeItem("mikasa_session_token");
      }
    } catch {}
  }

  public getAuthToken(): string | null {
    if (!this.authToken && typeof window !== "undefined") {
      try {
        this.authToken = localStorage.getItem("mikasa_session_token");
      } catch {}
    }
    return this.authToken;
  }

  public getAuthHeaders(): Record<string, string> {
    const token = this.getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  public onAuthChange(cb: (user: MikasaAuthUser | null) => void): () => void {
    this.authListeners.add(cb);
    return () => this.authListeners.delete(cb);
  }

  private notifyAuthChange(user: MikasaAuthUser | null) {
    this.authListeners.forEach((cb) => {
      try {
        cb(user);
      } catch (err) {
        console.error("Error in auth listener", err);
      }
    });
  }

  public async register(payload: {
    username: string;
    password: string;
    email?: string;
    confirm_password?: string;
  }): Promise<AuthResponse> {
    if (!isSupabaseConfigured) {
      return {
        ok: false,
        error: "Supabase konfiguratsiyasi topilmadi. Iltimos, .env faylida VITE_SUPABASE_URL va VITE_SUPABASE_ANON_KEY ni sozlang.",
      };
    }
    try {
      const email = payload.email || `${payload.username.toLowerCase()}@mikasa.local`;
      const { data, error } = await supabase.auth.signUp({
        email: email,
        password: payload.password,
        options: {
          data: {
            username: payload.username,
            display_name: payload.username,
          },
        },
      });

      if (error) {
        return { ok: false, error: formatAuthError(error) };
      }

      const sessionToken = data.session?.access_token || "";
      if (sessionToken) {
        this.setAuthToken(sessionToken);
      }

      const user: MikasaAuthUser | undefined = data.user
        ? {
            id: data.user.id,
            username: payload.username,
            email: data.user.email || email,
            is_active: true,
            is_verified: Boolean(data.user.email_confirmed_at),
            created_at: Date.now() / 1000,
          }
        : undefined;

      if (user && sessionToken) {
        this.notifyAuthChange(user);
      }

      return {
        ok: true,
        message: data.session
          ? "Akkaunt muvaffaqiyatli yaratildi!"
          : "Hisob yaratildi! Iltimos, email manzilingizga yuborilgan tasdiqlash xatini tekshiring.",
        user,
        session_token: sessionToken,
        expires_at: data.session?.expires_at,
      };
    } catch (err: any) {
      return { ok: false, error: formatAuthError(err) };
    }
  }

  public async login(payload: {
    username_or_email: string;
    password: string;
    email?: string;
  }): Promise<AuthResponse> {
    if (!isSupabaseConfigured) {
      return {
        ok: false,
        error: "Supabase konfiguratsiyasi topilmadi. Iltimos, .env faylida VITE_SUPABASE_URL va VITE_SUPABASE_ANON_KEY ni sozlang.",
      };
    }
    try {
      const targetEmail =
        payload.email ||
        (payload.username_or_email.includes("@")
          ? payload.username_or_email
          : `${payload.username_or_email.toLowerCase()}@mikasa.local`);

      const { data, error } = await supabase.auth.signInWithPassword({
        email: targetEmail,
        password: payload.password,
      });

      if (error) {
        return { ok: false, error: formatAuthError(error) };
      }

      const sessionToken = data.session?.access_token || "";
      if (sessionToken) {
        this.setAuthToken(sessionToken);
      }

      const user: MikasaAuthUser | undefined = data.user
        ? {
            id: data.user.id,
            username: data.user.user_metadata?.username || payload.username_or_email,
            email: data.user.email || targetEmail,
            is_active: true,
            is_verified: Boolean(data.user.email_confirmed_at),
            created_at: Date.now() / 1000,
          }
        : undefined;

      if (user) {
        this.notifyAuthChange(user);
      }

      return {
        ok: true,
        message: "Tizimga muvaffaqiyatli kirildi",
        user,
        session_token: sessionToken,
        expires_at: data.session?.expires_at,
      };
    } catch (err: any) {
      return { ok: false, error: formatAuthError(err) };
    }
  }

  public async signInWithGoogle(): Promise<{ ok: boolean; error?: string; url?: string }> {
    if (!isSupabaseConfigured) {
      return {
        ok: false,
        error: "Supabase konfiguratsiyasi topilmadi. Google OAuth uchun .env faylida VITE_SUPABASE_URL va VITE_SUPABASE_ANON_KEY ni sozlang.",
      };
    }
    try {
      const redirectTo = typeof window !== "undefined" ? window.location.origin : undefined;
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo,
          queryParams: {
            access_type: "offline",
            prompt: "consent",
          },
        },
      });
      if (error) {
        return { ok: false, error: formatAuthError(error) };
      }
      return { ok: true, url: data.url };
    } catch (err: any) {
      return { ok: false, error: formatAuthError(err) };
    }
  }

  public async logout(): Promise<{ ok: boolean; message?: string; error?: string }> {
    try {
      await supabase.auth.signOut();
      try {
        await fetch(`${API_BASE}/api/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...this.getAuthHeaders(),
          },
        });
      } catch {}
      this.setAuthToken(null);
      this.notifyAuthChange(null);
      return { ok: true, message: "Muvaffaqiyatli chiqildi" };
    } catch (err: any) {
      this.setAuthToken(null);
      this.notifyAuthChange(null);
      return { ok: false, error: formatAuthError(err) };
    }
  }

  public async logoutAllAccounts(): Promise<{ ok: boolean; message?: string; count?: number; error?: string }> {
    try {
      await supabase.auth.signOut({ scope: "global" });
      this.setAuthToken(null);
      this.notifyAuthChange(null);
      return { ok: true, message: "Barcha qurilmalardan chiqildi" };
    } catch (err: any) {
      return { ok: false, error: formatAuthError(err) };
    }
  }

  public async getMe(): Promise<AuthMeResponse> {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session || !session.user) {
        this.setAuthToken(null);
        this.notifyAuthChange(null);
        return { ok: false, authenticated: false };
      }

      this.setAuthToken(session.access_token);

      // Verify and fetch profile from backend
      try {
        const res = await fetch(`${API_BASE}/api/auth/me`, {
          headers: {
            ...this.getAuthHeaders(),
          },
        });
        if (res.ok) {
          const backendData = await res.json();
          if (backendData.ok && backendData.user) {
            this.notifyAuthChange(backendData.user);
            return backendData;
          }
        }
      } catch {}

      const user: MikasaAuthUser = {
        id: session.user.id,
        username: session.user.user_metadata?.username || session.user.email?.split("@")[0] || "User",
        email: session.user.email || "",
        is_active: true,
        is_verified: Boolean(session.user.email_confirmed_at),
        created_at: Date.now() / 1000,
      };
      this.notifyAuthChange(user);
      return {
        ok: true,
        authenticated: true,
        user,
        session: {
          session_id: session.user.id,
          user_id: session.user.id,
          created_at: Date.now() / 1000,
          expires_at: session.expires_at || 0,
          last_activity_at: Date.now() / 1000,
          is_active: true,
        },
      };
    } catch (err: any) {
      return { ok: false, authenticated: false, error: formatAuthError(err) };
    }
  }

  public async verifyEmail(_token: string): Promise<{ ok: boolean; message?: string; error?: string }> {
    return { ok: true, message: "Email Supabase Auth tasdiqlash havolasi orqali tasdiqlanadi." };
  }

  public async forgotPassword(target: string): Promise<{ ok: boolean; message?: string; token?: string; error?: string }> {
    if (!isSupabaseConfigured) {
      return {
        ok: false,
        error: "Supabase konfiguratsiyasi topilmadi. Iltimos, .env faylida VITE_SUPABASE_URL va VITE_SUPABASE_ANON_KEY ni sozlang.",
      };
    }
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(target);
      if (error) {
        return { ok: false, error: formatAuthError(error) };
      }
      return { ok: true, message: "Parolni tiklash bo'yicha yo'riqnoma email manzilingizga yuborildi." };
    } catch (err: any) {
      return { ok: false, error: formatAuthError(err) };
    }
  }

  public async resetPassword(payload: {
    new_password: string;
    confirm_password?: string;
    token?: string;
  }): Promise<{ ok: boolean; message?: string; error?: string }> {
    if (!isSupabaseConfigured) {
      return {
        ok: false,
        error: "Supabase konfiguratsiyasi topilmadi. Iltimos, .env faylida VITE_SUPABASE_URL va VITE_SUPABASE_ANON_KEY ni sozlang.",
      };
    }
    try {
      const { error } = await supabase.auth.updateUser({ password: payload.new_password });
      if (error) {
        return { ok: false, error: formatAuthError(error) };
      }
      return { ok: true, message: "Yangi parol muvaffaqiyatli o'rnatildi!" };
    } catch (err: any) {
      return { ok: false, error: formatAuthError(err) };
    }
  }

  public async changePassword(payload: {
    new_password: string;
    old_password?: string;
    confirm_password?: string;
  }): Promise<{ ok: boolean; message?: string; error?: string }> {
    return this.resetPassword(payload);
  }

  public async getHealth(): Promise<{
    status: string;
    app: string;
    version: string;
    supabase: string;
    environment: string;
    timestamp?: number;
  } | null> {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      if (res.ok) {
        return await res.json();
      }
      return null;
    } catch {
      return null;
    }
  }

  // ========== Phase 42: Device Enrollment & Pairing ==========
  public async startDevicePairing(ttl: number = 300): Promise<DevicePairingStartResponse> {
    try {
      const headers = {
        ...this.getAuthHeaders(),
        "Content-Type": "application/json",
      };
      const res = await fetch(`${API_BASE}/api/devices/pairing/start`, {
        method: "POST",
        headers,
        body: JSON.stringify({ ttl }),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: err.message || String(err) };
    }
  }

  public async getDevicePairingStatus(pairingId: string): Promise<DevicePairingStatusResponse> {
    try {
      const headers = this.getAuthHeaders();
      const res = await fetch(`${API_BASE}/api/devices/pairing/${encodeURIComponent(pairingId)}`, {
        method: "GET",
        headers,
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: err.message || String(err) };
    }
  }

  public async cancelDevicePairing(pairingId: string): Promise<{ ok: boolean; message?: string; error?: string }> {
    try {
      const headers = {
        ...this.getAuthHeaders(),
        "Content-Type": "application/json",
      };
      const res = await fetch(`${API_BASE}/api/devices/pairing/${encodeURIComponent(pairingId)}/cancel`, {
        method: "POST",
        headers,
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: err.message || String(err) };
    }
  }

  public async completeDevicePairing(payload: {
    pairing_id: string;
    code: string;
    public_key: string;
    device: {
      hostname: string;
      platform?: string;
      os_version?: string;
      name?: string;
      fingerprint?: string;
      device_id?: string;
    };
  }): Promise<DevicePairingCompleteResponse> {
    try {
      const res = await fetch(`${API_BASE}/api/devices/pairing/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, error: err.message || String(err) };
    }
  }
}

export interface DevicePairingStartResponse {
  ok: boolean;
  success?: boolean;
  pairing_id?: string;
  code?: string;
  expires_at?: number;
  expires_in?: number;
  error?: string;
}

export interface DevicePairingStatusResponse {
  ok: boolean;
  session?: {
    id: string;
    user_id: string;
    status: string;
    remaining_seconds: number;
    device_id?: string;
    created_at: number;
    expires_at: number;
  };
  status?: string;
  remaining_seconds?: number;
  device_id?: string;
  error?: string;
}

export interface DevicePairingCompleteResponse {
  ok: boolean;
  success?: boolean;
  message?: string;
  device?: UserDevice;
  credential?: {
    id: string;
    algorithm: string;
    public_key: string;
    enrolled_at?: number;
  };
  error?: string;
}

export interface TelegramLinkStartResponse {
  ok: boolean;
  request_id?: string;
  otp?: string;
  link_token?: string;
  deep_link?: string;
  expires_at?: number;
  ttl_seconds?: number;
  bot_username?: string;
  error?: string;
}

export interface TelegramLinkVerifyResponse {
  ok: boolean;
  message?: string;
  link?: {
    id: string;
    mikasa_user_id: string;
    telegram_user_id: number;
    linked_at: number;
    last_verified_at: number;
    status: string;
    metadata?: Record<string, any>;
  };
  mikasa_user_id?: string;
  error?: string;
}

export interface TelegramLinkStatusResponse {
  ok: boolean;
  status: string;
  is_linked: boolean;
  telegram_user_id?: number | null;
  link?: any;
  attempt_count?: number;
  expires_at?: number;
  ttl_seconds?: number;
  error?: string;
}

export interface TelegramAccountResponse {
  ok: boolean;
  is_linked: boolean;
  link?: {
    id: string;
    mikasa_user_id: string;
    telegram_user_id: number;
    linked_at: number;
    last_verified_at: number;
    status: string;
    metadata?: Record<string, any>;
  } | null;
  telegram_identity?: {
    telegram_user_id: number;
    first_name?: string;
    username?: string;
    created_at?: number;
    last_seen_at?: number;
    is_verified?: boolean;
    is_linked?: boolean;
  } | null;
  error?: string;
}

export interface TelegramBotStatusResponse {
  ok: boolean;
  configured: boolean;
  bot_username: string;
  active_links_count: number;
  pending_requests_count: number;
  error?: string;
}

// Phase 40: Universal Account & Multi-Device Interfaces
export interface UserDevice {
  id: string;
  mikasa_user_id: string;
  device_id: string;
  name: string;
  hostname: string;
  platform: string;
  agent_version: string;
  status: "online" | "offline" | "standby" | "revoked" | string;
  created_at: number;
  last_seen_at?: number | null;
  last_heartbeat_at?: number | null;
  metadata?: Record<string, any>;
  is_selected?: boolean;
}

export interface DevicesListResponse {
  ok: boolean;
  user_id?: string;
  devices: UserDevice[];
  selected_device_id?: string | null;
  error?: string;
}

export interface DeviceDetailResponse {
  ok: boolean;
  device?: UserDevice;
  error?: string;
}

export interface DeviceRenameResponse {
  ok: boolean;
  message?: string;
  device?: UserDevice;
  error?: string;
}

export interface DeviceSelectResponse {
  ok: boolean;
  message?: string;
  selected_device?: UserDevice;
  error?: string;
}

export interface DevicePermissionsResponse {
  ok: boolean;
  device_id?: string;
  profile?: PermissionProfileData;
  catalog?: Record<string, PermissionDefinitionItem[]> | any;
  error?: string;
}

export interface UserSession {
  user_id: string;
  device_id: string;
  device_name?: string;
  session_id: string;
  created_at: number;
  expires_at: number;
  is_active: boolean;
  permissions: string[];
  metadata?: Record<string, any>;
}

export interface AccountSessionsResponse {
  ok: boolean;
  user_id?: string;
  sessions: UserSession[];
  total: number;
  error?: string;
}

// Phase 41: Account Registration & Authentication Interfaces
export interface MikasaAuthUser {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: number;
  last_login_at?: number | null;
  role?: string;
}

export interface MikasaAccountSession {
  session_id: string;
  user_id: string;
  created_at: number;
  expires_at: number;
  last_activity_at: number;
  is_active: boolean;
  client_ip?: string;
  user_agent?: string;
}

export interface AuthResponse {
  ok: boolean;
  message?: string;
  error?: string;
  user?: MikasaAuthUser;
  session_token?: string;
  expires_at?: number;
}

export interface AuthMeResponse {
  ok: boolean;
  authenticated: boolean;
  user?: MikasaAuthUser;
  session?: MikasaAccountSession;
  error?: string;
}

export const backendService = new BackendService();

