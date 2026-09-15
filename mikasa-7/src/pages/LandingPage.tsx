import React, { useState, useRef, useEffect, useCallback } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import { Avatar } from "../components/Avatar";
import {
  MicIcon,
  ChatIcon,
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
  SchedulerIcon,
  MemoryIcon,
  CheckCircleIcon,
  AlertCircleIcon,
} from "../components/icons/Icons";
import {
  backendService,
  BackendStatus,
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

export const LandingPage: React.FC<LandingPageProps> = ({
  userName = "Ustoz",
  onNavigate,
}) => {
  const [inputText, setInputText] = useState("");
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({ status: "connecting" });
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

    const unsubStatus = backendService.onStatusChange((status) => {
      setBackendStatus(status);
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

  return (
    <div
      className="landing-page-v34"
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        overflow: "hidden",
        userSelect: "none",
        zIndex: 2,
      }}
    >
      {/* ============================================================ */}
      {/* 1. TOP NAVIGATION BAR                                         */}
      {/* ============================================================ */}
      <header
        className="landing-top-nav"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "56px",
          padding: "0 24px",
          backgroundColor: "rgba(6, 10, 20, 0.65)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          zIndex: 40,
          flexShrink: 0,
        }}
      >
        {/* Brand & Online Dot */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              cursor: "pointer",
            }}
            onClick={() => onNavigate("/")}
          >
            <span
              style={{
                fontFamily: "system-ui, -apple-system, sans-serif",
                fontSize: "17px",
                fontWeight: 800,
                letterSpacing: "0.08em",
                background: "linear-gradient(135deg, #FFFFFF 0%, #93C5FD 50%, #38BDF8 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              MIKASA AI
            </span>
            <span
              style={{
                fontSize: "10px",
                fontWeight: 600,
                padding: "2px 6px",
                borderRadius: "6px",
                backgroundColor: "rgba(56, 189, 248, 0.15)",
                color: "#38BDF8",
                border: "1px solid rgba(56, 189, 248, 0.3)",
              }}
            >
              v7.0.0
            </span>
          </div>

          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "3px 9px",
              borderRadius: "20px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.06)",
              fontSize: "11px",
              color: "#94A3B8",
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                backgroundColor:
                  backendStatus.status === "online"
                    ? "#10B981"
                    : backendStatus.status === "connecting"
                    ? "#F59E0B"
                    : "#EF4444",
                boxShadow:
                  backendStatus.status === "online"
                    ? "0 0 8px rgba(16, 185, 129, 0.8)"
                    : "0 0 8px rgba(245, 158, 11, 0.8)",
              }}
            />
            <span>
              {backendStatus.status === "online"
                ? "Online"
                : backendStatus.status === "connecting"
                ? "Ulanmoqda..."
                : "Offline"}
            </span>
          </div>
        </div>

        {/* Center Quick Navigation Links */}
        <nav style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <button
            onClick={() => onNavigate("/chat")}
            className="nav-tab-pill"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "7px",
              padding: "6px 14px",
              borderRadius: "10px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "#E2E8F0",
              fontSize: "12.5px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(56, 189, 248, 0.15)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.35)";
              e.currentTarget.style.color = "#38BDF8";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.color = "#E2E8F0";
            }}
          >
            <ChatIcon size={14} color="currentColor" />
            <span>Suhbatlashish</span>
          </button>

          <button
            onClick={() => onNavigate("/memory")}
            className="nav-tab-pill"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "7px",
              padding: "6px 14px",
              borderRadius: "10px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "#E2E8F0",
              fontSize: "12.5px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(168, 85, 247, 0.15)";
              e.currentTarget.style.borderColor = "rgba(168, 85, 247, 0.35)";
              e.currentTarget.style.color = "#C084FC";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.color = "#E2E8F0";
            }}
          >
            <MemoryIcon size={14} color="currentColor" />
            <span>Xotira</span>
          </button>

          <button
            onClick={() => onNavigate("/scheduler")}
            className="nav-tab-pill"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "7px",
              padding: "6px 14px",
              borderRadius: "10px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "#E2E8F0",
              fontSize: "12.5px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(16, 185, 129, 0.15)";
              e.currentTarget.style.borderColor = "rgba(16, 185, 129, 0.35)";
              e.currentTarget.style.color = "#34D399";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.color = "#E2E8F0";
            }}
          >
            <SchedulerIcon size={14} color="currentColor" />
            <span>Rejalashtirish</span>
          </button>
        </nav>

        {/* Right Action & Profile Button */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* Toggle Left (Tizim) */}
          <button
            onClick={() => setLeftPanelOpen(!leftPanelOpen)}
            title={leftPanelOpen ? "Tizim panelini berkitish" : "Tizim panelini ko'rsatish"}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 10px",
              borderRadius: "8px",
              backgroundColor: leftPanelOpen ? "rgba(56, 189, 248, 0.15)" : "rgba(255, 255, 255, 0.04)",
              border: `1px solid ${leftPanelOpen ? "rgba(56, 189, 248, 0.35)" : "rgba(255, 255, 255, 0.08)"}`,
              color: leftPanelOpen ? "#38BDF8" : "#94A3B8",
              fontSize: "11.5px",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <CpuIcon size={13} color="currentColor" />
            <span>Tizim</span>
          </button>

          {/* Toggle Right (Vazifalar) */}
          <button
            onClick={() => setRightPanelOpen(!rightPanelOpen)}
            title={rightPanelOpen ? "Vazifalar panelini berkitish" : "Vazifalar panelini ko'rsatish"}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 10px",
              borderRadius: "8px",
              backgroundColor: rightPanelOpen ? "rgba(16, 185, 129, 0.15)" : "rgba(255, 255, 255, 0.04)",
              border: `1px solid ${rightPanelOpen ? "rgba(16, 185, 129, 0.35)" : "rgba(255, 255, 255, 0.08)"}`,
              color: rightPanelOpen ? "#10B981" : "#94A3B8",
              fontSize: "11.5px",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <SchedulerIcon size={13} color="currentColor" />
            <span>Vazifalar</span>
          </button>

          {/* User Profile Pill */}
          <div
            onClick={() => onNavigate("/account")}
            title="Foydalanuvchi profili va sozlamalar"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "4px 10px 4px 5px",
              borderRadius: "20px",
              backgroundColor: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.1)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.4)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.05)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
            }}
          >
            <Avatar initials={(userName || "U").charAt(0).toUpperCase()} size={24} />
            <span style={{ fontSize: "12.5px", fontWeight: 600, color: "#F1F5F9" }}>
              {userName || backendStatus.user || "Ustoz"}
            </span>
          </div>
        </div>
      </header>

      {/* ============================================================ */}
      {/* 2. MAIN 3-COLUMN WORKSPACE BODY                               */}
      {/* ============================================================ */}
      <div
        className="landing-workspace-grid"
        style={{
          display: "flex",
          flex: 1,
          width: "100%",
          height: "calc(100% - 56px)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* ------------------------------------------------------------ */}
        {/* LEFT PANEL: TIZIM HOLATI (Telemetry via psutil)              */}
        {/* ------------------------------------------------------------ */}
        {leftPanelOpen && (
          <aside
            className="glass-panel-telemetry"
            style={{
              width: "270px",
              height: "100%",
              backgroundColor: "rgba(8, 14, 26, 0.68)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              borderRight: "1px solid rgba(255, 255, 255, 0.08)",
              padding: "18px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
              overflowY: "auto",
              flexShrink: 0,
              zIndex: 10,
              animation: "fadeIn 0.2s ease",
            }}
          >
            {/* Header */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
                paddingBottom: "10px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <CpuIcon size={16} color="#38BDF8" />
                <span style={{ fontSize: "13.5px", fontWeight: 700, color: "#F8FAFC" }}>
                  Tizim holati
                </span>
              </div>
              <button
                onClick={fetchMetrics}
                title="Yangilash"
                style={{
                  background: "transparent",
                  border: "none",
                  color: metricsLoading ? "#38BDF8" : "#94A3B8",
                  cursor: "pointer",
                  padding: "4px",
                  borderRadius: "6px",
                  display: "flex",
                  alignItems: "center",
                  animation: metricsLoading ? "spin 0.8s linear infinite" : "none",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#38BDF8")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "#94A3B8")}
              >
                <RefreshIcon size={13} color="currentColor" />
              </button>
            </div>

            {/* Metric 1: CPU */}
            <div
              className="glass-card"
              style={{
                padding: "12px",
                borderRadius: "12px",
                backgroundColor: "rgba(14, 22, 38, 0.6)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <span style={{ fontSize: "11.5px", color: "#94A3B8", fontWeight: 500 }}>
                  Protsessor (CPU)
                </span>
                <span style={{ fontSize: "12px", fontWeight: 700, color: "#38BDF8" }}>
                  {systemMetrics ? `${systemMetrics.cpu_percent}%` : "--%"}
                </span>
              </div>
              <div
                style={{
                  width: "100%",
                  height: "6px",
                  borderRadius: "3px",
                  backgroundColor: "rgba(255, 255, 255, 0.08)",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, systemMetrics?.cpu_percent || 0)}%`,
                    height: "100%",
                    borderRadius: "3px",
                    background:
                      (systemMetrics?.cpu_percent || 0) > 80
                        ? "linear-gradient(90deg, #EF4444, #F43F5E)"
                        : (systemMetrics?.cpu_percent || 0) > 60
                        ? "linear-gradient(90deg, #F59E0B, #FBBF24)"
                        : "linear-gradient(90deg, #0284C7, #38BDF8)",
                    transition: "width 0.4s ease",
                  }}
                />
              </div>
            </div>

            {/* Metric 2: RAM */}
            <div
              className="glass-card"
              style={{
                padding: "12px",
                borderRadius: "12px",
                backgroundColor: "rgba(14, 22, 38, 0.6)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "11.5px", color: "#94A3B8", fontWeight: 500 }}>
                  Operativ xotira (RAM)
                </span>
                <span style={{ fontSize: "12px", fontWeight: 700, color: "#A855F7" }}>
                  {systemMetrics ? `${systemMetrics.ram_percent}%` : "--%"}
                </span>
              </div>
              <div style={{ fontSize: "10.5px", color: "#64748B", marginBottom: "6px" }}>
                {systemMetrics
                  ? `${systemMetrics.ram_used_gb.toFixed(1)} GB / ${systemMetrics.ram_total_gb.toFixed(1)} GB`
                  : "Yuklanmoqda..."}
              </div>
              <div
                style={{
                  width: "100%",
                  height: "6px",
                  borderRadius: "3px",
                  backgroundColor: "rgba(255, 255, 255, 0.08)",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, systemMetrics?.ram_percent || 0)}%`,
                    height: "100%",
                    borderRadius: "3px",
                    background: "linear-gradient(90deg, #7C3AED, #C084FC)",
                    transition: "width 0.4s ease",
                  }}
                />
              </div>
            </div>

            {/* Metric 3: Disk */}
            <div
              className="glass-card"
              style={{
                padding: "12px",
                borderRadius: "12px",
                backgroundColor: "rgba(14, 22, 38, 0.6)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "11.5px", color: "#94A3B8", fontWeight: 500 }}>
                  Doimiy xotira (Disk)
                </span>
                <span style={{ fontSize: "12px", fontWeight: 700, color: "#10B981" }}>
                  {systemMetrics ? `${systemMetrics.disk_percent}%` : "--%"}
                </span>
              </div>
              <div style={{ fontSize: "10.5px", color: "#64748B", marginBottom: "6px" }}>
                {systemMetrics?.disk_free_gb
                  ? `${systemMetrics.disk_free_gb.toFixed(1)} GB bo'sh joy mavjud`
                  : "Yuklanmoqda..."}
              </div>
              <div
                style={{
                  width: "100%",
                  height: "6px",
                  borderRadius: "3px",
                  backgroundColor: "rgba(255, 255, 255, 0.08)",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${Math.min(100, systemMetrics?.disk_percent || 0)}%`,
                    height: "100%",
                    borderRadius: "3px",
                    background: "linear-gradient(90deg, #059669, #34D399)",
                    transition: "width 0.4s ease",
                  }}
                />
              </div>
            </div>

            {/* Metric 4: Tarmoq (Network) */}
            <div
              className="glass-card"
              style={{
                padding: "12px",
                borderRadius: "12px",
                backgroundColor: "rgba(14, 22, 38, 0.6)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
              }}
            >
              <span style={{ fontSize: "11.5px", color: "#94A3B8", fontWeight: 500, display: "block", marginBottom: "8px" }}>
                Tarmoq yuklamasi
              </span>
              <div style={{ display: "flex", gap: "8px" }}>
                <div
                  style={{
                    flex: 1,
                    padding: "6px 8px",
                    borderRadius: "8px",
                    backgroundColor: "rgba(255, 255, 255, 0.04)",
                    textAlign: "center",
                  }}
                >
                  <div style={{ fontSize: "10px", color: "#64748B" }}>Yuklash ↑</div>
                  <div style={{ fontSize: "12px", fontWeight: 700, color: "#38BDF8" }}>
                    {systemMetrics ? `${systemMetrics.network_sent_kb} KB/s` : "--"}
                  </div>
                </div>
                <div
                  style={{
                    flex: 1,
                    padding: "6px 8px",
                    borderRadius: "8px",
                    backgroundColor: "rgba(255, 255, 255, 0.04)",
                    textAlign: "center",
                  }}
                >
                  <div style={{ fontSize: "10px", color: "#64748B" }}>Qabul ↓</div>
                  <div style={{ fontSize: "12px", fontWeight: 700, color: "#10B981" }}>
                    {systemMetrics ? `${systemMetrics.network_recv_kb} KB/s` : "--"}
                  </div>
                </div>
              </div>
            </div>

            {/* Metric 5: Quvvat / Batareya */}
            <div
              style={{
                padding: "8px 12px",
                borderRadius: "10px",
                backgroundColor: "rgba(16, 185, 129, 0.08)",
                border: "1px solid rgba(16, 185, 129, 0.2)",
                fontSize: "11px",
                color: "#A7F3D0",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span>Quvvat manbai:</span>
              <span style={{ fontWeight: 600 }}>
                {systemMetrics?.battery_percent !== undefined && systemMetrics?.battery_percent !== null
                  ? `${systemMetrics.battery_percent}% (${systemMetrics.battery_plugged ? "Ulangan" : "Batareyada"})`
                  : "Tarmoqqa ulangan"}
              </span>
            </div>
          </aside>
        )}

        {/* ------------------------------------------------------------ */}
        {/* CENTER COLUMN: ORB, SUGGESTIONS & AGENT VISUALIZATION        */}
        {/* ------------------------------------------------------------ */}
        <main
          className="landing-center-hero"
          style={{
            flex: 1,
            height: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 24px 20px 24px",
            overflowY: "auto",
            overflowX: "hidden",
            position: "relative",
            zIndex: 15,
          }}
        >
          {/* TOP GREETING */}
          <div
            style={{
              textAlign: "center",
              marginTop: "6px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <h1
              className="text-metallic-gradient"
              style={{
                fontSize: "clamp(28px, 3.4vw, 38px)",
                fontWeight: 700,
                letterSpacing: "-0.02em",
                lineHeight: 1.15,
                margin: 0,
              }}
            >
              Salom, {userName || backendStatus.user || "Ustoz"}
            </h1>
            <p
              style={{
                fontSize: "clamp(14px, 1.5vw, 16px)",
                color: "#94A3B8",
                fontWeight: 400,
                margin: 0,
              }}
            >
              Qanday yordam beray?
            </p>
          </div>

          {/* ========================================================== */}
          {/* CENTRAL ORB & ORBITING SUGGESTIONS / AGENT PROGRESS CARD  */}
          {/* ========================================================== */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              maxWidth: "860px",
              margin: "auto 0",
              position: "relative",
              gap: "18px",
            }}
          >
            {/* If Agent Plan is NOT active: Show Orb with Orbiting Suggestions */}
            {!activePlan ? (
              <div
                style={{
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "100%",
                  minHeight: "290px",
                }}
              >
                {/* Left 3 Orbiting Suggestions */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "14px",
                    alignItems: "flex-end",
                    marginRight: "clamp(14px, 3vw, 36px)",
                  }}
                >
                  {ORBITING_SUGGESTIONS.slice(0, 3).map((item) => {
                    const IconComponent = item.icon;
                    return (
                      <button
                        key={item.id}
                        className={`glass-pill-suggestion ${item.animationClass}`}
                        onClick={() => handleRunQuery(item.prompt)}
                        title={item.prompt}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "8px",
                          padding: "9px 16px",
                          borderRadius: "30px",
                          backgroundColor: "rgba(12, 20, 36, 0.72)",
                          backdropFilter: "blur(18px)",
                          WebkitBackdropFilter: "blur(18px)",
                          border: "1px solid rgba(255, 255, 255, 0.1)",
                          color: "#E2E8F0",
                          fontSize: "12.5px",
                          fontWeight: 500,
                          cursor: "pointer",
                        }}
                      >
                        <IconComponent size={14} color="#38BDF8" />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Central Mikasa Orb */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "10px",
                    cursor: "pointer",
                  }}
                  onClick={handleVoiceToggle}
                  title={orbState === "listening" ? "Tinglashni to'xtatish" : "Ovozli muloqotni boshlash"}
                >
                  <MikasaOrb size="clamp(150px, 17vw, 185px)" state={orbState} audioLevel={audioLevel} />

                  {/* State badge under the Orb */}
                  <div
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "4px 14px",
                      borderRadius: "20px",
                      backgroundColor: stateInfo.bg,
                      border: `1px solid ${stateInfo.border}`,
                      color: stateInfo.color,
                      fontSize: "11px",
                      fontWeight: 700,
                      letterSpacing: "0.06em",
                      boxShadow: `0 0 16px ${stateInfo.bg}`,
                      transition: "all 0.25s ease",
                    }}
                  >
                    <span
                      style={{
                        width: "6px",
                        height: "6px",
                        borderRadius: "50%",
                        backgroundColor: stateInfo.color,
                      }}
                    />
                    <span>{stateInfo.label}</span>
                  </div>
                </div>

                {/* Right 3 Orbiting Suggestions */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "14px",
                    alignItems: "flex-start",
                    marginLeft: "clamp(14px, 3vw, 36px)",
                  }}
                >
                  {ORBITING_SUGGESTIONS.slice(3, 6).map((item) => {
                    const IconComponent = item.icon;
                    return (
                      <button
                        key={item.id}
                        className={`glass-pill-suggestion ${item.animationClass}`}
                        onClick={() => handleRunQuery(item.prompt)}
                        title={item.prompt}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "8px",
                          padding: "9px 16px",
                          borderRadius: "30px",
                          backgroundColor: "rgba(12, 20, 36, 0.72)",
                          backdropFilter: "blur(18px)",
                          WebkitBackdropFilter: "blur(18px)",
                          border: "1px solid rgba(255, 255, 255, 0.1)",
                          color: "#E2E8F0",
                          fontSize: "12.5px",
                          fontWeight: 500,
                          cursor: "pointer",
                        }}
                      >
                        <IconComponent size={14} color="#34D399" />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : (
              /* AgentLoop & Planning 2.0 Visualization Card */
              <div
                className="glass-card-interactive"
                style={{
                  width: "100%",
                  maxHeight: "380px",
                  borderRadius: "18px",
                  backgroundColor: "rgba(10, 16, 30, 0.85)",
                  backdropFilter: "blur(26px)",
                  WebkitBackdropFilter: "blur(26px)",
                  border: "1px solid rgba(56, 189, 248, 0.35)",
                  boxShadow: "0 12px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(2, 132, 199, 0.15)",
                  display: "flex",
                  flexDirection: "column",
                  overflow: "hidden",
                  padding: "16px 20px",
                  gap: "12px",
                }}
              >
                {/* Plan Header */}
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 800,
                          padding: "3px 8px",
                          borderRadius: "6px",
                          backgroundColor: "rgba(56, 189, 248, 0.2)",
                          color: "#38BDF8",
                          border: "1px solid rgba(56, 189, 248, 0.4)",
                        }}
                      >
                        REJA v{activePlan.plan_version || 1}
                      </span>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 600,
                          color: activePlan.status === "completed" ? "#10B981" : activePlan.status === "failed" ? "#EF4444" : "#F59E0B",
                        }}
                      >
                        {activePlan.status === "completed"
                          ? "Muvaffaqiyatli yakunlandi"
                          : activePlan.status === "failed"
                          ? "Xatolik bilan to'xtatildi"
                          : "Bajarilmoqda..."}
                      </span>
                    </div>
                    <div style={{ fontSize: "14px", fontWeight: 700, color: "#FFFFFF" }}>
                      {activePlan.goal}
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    {isAgentRunning && (
                      <button
                        onClick={handleAbortPlan}
                        style={{
                          padding: "5px 12px",
                          borderRadius: "8px",
                          backgroundColor: "rgba(239, 68, 68, 0.2)",
                          border: "1px solid rgba(239, 68, 68, 0.4)",
                          color: "#FCA5A5",
                          fontSize: "11px",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        To'xtatish
                      </button>
                    )}
                    {!isAgentRunning && (
                      <button
                        onClick={() => setActivePlan(null)}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#94A3B8",
                          cursor: "pointer",
                          padding: "4px",
                        }}
                        title="Yopish"
                      >
                        <CloseIcon size={14} color="currentColor" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Replanning Reason Banner */}
                {Boolean((activePlan.plan_version && activePlan.plan_version > 1) || activePlan.replan_history?.length) && (
                  <div
                    style={{
                      padding: "8px 12px",
                      borderRadius: "10px",
                      backgroundColor: "rgba(245, 158, 11, 0.12)",
                      border: "1px solid rgba(245, 158, 11, 0.35)",
                      color: "#FCD34D",
                      fontSize: "12px",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                    }}
                  >
                    <AlertCircleIcon size={14} color="#F59E0B" />
                    <span>
                      Qayta rejalashtirildi:{" "}
                      {activePlan.replan_history?.[activePlan.replan_history.length - 1]?.reason ||
                        "Muqobil asbob va yo'l tanlandi."}
                    </span>
                  </div>
                )}

                {/* Steps List */}
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                    overflowY: "auto",
                    paddingRight: "4px",
                  }}
                >
                  {activePlan.steps.map((step, idx) => {
                    const isRunning = step.status === "running";
                    const isDone = step.status === "completed";
                    const isFailed = step.status === "failed";
                    const isWaiting = step.status === "waiting_confirmation";

                    return (
                      <div
                        key={step.step_id || idx}
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: "10px",
                          padding: "8px 12px",
                          borderRadius: "10px",
                          backgroundColor: isRunning
                            ? "rgba(56, 189, 248, 0.12)"
                            : isDone
                            ? "rgba(16, 185, 129, 0.08)"
                            : "rgba(255, 255, 255, 0.03)",
                          border: `1px solid ${
                            isRunning
                              ? "rgba(56, 189, 248, 0.4)"
                              : isDone
                              ? "rgba(16, 185, 129, 0.25)"
                              : "rgba(255, 255, 255, 0.06)"
                          }`,
                        }}
                      >
                        <div style={{ marginTop: "2px" }}>
                          {isDone ? (
                            <CheckCircleIcon size={15} color="#10B981" />
                          ) : isRunning ? (
                            <div
                              style={{
                                width: "14px",
                                height: "14px",
                                border: "2px solid rgba(56, 189, 248, 0.2)",
                                borderTopColor: "#38BDF8",
                                borderRadius: "50%",
                                animation: "spin 0.8s linear infinite",
                              }}
                            />
                          ) : isFailed ? (
                            <AlertCircleIcon size={15} color="#EF4444" />
                          ) : (
                            <ClockIcon size={15} color="#64748B" />
                          )}
                        </div>

                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                            <span style={{ fontSize: "12.5px", fontWeight: 600, color: "#F1F5F9" }}>
                              {step.order}. {step.intent || step.description}
                            </span>
                            {step.selected_tool && (
                              <span
                                style={{
                                  fontSize: "10px",
                                  padding: "1px 5px",
                                  borderRadius: "4px",
                                  backgroundColor: "rgba(255, 255, 255, 0.06)",
                                  color: "#94A3B8",
                                }}
                              >
                                tool: {step.selected_tool}
                              </span>
                            )}
                            {step.required_capability && (
                              <span
                                style={{
                                  fontSize: "10px",
                                  padding: "1px 5px",
                                  borderRadius: "4px",
                                  backgroundColor: "rgba(56, 189, 248, 0.1)",
                                  color: "#38BDF8",
                                }}
                              >
                                {step.required_capability}
                              </span>
                            )}
                          </div>

                          {/* Safe Verifier Feedback */}
                          {step.verification && (
                            <div style={{ fontSize: "11px", color: "#34D399", marginTop: "3px" }}>
                              Tasdiqlandi: {step.verification.reason || "Natija tekshiruvdan o'tdi"}
                            </div>
                          )}

                          {/* Human Confirmation Interaction */}
                          {isWaiting && (
                            <div style={{ marginTop: "6px", display: "flex", gap: "8px" }}>
                              <button
                                onClick={() => handleConfirmStep(step.step_id, true)}
                                style={{
                                  padding: "4px 10px",
                                  borderRadius: "6px",
                                  backgroundColor: "#10B981",
                                  color: "#FFFFFF",
                                  border: "none",
                                  fontSize: "11px",
                                  fontWeight: 600,
                                  cursor: "pointer",
                                }}
                              >
                                Tasdiqlash
                              </button>
                              <button
                                onClick={() => handleConfirmStep(step.step_id, false)}
                                style={{
                                  padding: "4px 10px",
                                  borderRadius: "6px",
                                  backgroundColor: "rgba(255, 255, 255, 0.1)",
                                  color: "#E2E8F0",
                                  border: "none",
                                  fontSize: "11px",
                                  cursor: "pointer",
                                }}
                              >
                                Rad etish
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* AI Text Response / Loading Banner */}
            {(isLoading || lastResponse) && (
              <div
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  borderRadius: "16px",
                  backgroundColor: "rgba(10, 16, 28, 0.82)",
                  backdropFilter: "blur(24px)",
                  WebkitBackdropFilter: "blur(24px)",
                  border: "1px solid rgba(56, 189, 248, 0.35)",
                  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.45)",
                  color: "#FFFFFF",
                  fontSize: "13.5px",
                  lineHeight: 1.5,
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "10px",
                }}
              >
                <div style={{ marginTop: "2px", flexShrink: 0 }}>
                  <SparklesIcon size={16} color="#38BDF8" />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: "11px", color: "#38BDF8", fontWeight: 600, marginBottom: "2px" }}>
                    {isLoading ? "Mikasa javob tayyorlamoqda..." : "Mikasa"}
                  </div>
                  <div style={{ color: "#E2E8F0", whiteSpace: "pre-wrap" }}>
                    {isLoading ? "Rejalashtirish va tahlil ketmoqda..." : lastResponse}
                  </div>
                </div>
                {!isLoading && (
                  <button
                    type="button"
                    onClick={() => setLastResponse(null)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#94A3B8",
                      cursor: "pointer",
                      padding: "4px",
                      borderRadius: "6px",
                      display: "flex",
                      alignItems: "center",
                    }}
                    title="Yopish"
                  >
                    <CloseIcon size={12} color="currentColor" />
                  </button>
                )}
              </div>
            )}
          </div>

          {/* ========================================================== */}
          {/* 3. BOTTOM VOICE BAR & LOCAL TIME IN UZBEK                  */}
          {/* ========================================================== */}
          <div
            style={{
              width: "100%",
              maxWidth: "680px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "8px",
            }}
          >
            {/* Real Uzbek Local Time and Date */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "12px",
                color: "rgba(255, 255, 255, 0.75)",
                fontWeight: 500,
                letterSpacing: "0.02em",
                textShadow: "0 1px 4px rgba(0, 0, 0, 0.6)",
              }}
            >
              <ClockIcon size={13} color="#38BDF8" />
              <span>{currentTime}</span>
            </div>

            {/* Mic Permission Toast (if error) */}
            {micError && (
              <div
                style={{
                  width: "100%",
                  padding: "8px 14px",
                  borderRadius: "12px",
                  backgroundColor: "rgba(239, 68, 68, 0.15)",
                  backdropFilter: "blur(16px)",
                  border: "1px solid rgba(239, 68, 68, 0.4)",
                  color: "#FCA5A5",
                  fontSize: "12px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "8px",
                }}
              >
                <span>{micError}</span>
                <button
                  onClick={() => setMicError(null)}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "#FCA5A5",
                    cursor: "pointer",
                    padding: "2px",
                  }}
                >
                  <CloseIcon size={12} color="currentColor" />
                </button>
              </div>
            )}

            {/* Floating Glassmorphic Voice & Composer Bar */}
            <form
              onSubmit={handleSubmit}
              className="landing-composer"
              style={{
                display: "flex",
                alignItems: "center",
                width: "100%",
                height: "56px",
                borderRadius: "24px",
                backgroundColor: "rgba(8, 14, 26, 0.78)",
                backdropFilter: "blur(26px)",
                WebkitBackdropFilter: "blur(26px)",
                border: "1px solid rgba(56, 189, 248, 0.28)",
                boxShadow:
                  "0 10px 36px rgba(0, 0, 0, 0.5), 0 0 24px rgba(2, 132, 199, 0.15), inset 0 1px 1px rgba(255, 255, 255, 0.15)",
                padding: "5px 8px 5px 16px",
                gap: "10px",
                transition: "all 0.2s ease",
              }}
            >
              {/* Attachment File input */}
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
                aria-label="Fayl biriktirish"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "32px",
                  height: "32px",
                  borderRadius: "10px",
                  color: "rgba(255, 255, 255, 0.65)",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  flexShrink: 0,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)";
                  e.currentTarget.style.color = "#FFFFFF";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color = "rgba(255, 255, 255, 0.65)";
                }}
              >
                <AttachIcon size={18} />
              </button>

              {/* Text input */}
              <input
                ref={inputRef}
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Nima yordam kerak? Mikasa tayyor..."
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: "#FFFFFF",
                  fontSize: "14.5px",
                  fontWeight: 400,
                  letterSpacing: "0.01em",
                }}
              />

              {/* Voice Toggle Button */}
              <button
                type="button"
                onClick={handleVoiceToggle}
                title={orbState === "listening" ? "Ovozni to'xtatish" : "Ovozli gapirish"}
                aria-label="Ovozli gapirish"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "36px",
                  height: "36px",
                  borderRadius: "12px",
                  backgroundColor:
                    orbState === "listening" ? "rgba(244, 63, 94, 0.25)" : "rgba(255, 255, 255, 0.06)",
                  border: `1px solid ${
                    orbState === "listening" ? "rgba(244, 63, 94, 0.6)" : "rgba(255, 255, 255, 0.1)"
                  }`,
                  color: orbState === "listening" ? "#F43F5E" : "#38BDF8",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  flexShrink: 0,
                }}
              >
                <MicIcon size={18} color="currentColor" />
              </button>

              {/* Send Button */}
              <button
                type="submit"
                title="Yuborish"
                aria-label="Yuborish"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "38px",
                  height: "38px",
                  borderRadius: "50%",
                  backgroundColor: "#0284C7",
                  boxShadow: "0 0 16px rgba(56, 189, 248, 0.55), inset 0 1px 1px rgba(255, 255, 255, 0.4)",
                  color: "#FFFFFF",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  flexShrink: 0,
                  border: "1px solid rgba(56, 189, 248, 0.5)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = "#0369A1";
                  e.currentTarget.style.transform = "scale(1.05)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = "#0284C7";
                  e.currentTarget.style.transform = "scale(1)";
                }}
              >
                <ArrowUpIcon size={16} color="#FFFFFF" />
              </button>
            </form>
          </div>
        </main>

        {/* ------------------------------------------------------------ */}
        {/* RIGHT PANEL: MENING VAZIFALARIM (Scheduler Tasks)           */}
        {/* ------------------------------------------------------------ */}
        {rightPanelOpen && (
          <aside
            className="glass-panel-tasks"
            style={{
              width: "270px",
              height: "100%",
              backgroundColor: "rgba(8, 14, 26, 0.68)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              borderLeft: "1px solid rgba(255, 255, 255, 0.08)",
              padding: "18px 16px",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
              overflowY: "auto",
              flexShrink: 0,
              zIndex: 10,
              animation: "fadeIn 0.2s ease",
            }}
          >
            {/* Header */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
                paddingBottom: "10px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <SchedulerIcon size={16} color="#10B981" />
                <span style={{ fontSize: "13.5px", fontWeight: 700, color: "#F8FAFC" }}>
                  Mening vazifalarim
                </span>
              </div>
              <button
                onClick={() => onNavigate("/scheduler")}
                title="Yangi vazifa qo'shish"
                style={{
                  background: "rgba(16, 185, 129, 0.15)",
                  border: "1px solid rgba(16, 185, 129, 0.35)",
                  color: "#34D399",
                  cursor: "pointer",
                  padding: "3px 8px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 600,
                }}
              >
                + Qo'shish
              </button>
            </div>

            {/* Tasks List */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 1, overflowY: "auto" }}>
              {tasks && tasks.length > 0 ? (
                tasks.map((task) => (
                  <div
                    key={task.id || task.task_id}
                    onClick={() => onNavigate("/scheduler")}
                    style={{
                      padding: "10px 12px",
                      borderRadius: "12px",
                      backgroundColor: "rgba(14, 22, 38, 0.6)",
                      border: "1px solid rgba(255, 255, 255, 0.06)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = "rgba(20, 32, 54, 0.75)";
                      e.currentTarget.style.borderColor = "rgba(16, 185, 129, 0.35)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = "rgba(14, 22, 38, 0.6)";
                      e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.06)";
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: "4px",
                          backgroundColor: task.completed
                            ? "rgba(56, 189, 248, 0.15)"
                            : "rgba(16, 185, 129, 0.15)",
                          color: task.completed ? "#38BDF8" : "#34D399",
                        }}
                      >
                        {task.completed ? "Bajarildi" : task.repeat ? "Takroriy" : "Faol"}
                      </span>
                      <span style={{ fontSize: "10px", color: "#64748B" }}>
                        {task.run_at ? task.run_at.slice(0, 16) : "Rejalashtirilgan"}
                      </span>
                    </div>

                    <div style={{ fontSize: "12px", fontWeight: 600, color: "#F1F5F9", lineHeight: 1.3 }}>
                      {task.data?.text || task.type || "Rejalashtirilgan amal"}
                    </div>
                  </div>
                ))
              ) : (
                <div
                  style={{
                    padding: "24px 12px",
                    textAlign: "center",
                    borderRadius: "12px",
                    backgroundColor: "rgba(14, 22, 38, 0.4)",
                    border: "1px dashed rgba(255, 255, 255, 0.08)",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <SchedulerIcon size={24} color="#64748B" />
                  <span style={{ fontSize: "12px", color: "#94A3B8" }}>
                    Hozircha faol vazifalar yo'q
                  </span>
                  <button
                    onClick={() => onNavigate("/scheduler")}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "8px",
                      backgroundColor: "rgba(56, 189, 248, 0.15)",
                      border: "1px solid rgba(56, 189, 248, 0.3)",
                      color: "#38BDF8",
                      fontSize: "11.5px",
                      fontWeight: 600,
                      cursor: "pointer",
                      marginTop: "4px",
                    }}
                  >
                    Reja yaratish
                  </button>
                </div>
              )}
            </div>

            {/* Quick Daily Plan Helper Card */}
            <div
              style={{
                padding: "12px",
                borderRadius: "12px",
                backgroundColor: "rgba(16, 185, 129, 0.08)",
                border: "1px solid rgba(16, 185, 129, 0.25)",
                display: "flex",
                flexDirection: "column",
                gap: "6px",
              }}
            >
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#A7F3D0" }}>
                Bugungi kun rejasi
              </div>
              <p style={{ fontSize: "11px", color: "#6EE7B7", margin: 0, lineHeight: 1.3 }}>
                Mikasa kunlik jadvalingizni avtomatik rejalashtirishi mumkin.
              </p>
              <button
                onClick={() => handleRunQuery("Bugungi kunim uchun maqbul va samarali ish rejasini tuzishga yordam ber")}
                style={{
                  marginTop: "4px",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  backgroundColor: "#059669",
                  border: "none",
                  color: "#FFFFFF",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                  textAlign: "center",
                }}
              >
                Rejalashtirishni boshlash
              </button>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
};

export default LandingPage;
