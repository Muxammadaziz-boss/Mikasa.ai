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
  query: string;
  category: string;
  icon: string;
  desc: string;
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

export interface MemoryResponse {
  ok: boolean;
  profile: Record<string, any>;
  knowledge: KnowledgeItem[];
  conversations: Array<{ user: string; agent: string; time: string }>;
  stats: {
    kontekst_hajmi?: number;
    suhbatlar_soni?: number;
    bilimlar_soni?: number;
    profil_toliq?: boolean;
  };
}

export interface ScheduledTaskItem {
  id: string;
  type: string;
  run_at: string;
  data: { text?: string; [key: string]: any };
  completed: boolean;
  repeat: boolean;
}

export interface SchedulerResponse {
  ok: boolean;
  tasks: ScheduledTaskItem[];
  active_count: number;
}

export interface PluginItem {
  name: string;
  description: string;
  parameters: Record<string, any>;
  category: string;
  enabled: boolean;
  version: string;
}

export interface PluginsResponse {
  ok: boolean;
  tools: PluginItem[];
  total_count: number;
  categories: string[];
}

export interface AccountSettings {
  ok: boolean;
  name: string;
  voice_type: "ayol" | "erkak";
  theme: string;
  tts_speed: number;
  ai_model: string;
  version: string;
  voices_available: Array<{ id: string; name: string; lang: string }>;
}

export type VoiceState = "idle" | "listening" | "thinking" | "speaking";

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
      this.notifyStatus(data);
      if (data.voice_state) {
        this.notifyVoiceState(data.voice_state);
      }
      return data;
    } catch {
      const offlineStatus: BackendStatus = { status: "offline" };
      this.notifyStatus(offlineStatus);
      return offlineStatus;
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

  public async executeCommand(command: string): Promise<{ ok: boolean; result: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/commands/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
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
      return { ok: false, tools: [], total_count: 0, categories: [] };
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
    try {
      const res = await fetch(`${API_BASE}/api/account`, { method: "GET" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    } catch {
      return {
        ok: false,
        name: "Muxammadaziz",
        voice_type: "ayol",
        theme: "dark",
        tts_speed: 2.0,
        ai_model: "gemini",
        version: "7.1.0",
        voices_available: [
          { id: "ayol", name: "Madina (Ayol)", lang: "uz-UZ-MadinaNeural" },
          { id: "erkak", name: "Sardar (Erkak)", lang: "uz-UZ-SardarNeural" },
        ],
      };
    }
  }

  public async updateAccount(data: {
    name?: string;
    voice_type?: string;
    tts_speed?: number;
    theme?: string;
  }): Promise<{ ok: boolean; message: string }> {
    try {
      const res = await fetch(`${API_BASE}/api/account`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      return await res.json();
    } catch (err: any) {
      return { ok: false, message: String(err) };
    }
  }

  public getStatus(): BackendStatus {
    return this.currentStatus;
  }

  public getVoiceState(): VoiceState {
    return this.currentVoiceState;
  }
}

export const backendService = new BackendService();
