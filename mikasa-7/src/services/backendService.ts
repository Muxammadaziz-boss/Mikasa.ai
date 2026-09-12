// ========== backendService.ts ==========
// Mikasa AI 7.1.0 — Desktop Frontend to Python Backend Connector
// Connects to local aiohttp API Server at http://127.0.0.1:18420

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
  key: string;
  value: string;
  saved_at?: string;
  access_count?: number;
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

export type VoiceState = "idle" | "listening" | "thinking" | "speaking" | "error";

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

  constructor() {
    this.connectWs();
    this.startHealthPolling();
  }

  // ========== Listeners ==========
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

  public async saveKnowledge(key: string, value: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/api/memory/knowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value }),
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
        version: "7.1.0",
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

  public getStatus(): BackendStatus {
    return this.currentStatus;
  }

  public getUserName(): string {
    return this.currentStatus.user || localStorage.getItem("mikasa_user_name") || "Ustoz";
  }

  public getVoiceState(): VoiceState {
    return this.currentVoiceState;
  }
}

export const backendService = new BackendService();

