import React, { useState, useRef, useEffect, useCallback } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import {
  MicIcon,
  SparklesIcon,
  FileTextIcon,
  AttachIcon,
  ArrowUpIcon,
  CloseIcon,
  CpuIcon,
  RefreshIcon,
  ClockIcon,
  SunIcon,
  CodeIcon,
  GlobeIcon,
  CheckCircleIcon,
  AlertCircleIcon,
} from "../components/icons/Icons";
import {
  backendService,
  VoiceState,
  SystemMetrics,
  ScheduledTaskItem,
  AgentPlanData,
} from "../services/backendService";

interface LandingPageProps {
  userName?: string;
  onNavigate: (path: string, initialPrompt?: string) => void;
}

// Format Uzbek Date & Time: "Seshanba, 15-sentabr • 22:45"
const formatUzbekDateTime = (date: Date): string => {
  const dayNames = [
    "Yakshanba",
    "Dushanba",
    "Seshanba",
    "Chorshanba",
    "Payshanba",
    "Juma",
    "Shanba",
  ];
  const monthNames = [
    "yanvar",
    "fevral",
    "mart",
    "aprel",
    "may",
    "iyun",
    "iyul",
    "avgust",
    "sentabr",
    "oktabr",
    "noyabr",
    "dekabr",
  ];
  const day = dayNames[date.getDay()];
  const dateNum = date.getDate();
  const month = monthNames[date.getMonth()];
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${day}, ${dateNum}-${month} • ${hours}:${minutes}`;
};

// 6 Orbiting suggestions around the Orb
interface SuggestionItem {
  id: string;
  label: string;
  prompt: string;
  icon: React.ComponentType<{ size?: number; color?: string }>;
  animationClass: string;
}

const ORBITING_SUGGESTIONS: SuggestionItem[] = [
  {
    id: "weather",
    label: "Ob-havoni tekshir",
    prompt: "Toshkent shahridagi hozirgi ob-havo ma'lumotlarini aniqlab ber",
    icon: SunIcon,
    animationClass: "orb-float-1",
  },
  {
    id: "system",
    label: "Kompyuterimni tekshir",
    prompt: "Kompyuterim resurslari (CPU, RAM, disk) holatini to'liq tahlil qilib hisobot ber",
    icon: CpuIcon,
    animationClass: "orb-float-2",
  },
  {
    id: "plan",
    label: "Bugungi rejani tuz",
    prompt: "Bugungi kun uchun ustuvor vazifalar va vaqt rejasini tuzishga yordam ber",
    icon: ClockIcon,
    animationClass: "orb-float-3",
  },
  {
    id: "python",
    label: "Pythonni tushuntir",
    prompt: "Python dasturlash tilidagi asinxron ishlash (asyncio) prinsiplarini amaliy misol bilan tushuntir",
    icon: CodeIcon,
    animationClass: "orb-float-4",
  },
  {
    id: "file",
    label: "Faylni tahlil qil",
    prompt: "Loyiha papkasidagi asosiy fayllar tuzilishi va vazifalarini tahlil qil",
    icon: FileTextIcon,
    animationClass: "orb-float-5",
  },
  {
    id: "web",
    label: "Internetdan izla",
    prompt: "Internetdan sun'iy intellekt va agentlar sohasidagi so'nggi yangiliklarni qidir",
    icon: GlobeIcon,
    animationClass: "orb-float-6",
  },
];

const STATE_CONFIG: Record<VoiceState, { label: string; color: string; bg: string; border: string }> = {
  idle: { label: "MIKASA TAYYOR", color: "#38BDF8", bg: "rgba(56, 189, 248, 0.12)", border: "rgba(56, 189, 248, 0.35)" },
  listening: { label: "TINGLANMOQDA...", color: "#F43F5E", bg: "rgba(244, 63, 94, 0.18)", border: "rgba(244, 63, 94, 0.5)" },
  thinking: { label: "O'YLANMOQDA...", color: "#A855F7", bg: "rgba(168, 85, 247, 0.18)", border: "rgba(168, 85, 247, 0.5)" },
  planning: { label: "REJALASHTIRILMOQDA...", color: "#6366F1", bg: "rgba(99, 102, 241, 0.18)", border: "rgba(99, 102, 241, 0.5)" },
  acting: { label: "BAJARILMOQDA...", color: "#06B6D4", bg: "rgba(6, 182, 212, 0.18)", border: "rgba(6, 182, 212, 0.5)" },
  verifying: { label: "TEKSHIRILMOQDA...", color: "#F59E0B", bg: "rgba(245, 158, 11, 0.18)", border: "rgba(245, 158, 11, 0.5)" },
  replanning: { label: "QAYTA REJALASHTIRILMOQDA...", color: "#EC4899", bg: "rgba(236, 72, 153, 0.18)", border: "rgba(236, 72, 153, 0.5)" },
  speaking: { label: "JAVOB BERILMOQDA...", color: "#10B981", bg: "rgba(16, 185, 129, 0.18)", border: "rgba(16, 185, 129, 0.5)" },
  completed: { label: "BAJARILDI", color: "#10B981", bg: "rgba(16, 185, 129, 0.18)", border: "rgba(16, 185, 129, 0.5)" },
  error: { label: "XATOLIK YUZ BERDI", color: "#EF4444", bg: "rgba(239, 68, 68, 0.18)", border: "rgba(239, 68, 68, 0.5)" },
};

/* ═══════════════════════════════════════════════════════
   Metric Row — compact telemetry display for system panel
   ═══════════════════════════════════════════════════════ */
const MetricRow: React.FC<{ label: string; value: string; percent?: number; color: string }> = ({ label, value, percent, color }) => (
  <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "4px 0" }}>
    <span style={{ fontSize: "11px", color: "#8E9BAE", width: "52px", flexShrink: 0 }}>{label}</span>
    {percent !== undefined && (
      <div style={{ flex: 1, height: "4px", borderRadius: "2px", backgroundColor: "rgba(255,255,255,0.06)", overflow: "hidden", minWidth: "50px" }}>
        <div style={{ width: `${Math.min(percent, 100)}%`, height: "100%", borderRadius: "2px", backgroundColor: color, transition: "width 0.5s ease" }} />
      </div>
    )}
    <span style={{ fontSize: "11px", color: "#CBD5E1", fontWeight: 600, minWidth: "44px", textAlign: "right" }}>{value}</span>
  </div>
);

export const LandingPage: React.FC<LandingPageProps> = ({
  userName = "Ustoz",
  onNavigate,
}) => {
  const [inputText, setInputText] = useState("");
  const [orbState, setOrbState] = useState<VoiceState>("idle");
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [lastResponse, setLastResponse] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);

  // Real System Metrics (Left Panel)
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);

  // Real Scheduler Tasks (Right Panel)
  const [tasks, setTasks] = useState<ScheduledTaskItem[]>([]);

  // Real AgentLoop & Planning 2.0 Visualization
  const [activePlan, setActivePlan] = useState<AgentPlanData | null>(null);
  const [isAgentRunning, setIsAgentRunning] = useState(false);

  // Side Panel Toggles
  const [leftPanelOpen, setLeftPanelOpen] = useState<boolean>(() => {
    return typeof window !== "undefined" ? window.innerWidth >= 1280 : true;
  });
  const [rightPanelOpen, setRightPanelOpen] = useState<boolean>(() => {
    return typeof window !== "undefined" ? window.innerWidth >= 1340 : true;
  });

  // Real Local Date & Time in Uzbek
  const [currentTime, setCurrentTime] = useState<string>(() => formatUzbekDateTime(new Date()));

  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Clock interval (updates every 10s)
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(formatUzbekDateTime(new Date()));
    }, 10000);
    return () => clearInterval(timer);
  }, []);

  // Fetch System Telemetry
  const fetchMetrics = useCallback(async () => {
    try {
      setMetricsLoading(true);
      const metrics = await backendService.getSystemMetrics();
      if (metrics && metrics.ok !== false) {
        setSystemMetrics(metrics);
      }
    } catch {
      // Graceful fallback
    } finally {
      setMetricsLoading(false);
    }
  }, []);

  // Fetch Scheduler Tasks
  const fetchTasks = useCallback(async () => {
    try {
      const res = await backendService.getSchedulerTasks();
      if (res && res.ok && Array.isArray(res.tasks)) {
        setTasks(res.tasks);
      }
    } catch {
      // Graceful fallback
    }
  }, []);

  // Initial Data & WebSocket listeners
  useEffect(() => {
    fetchMetrics();
    fetchTasks();

    const unsubStatus = backendService.onStatusChange(() => {
      // Status display handled by AppShell top nav
    });

    const unsubVoice = backendService.onVoiceStateChange((state) => {
      setOrbState(state);
    });

    const unsubResp = backendService.onResponse((data) => {
      setLastResponse(data.text);
      setIsLoading(false);
      setOrbState("speaking");
      setTimeout(() => {
        setOrbState("idle");
      }, 3500);
    });

    const unsubMetrics = backendService.onSystemMetrics((metrics) => {
      if (metrics) setSystemMetrics(metrics);
    });

    const unsubAgent = backendService.onAgentEvent((event) => {
      if (event.type === "agent_plan_created" && event.data?.plan) {
        setActivePlan(event.data.plan);
        setIsAgentRunning(true);
        setOrbState("planning");
      } else if (event.type === "agent_step_started") {
        setOrbState("acting");
        if (event.data?.step_id) {
          setActivePlan((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              steps: prev.steps.map((s) =>
                s.step_id === event.data.step_id ? { ...s, status: "running" } : s
              ),
            };
          });
        }
      } else if (event.type === "agent_step_completed") {
        setOrbState("verifying");
        if (event.data?.step_id) {
          setActivePlan((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              steps: prev.steps.map((s) =>
                s.step_id === event.data.step_id
                  ? {
                      ...s,
                      status: "completed",
                      observed_result: event.data.result,
                      verification: event.data.verification,
                    }
                  : s
              ),
            };
          });
        }
      } else if (event.type === "agent_plan_replanned" && event.data?.plan) {
        setActivePlan(event.data.plan);
        setOrbState("replanning");
      } else if (event.type === "agent_completed") {
        setIsAgentRunning(false);
        setOrbState("completed");
        if (event.data?.response) {
          setLastResponse(event.data.response);
        }
        setTimeout(() => {
          setOrbState("idle");
        }, 4000);
      } else if (event.type === "agent_failed") {
        setIsAgentRunning(false);
        setOrbState("error");
        setTimeout(() => {
          setOrbState("idle");
        }, 4000);
      }
    });

    // Telemetry polling every 3.5s
    const metricsInterval = setInterval(fetchMetrics, 3500);
    // Task polling every 12s
    const tasksInterval = setInterval(fetchTasks, 12000);

    return () => {
      unsubStatus();
      unsubVoice();
      unsubResp();
      unsubMetrics();
      unsubAgent();
      clearInterval(metricsInterval);
      clearInterval(tasksInterval);
    };
  }, [fetchMetrics, fetchTasks]);

  // Voice Interaction Toggle
  const handleVoiceToggle = async () => {
    setMicError(null);
    if (orbState === "listening") {
      backendService.stopClientVoice();
      setOrbState("idle");
      setAudioLevel(0);
    } else {
      setOrbState("listening");
      const started = await backendService.startClientVoice(
        (text, isFinal) => {
          if (isFinal && text && text.trim()) {
            handleRunQuery(text.trim());
          }
        },
        (errorMsg) => {
          setMicError(errorMsg);
          setOrbState("idle");
          setAudioLevel(0);
        },
        (level: any) => {
          if (typeof level === "number") {
            setAudioLevel(level);
          }
        }
      );
      if (!started) {
        // startClientVoice already handled error
      }
    }
  };

  // Run Query through AgentLoop or Chat
  const handleRunQuery = async (query: string) => {
    if (!query || !query.trim()) return;
    const cleanQuery = query.trim();
    setInputText("");
    setMicError(null);
    setIsLoading(true);
    setOrbState("thinking");

    try {
      // Execute via AgentLoop
      const res = await backendService.executeAgent(cleanQuery);
      if (res.ok) {
        if (res.plan) {
          setActivePlan(res.plan);
          setIsAgentRunning(true);
          setOrbState("acting");
        } else if (res.content || res.response) {
          setLastResponse(res.content || res.response);
          setOrbState("speaking");
          setTimeout(() => setOrbState("idle"), 4000);
        }
      } else {
        // Fallback to chat
        const chatRes = await backendService.sendChat(cleanQuery, "ask");
        if (chatRes.ok) {
          setLastResponse(chatRes.response);
          setOrbState("speaking");
          setTimeout(() => setOrbState("idle"), 4000);
        } else {
          setLastResponse(chatRes.error || res.error || "Kutilmagan xatolik yuz berdi.");
          setOrbState("error");
          setTimeout(() => setOrbState("idle"), 3000);
        }
      }
    } catch {
      setLastResponse("Aloqa xatosi. Backend bilan bog'lanib bo'lmadi.");
      setOrbState("error");
      setTimeout(() => setOrbState("idle"), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      handleRunQuery(inputText.trim());
    }
  };

  const handleAbortPlan = async () => {
    if (activePlan?.plan_id) {
      await backendService.abortAgentPlan(activePlan.plan_id);
    }
    setIsAgentRunning(false);
    setOrbState("idle");
  };

  const handleConfirmStep = async (stepId: string, approve: boolean) => {
    if (activePlan?.plan_id) {
      await backendService.confirmAgentStep(activePlan.plan_id, stepId, approve);
    }
  };

  const handleFileAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const fileName = files[0].name;
      setInputText(`"${fileName}" faylini tahlil qil va xulosasini ber.`);
      if (inputRef.current) inputRef.current.focus();
    }
  };

  const stateInfo = STATE_CONFIG[orbState] || STATE_CONFIG.idle;

  /* ═══════════════════════════════════════════════════════════════════
     RENDER — Full-width immersive home with floating glass panels
     ═══════════════════════════════════════════════════════════════════ */
  return (
    <div
      className="landing-page-redesign"
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        userSelect: "none",
        zIndex: 2,
      }}
    >
      {/* ═══ MAIN 3-COLUMN CONTENT ═══ */}
      <div
        style={{
          display: "flex",
          flex: 1,
          width: "100%",
          height: "100%",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* ── LEFT: System Status Panel ── */}
        {leftPanelOpen && (
          <div
            className="glass-panel"
            style={{
              position: "absolute",
              top: "20px",
              left: "20px",
              width: "240px",
              maxHeight: "calc(100% - 140px)",
              overflowY: "auto",
              padding: "16px",
              zIndex: 15,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <CpuIcon size={14} color="#38BDF8" />
                <span style={{ fontSize: "12px", fontWeight: 700, color: "#E2E8F0", letterSpacing: "0.06em" }}>TIZIM HOLATI</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <button
                  onClick={fetchMetrics}
                  title="Yangilash"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: "22px", height: "22px", borderRadius: "6px",
                    backgroundColor: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                    color: "#64748B", cursor: "pointer", transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#38BDF8"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#64748B"; }}
                >
                  <RefreshIcon size={11} color="currentColor" />
                </button>
                <button
                  onClick={() => setLeftPanelOpen(false)}
                  title="Yopish"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: "22px", height: "22px", borderRadius: "6px",
                    backgroundColor: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                    color: "#64748B", cursor: "pointer", transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#EF4444"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#64748B"; }}
                >
                  <CloseIcon size={10} color="currentColor" />
                </button>
              </div>
            </div>

            {metricsLoading && !systemMetrics && (
              <div style={{ fontSize: "11px", color: "#64748B", textAlign: "center", padding: "8px 0" }}>Yuklanmoqda...</div>
            )}

            {systemMetrics && (
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <MetricRow label="CPU" value={`${systemMetrics.cpu_percent ?? 0}%`} percent={systemMetrics.cpu_percent ?? 0} color="#38BDF8" />
                <MetricRow label="RAM" value={`${systemMetrics.ram_percent ?? 0}%`} percent={systemMetrics.ram_percent ?? 0} color="#C084FC" />
                {systemMetrics.disk_percent !== undefined && (
                  <MetricRow label="Disk" value={`${systemMetrics.disk_percent}%`} percent={systemMetrics.disk_percent} color="#34D399" />
                )}
                {systemMetrics.network_sent_kb !== undefined && (
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "4px 0" }}>
                    <span style={{ fontSize: "11px", color: "#8E9BAE", width: "52px", flexShrink: 0 }}>Tarmoq</span>
                    <span style={{ fontSize: "10.5px", color: "#94A3B8" }}>
                      ↑{((systemMetrics.network_sent_kb || 0) / 1024).toFixed(1)}MB ↓{((systemMetrics.network_recv_kb || 0) / 1024).toFixed(1)}MB
                    </span>
                  </div>
                )}
                {systemMetrics.battery_percent != null && (
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "4px 0" }}>
                    <span style={{ fontSize: "11px", color: "#8E9BAE", width: "52px", flexShrink: 0 }}>Batareya</span>
                    <span style={{ fontSize: "11px", color: "#CBD5E1", fontWeight: 600 }}>
                      {systemMetrics.battery_percent}% {systemMetrics.battery_plugged ? "⚡" : ""}
                    </span>
                  </div>
                )}
              </div>
            )}

            {!systemMetrics && !metricsLoading && (
              <div style={{ fontSize: "11px", color: "#475569", textAlign: "center", padding: "12px 0" }}>
                Ma'lumot mavjud emas
              </div>
            )}
          </div>
        )}

        {/* ── CENTER: Orb + Greeting + Suggestions + Agent ── */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            paddingTop: "10px",
            paddingBottom: "10px",
            position: "relative",
          }}
        >
          {/* Greeting */}
          <div style={{ textAlign: "center", marginBottom: "4px" }}>
            <h1
              style={{
                fontSize: "clamp(22px, 2.5vw, 32px)",
                fontWeight: 700,
                background: "linear-gradient(135deg, #FFFFFF 0%, #CBD5E1 60%, #93C5FD 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                margin: 0,
                lineHeight: 1.3,
              }}
            >
              Salom, {userName}.
            </h1>
            <p
              style={{
                fontSize: "clamp(13px, 1.2vw, 16px)",
                color: "#94A3B8",
                marginTop: "4px",
                fontWeight: 400,
              }}
            >
              Bugun qanday yordam beray?
            </p>
          </div>

          {/* Orb Container with Orbiting Suggestions */}
          <div
            style={{
              position: "relative",
              width: "clamp(280px, 30vw, 420px)",
              height: "clamp(280px, 30vw, 420px)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {/* The Orb */}
            <MikasaOrb
              size={typeof window !== "undefined" && window.innerWidth < 1200 ? 180 : 220}
              state={orbState}
              audioLevel={audioLevel}
              onClick={handleVoiceToggle}
            />

            {/* Orbiting Suggestion Pills */}
            {ORBITING_SUGGESTIONS.map((sug, i) => {
              const angle = (i * 60 - 90) * (Math.PI / 180);
              const radiusX = typeof window !== "undefined" && window.innerWidth < 1200 ? 135 : 175;
              const radiusY = typeof window !== "undefined" && window.innerWidth < 1200 ? 125 : 160;
              const x = Math.cos(angle) * radiusX;
              const y = Math.sin(angle) * radiusY;
              const Icon = sug.icon;
              return (
                <button
                  key={sug.id}
                  className="glass-pill-suggestion"
                  onClick={() => {
                    onNavigate("/chat", sug.prompt);
                  }}
                  title={sug.prompt}
                  style={{
                    position: "absolute",
                    left: `calc(50% + ${x}px - 65px)`,
                    top: `calc(50% + ${y}px - 15px)`,
                    animation: `${sug.animationClass} 4s ease-in-out infinite`,
                  }}
                >
                  <Icon size={13} color="#7DD3FC" />
                  <span>{sug.label}</span>
                </button>
              );
            })}
          </div>

          {/* State Badge */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "5px 14px",
              borderRadius: "20px",
              backgroundColor: stateInfo.bg,
              border: `1px solid ${stateInfo.border}`,
              marginTop: "2px",
            }}
          >
            <span
              style={{
                width: "7px",
                height: "7px",
                borderRadius: "50%",
                backgroundColor: stateInfo.color,
                boxShadow: `0 0 10px ${stateInfo.color}`,
                animation: orbState === "listening" ? "orb-pulse-fast 1.2s ease-in-out infinite" : "orb-breathing 3s ease-in-out infinite",
              }}
            />
            <span style={{ fontSize: "11px", fontWeight: 700, color: stateInfo.color, letterSpacing: "0.08em" }}>
              {stateInfo.label}
            </span>
          </div>

          {/* Mic Error */}
          {micError && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 14px",
                borderRadius: "10px",
                backgroundColor: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                fontSize: "12px",
                color: "#FCA5A5",
                maxWidth: "360px",
              }}
            >
              <AlertCircleIcon size={14} color="#EF4444" />
              <span>{micError}</span>
            </div>
          )}

          {/* Active Agent Plan Card */}
          {activePlan && isAgentRunning && (
            <div
              className="glass-panel"
              style={{ width: "clamp(320px, 40vw, 500px)", padding: "14px 16px", marginTop: "4px" }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <SparklesIcon size={14} color={stateInfo.color} />
                  <span style={{ fontSize: "12px", fontWeight: 700, color: "#E2E8F0" }}>AGENT REJASI</span>
                </div>
                <button
                  onClick={handleAbortPlan}
                  style={{
                    fontSize: "10.5px", padding: "3px 10px", borderRadius: "8px",
                    backgroundColor: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.3)",
                    color: "#FCA5A5", cursor: "pointer", transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.3)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.15)"; }}
                >
                  Bekor qilish
                </button>
              </div>
              {activePlan.goal && (
                <p style={{ fontSize: "12px", color: "#CBD5E1", marginBottom: "10px", lineHeight: 1.5 }}>
                  {activePlan.goal}
                </p>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {activePlan.steps.slice(0, 5).map((step) => (
                  <div
                    key={step.step_id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "5px 8px",
                      borderRadius: "8px",
                      backgroundColor: step.status === "running" ? "rgba(6, 182, 212, 0.1)" : "rgba(255,255,255,0.02)",
                      border: step.status === "running" ? "1px solid rgba(6, 182, 212, 0.25)" : "1px solid transparent",
                    }}
                  >
                    {step.status === "completed" ? (
                      <CheckCircleIcon size={13} color="#10B981" />
                    ) : step.status === "running" ? (
                      <div style={{ width: "13px", height: "13px", border: "2px solid #22D3EE", borderTopColor: "transparent", borderRadius: "50%", animation: "orb-particle-spin 0.8s linear infinite" }} />
                    ) : (
                      <div style={{ width: "11px", height: "11px", borderRadius: "50%", border: "1.5px solid #475569" }} />
                    )}
                    <span style={{ fontSize: "11.5px", color: step.status === "completed" ? "#94A3B8" : "#E2E8F0", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {step.description || step.tool || `Step ${step.step_id}`}
                    </span>
                    {step.status === "waiting_confirmation" && (
                      <div style={{ display: "flex", gap: "4px" }}>
                        <button onClick={() => handleConfirmStep(step.step_id, true)} style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "5px", backgroundColor: "rgba(16, 185, 129, 0.2)", border: "1px solid rgba(16, 185, 129, 0.3)", color: "#34D399", cursor: "pointer" }}>✓</button>
                        <button onClick={() => handleConfirmStep(step.step_id, false)} style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "5px", backgroundColor: "rgba(239, 68, 68, 0.2)", border: "1px solid rgba(239, 68, 68, 0.3)", color: "#FCA5A5", cursor: "pointer" }}>✗</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Last Response */}
          {lastResponse && !isAgentRunning && (
            <div
              className="glass-panel"
              style={{
                width: "clamp(300px, 38vw, 480px)",
                padding: "12px 16px",
                marginTop: "2px",
                maxHeight: "120px",
                overflowY: "auto",
              }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "8px" }}>
                <p style={{ fontSize: "12.5px", color: "#CBD5E1", lineHeight: 1.6, margin: 0, flex: 1 }}>
                  {lastResponse.length > 200 ? lastResponse.slice(0, 200) + "..." : lastResponse}
                </p>
                <button
                  onClick={() => setLastResponse(null)}
                  style={{ flexShrink: 0, color: "#475569", cursor: "pointer" }}
                >
                  <CloseIcon size={12} color="currentColor" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: Tasks Panel ── */}
        {rightPanelOpen && (
          <div
            className="glass-panel"
            style={{
              position: "absolute",
              top: "20px",
              right: "20px",
              width: "250px",
              maxHeight: "calc(100% - 140px)",
              overflowY: "auto",
              padding: "16px",
              zIndex: 15,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <ClockIcon size={14} color="#34D399" />
                <span style={{ fontSize: "12px", fontWeight: 700, color: "#E2E8F0", letterSpacing: "0.06em" }}>MENING VAZIFALARIM</span>
              </div>
              <button
                onClick={() => setRightPanelOpen(false)}
                title="Yopish"
                style={{
                  display: "flex", alignItems: "center", justifyContent: "center",
                  width: "22px", height: "22px", borderRadius: "6px",
                  backgroundColor: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                  color: "#64748B", cursor: "pointer", transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.color = "#EF4444"; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = "#64748B"; }}
              >
                <CloseIcon size={10} color="currentColor" />
              </button>
            </div>

            {tasks.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {tasks.slice(0, 8).map((task, idx) => (
                  <div
                    key={task.id || idx}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "6px 8px",
                      borderRadius: "8px",
                      backgroundColor: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.05)",
                    }}
                  >
                    {task.status === "completed" ? (
                      <CheckCircleIcon size={13} color="#10B981" />
                    ) : task.status === "active" ? (
                      <div style={{ width: "11px", height: "11px", borderRadius: "50%", backgroundColor: "#22D3EE", boxShadow: "0 0 8px rgba(34, 211, 238, 0.5)" }} />
                    ) : (
                      <div style={{ width: "11px", height: "11px", borderRadius: "50%", border: "1.5px solid #475569" }} />
                    )}
                    <span
                      style={{
                        fontSize: "11.5px",
                        color: task.status === "completed" ? "#64748B" : "#CBD5E1",
                        textDecoration: task.status === "completed" ? "line-through" : "none",
                        flex: 1,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {task.data?.text || task.type || `Vazifa #${idx + 1}`}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: "11.5px", color: "#475569", textAlign: "center", padding: "16px 0" }}>
                Hozircha vazifalar yo'q
              </div>
            )}

            {/* Quick link to Scheduler */}
            <button
              onClick={() => onNavigate("/scheduler")}
              style={{
                display: "flex", alignItems: "center", justifyContent: "center", gap: "6px",
                width: "100%", padding: "7px", marginTop: "10px", borderRadius: "8px",
                backgroundColor: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.2)",
                color: "#34D399", fontSize: "11px", fontWeight: 600, cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "rgba(16, 185, 129, 0.18)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "rgba(16, 185, 129, 0.08)"; }}
            >
              Barchasini ko'rish →
            </button>
          </div>
        )}

        {/* ── Panel Toggle Buttons (when panels are closed) ── */}
        {!leftPanelOpen && (
          <button
            onClick={() => setLeftPanelOpen(true)}
            title="Tizim panelini ko'rsatish"
            style={{
              position: "absolute", top: "20px", left: "20px", zIndex: 15,
              display: "flex", alignItems: "center", justifyContent: "center",
              width: "36px", height: "36px", borderRadius: "10px",
              backgroundColor: "rgba(10, 18, 35, 0.55)", backdropFilter: "blur(12px)",
              border: "1px solid rgba(255,255,255,0.08)", color: "#64748B", cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.35)"; e.currentTarget.style.color = "#38BDF8"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)"; e.currentTarget.style.color = "#64748B"; }}
          >
            <CpuIcon size={15} color="currentColor" />
          </button>
        )}
        {!rightPanelOpen && (
          <button
            onClick={() => setRightPanelOpen(true)}
            title="Vazifalar panelini ko'rsatish"
            style={{
              position: "absolute", top: "20px", right: "20px", zIndex: 15,
              display: "flex", alignItems: "center", justifyContent: "center",
              width: "36px", height: "36px", borderRadius: "10px",
              backgroundColor: "rgba(10, 18, 35, 0.55)", backdropFilter: "blur(12px)",
              border: "1px solid rgba(255,255,255,0.08)", color: "#64748B", cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = "rgba(16, 185, 129, 0.35)"; e.currentTarget.style.color = "#34D399"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)"; e.currentTarget.style.color = "#64748B"; }}
          >
            <ClockIcon size={15} color="currentColor" />
          </button>
        )}
      </div>

      {/* ═══ BOTTOM BAR: Voice Input + Time ═══ */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "16px",
          width: "100%",
          padding: "12px 24px 16px",
          flexShrink: 0,
          zIndex: 20,
        }}
      >
        {/* Time/Date (left of input) */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "12px",
            color: "#64748B",
            whiteSpace: "nowrap",
            minWidth: "180px",
          }}
        >
          <ClockIcon size={13} color="#475569" />
          <span>{currentTime}</span>
        </div>

        {/* Voice/Text Input */}
        <form
          onSubmit={handleSubmit}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            flex: 1,
            maxWidth: "600px",
            padding: "8px 12px",
            borderRadius: "16px",
            backgroundColor: "rgba(10, 18, 35, 0.6)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
            border: orbState === "listening"
              ? "1px solid rgba(244, 63, 94, 0.5)"
              : "1px solid rgba(255, 255, 255, 0.1)",
            boxShadow: orbState === "listening"
              ? "0 0 20px rgba(244, 63, 94, 0.2)"
              : "0 8px 32px rgba(0, 0, 0, 0.3)",
            transition: "all 0.25s ease",
          }}
        >
          {/* Mic button */}
          <button
            type="button"
            onClick={handleVoiceToggle}
            title={orbState === "listening" ? "Mikrofonni o'chirish" : "Mikrofon bilan gapiring"}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "38px",
              height: "38px",
              borderRadius: "12px",
              backgroundColor: orbState === "listening" ? "rgba(244, 63, 94, 0.25)" : "rgba(56, 189, 248, 0.12)",
              border: orbState === "listening"
                ? "1px solid rgba(244, 63, 94, 0.5)"
                : "1px solid rgba(56, 189, 248, 0.25)",
              color: orbState === "listening" ? "#F43F5E" : "#38BDF8",
              cursor: "pointer",
              transition: "all 0.2s ease",
              flexShrink: 0,
              animation: orbState === "listening" ? "orb-pulse-fast 1.5s ease-in-out infinite" : "none",
            }}
          >
            <MicIcon size={18} color="currentColor" />
          </button>

          {/* Text Input */}
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Mikasa, menga yordam ber..."
            disabled={isLoading}
            style={{
              flex: 1,
              fontSize: "14px",
              color: "#E2E8F0",
              backgroundColor: "transparent",
              border: "none",
              outline: "none",
              padding: "6px 4px",
            }}
          />

          {/* Attach file */}
          <input
            ref={fileInputRef}
            type="file"
            style={{ display: "none" }}
            onChange={handleFileAttach}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            title="Fayl biriktirish"
            style={{
              display: "flex", alignItems: "center", justifyContent: "center",
              width: "32px", height: "32px", borderRadius: "8px",
              backgroundColor: "transparent", border: "none",
              color: "#475569", cursor: "pointer", transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#94A3B8"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#475569"; }}
          >
            <AttachIcon size={16} color="currentColor" />
          </button>

          {/* Send */}
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            title="Yuborish"
            style={{
              display: "flex", alignItems: "center", justifyContent: "center",
              width: "34px", height: "34px", borderRadius: "10px",
              backgroundColor: inputText.trim() ? "rgba(56, 189, 248, 0.2)" : "rgba(255,255,255,0.04)",
              border: inputText.trim() ? "1px solid rgba(56, 189, 248, 0.35)" : "1px solid rgba(255,255,255,0.08)",
              color: inputText.trim() ? "#38BDF8" : "#475569",
              cursor: inputText.trim() ? "pointer" : "default",
              transition: "all 0.15s ease",
              opacity: isLoading ? 0.5 : 1,
            }}
          >
            {isLoading ? (
              <div style={{ width: "14px", height: "14px", border: "2px solid rgba(56, 189, 248, 0.3)", borderTopColor: "#38BDF8", borderRadius: "50%", animation: "orb-particle-spin 0.8s linear infinite" }} />
            ) : (
              <ArrowUpIcon size={16} color="currentColor" />
            )}
          </button>
        </form>

        {/* Spacer to balance time on left */}
        <div style={{ minWidth: "180px" }} />
      </div>
    </div>
  );
};
