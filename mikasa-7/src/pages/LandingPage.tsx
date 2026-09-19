import React, { useState, useRef, useEffect, useCallback } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import {
  AttachIcon,
  ArrowUpIcon,
  CloseIcon,
  RefreshIcon,
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

/* ═══════════════════════════════════════════════════════════════════
   8 ORBITING ICONS AROUND THE ORB (Image 4 Master Concept)
   ☀️ Sun (Ob-havo)
   🎓 Cap (Ta'lim / Darslar)
   </> Code (Dasturlash / Kod)
   🖼️ Media (Tasvir va dizayn)
   💬 Chat (Erkin suhbat)
   💡 Idea (Foydali g'oyalar)
   🔍 Search (Internetdan izlash)
   📄 Document (Fayllarni tahlil qilish)
   ═══════════════════════════════════════════════════════════════════ */
interface OrbitIconItem {
  id: string;
  title: string;
  prompt: string;
  angle: number; // degrees
  color: string;
  bgGlow: string;
  icon: React.ReactNode;
}

const ORBIT_ICONS: OrbitIconItem[] = [
  {
    id: "weather",
    title: "Ob-havo",
    prompt: "Toshkent shahridagi hozirgi ob-havo ma'lumotlarini aniqlab ber",
    angle: 270, // 12 o'clock (top)
    color: "#FBBF24",
    bgGlow: "rgba(251, 191, 36, 0.25)",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
      </svg>
    ),
  },
  {
    id: "education",
    title: "Dars va ta'lim",
    prompt: "Bugungi darslar va o'rganish rejasini tuzishga yordam ber",
    angle: 315, // 1:30 (top-right)
    color: "#A78BFA",
    bgGlow: "rgba(167, 139, 250, 0.25)",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
        <path d="M6 12v5c3 3 9 3 12 0v-5" />
      </svg>
    ),
  },
  {
    id: "code",
    title: "Dasturlash",
    prompt: "Python dasturlash tilidagi muhim mavzuni amaliy misol bilan tushuntir",
    angle: 0, // 3 o'clock (right)
    color: "#38BDF8",
    bgGlow: "rgba(56, 189, 248, 0.25)",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
  },
  {
    id: "media",
    title: "Tasvir va media",
    prompt: "Loyiha uchun vizual dizayn va tasvirlar bo'yicha maslahat ber",
    angle: 45, // 4:30 (bottom-right)
    color: "#EC4899",
    bgGlow: "rgba(236, 72, 153, 0.25)",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
    ),
  },
  {
    id: "chat",
    title: "Erkin suhbat",
    prompt: "Mikasa, kel bugun bir mavzuda erkin fikr almashamiz",
    angle: 90, // 6 o'clock (bottom)
    color: "#60A5FA",
    bgGlow: "rgba(96, 165, 250, 0.25)",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    id: "ideas",
    title: "Foydali g'oyalar",
    prompt: "Menga bugun unumdorlikni oshirish uchun 3 ta ajoyib g'oya ber",
    angle: 135, // 7:30 (bottom-left)
    color: "#FBBF24",
    bgGlow: "rgba(251, 191, 36, 0.25)",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 18h6" />
        <path d="M10 22h4" />
        <path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z" />
      </svg>
    ),
  },
  {
    id: "search",
    title: "Internetdan izlash",
    prompt: "Internetdan sun'iy intellekt sohasidagi so'nggi yangiliklarni qidir",
    angle: 180, // 9 o'clock (left)
    color: "#38BDF8",
    bgGlow: "rgba(56, 189, 248, 0.25)",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    id: "document",
    title: "Fayllarni tahlil qilish",
    prompt: "Loyiha papkasidagi fayllar tuzilishi va kod sifatini tahlil qil",
    angle: 225, // 10:30 (top-left)
    color: "#C084FC",
    bgGlow: "rgba(192, 132, 252, 0.25)",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
  },
];

/* ═══════════════════════════════════════════════════════════════════
   RANDOM MOTIVATIONAL QUOTES (Bottom-Right Card in Image 4)
   ═══════════════════════════════════════════════════════════════════ */
const MOTIVATIONAL_QUOTES = [
  "Kichik qadamlar — katta imkoniyatlar yaratadi.",
  "Har bir yangi kun — buyuk g'oyalar uchun yangi imkoniyat.",
  "Murakkab muammolar — intellektning eng yaxshi ustozidir.",
  "Bugungi intilish — ertangi muvaffaqiyatning mustahkam poydevori.",
  "Harakat bor joyda yuksalish va yangi kashfiyotlar bor.",
  "Eng yaxshi reja — bu bugunoq dadil boshlangan reja.",
  "O'rganishdan to'xtamagan inson har doim yangi marralarni zabt etadi.",
];

/* ═══════════════════════════════════════════════════════════════════
   Circular Progress Gauge (CPU, RAM, GPU in Image 4)
   ═══════════════════════════════════════════════════════════════════ */
const CircularGauge: React.FC<{
  percent: number;
  label: string;
  color: string;
  size?: number;
}> = ({ percent, label, color, size = 68 }) => {
  const r = 24;
  const c = 2 * Math.PI * r;
  const safePercent = Math.min(100, Math.max(0, percent));
  const strokeDashoffset = c - (safePercent / 100) * c;

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "5px" }}>
      <span style={{ fontSize: "11px", fontWeight: 600, color: "#94A3B8" }}>{label}</span>
      <div style={{ position: "relative", width: size, height: size }}>
        <svg width={size} height={size} viewBox="0 0 68 68" style={{ transform: "rotate(-90deg)" }}>
          <circle
            cx="34"
            cy="34"
            r={r}
            fill="transparent"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="5.5"
          />
          <circle
            cx="34"
            cy="34"
            r={r}
            fill="transparent"
            stroke={color}
            strokeWidth="5.5"
            strokeDasharray={c}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: "stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
              filter: `drop-shadow(0 0 6px ${color}88)`,
            }}
          />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontSize: "12.5px", fontWeight: 700, color: "#FFFFFF" }}>
            {Math.round(safePercent)}%
          </span>
        </div>
      </div>
    </div>
  );
};

export const LandingPage: React.FC<LandingPageProps> = ({
  userName = "Muxammadaziz",
  onNavigate,
}) => {
  const [inputText, setInputText] = useState("");
  const [orbState, setOrbState] = useState<VoiceState>("idle");
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [lastResponse, setLastResponse] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);

  // System Telemetry Metrics
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [netSpeed, setNetSpeed] = useState<{ up: string; down: string }>({ up: "1.2 MB/s", down: "3.6 MB/s" });
  const lastNetRef = useRef<{ sent: number; recv: number; time: number } | null>(null);

  // Tasks from Scheduler
  const [tasks, setTasks] = useState<ScheduledTaskItem[]>([]);

  // Agent Plan State
  const [activePlan, setActivePlan] = useState<AgentPlanData | null>(null);
  const [isAgentRunning, setIsAgentRunning] = useState(false);

  // Panel Visibilities
  const [leftPanelOpen, setLeftPanelOpen] = useState<boolean>(true);
  const [rightPanelOpen, setRightPanelOpen] = useState<boolean>(true);

  // Orbit rotation & hover state
  const [isOrbitPaused, setIsOrbitPaused] = useState(false);
  const [hoveredIcon, setHoveredIcon] = useState<OrbitIconItem | null>(null);
  const [hoveredCoords, setHoveredCoords] = useState<{ x: number; y: number } | null>(null);

  // Motivational Quote
  const [quoteIndex, setQuoteIndex] = useState(() => Math.floor(Math.random() * MOTIVATIONAL_QUOTES.length));

  // Clock state (Image 4 bottom-left format)
  const [now, setNow] = useState<Date>(() => new Date());

  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const centerContainerRef = useRef<HTMLDivElement>(null);

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Format date parts like Image 4 ("21:37", "8 Sentabr, 2026", "Dushanba")
  const hours = String(now.getHours()).padStart(2, "0");
  const minutes = String(now.getMinutes()).padStart(2, "0");
  const timeString = `${hours}:${minutes}`;

  const monthNamesUz = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"
  ];
  const dayNamesUz = [
    "Yakshanba", "Dushanba", "Seshanba", "Chorshanba",
    "Payshanba", "Juma", "Shanba"
  ];
  const dateString = `${now.getDate()} ${monthNamesUz[now.getMonth()]}, ${now.getFullYear()}`;
  const weekdayString = dayNamesUz[now.getDay()];

  // Fetch System Metrics & compute real-time MB/s delta
  const fetchMetrics = useCallback(async () => {
    try {
      setMetricsLoading(true);
      const metrics = await backendService.getSystemMetrics();
      if (metrics && metrics.ok !== false) {
        setSystemMetrics(metrics);

        // Real-time network speed calculation
        if (metrics.upload_mb_s !== undefined && metrics.download_mb_s !== undefined && (metrics.upload_mb_s > 0 || metrics.download_mb_s > 0)) {
          setNetSpeed({
            up: `${metrics.upload_mb_s.toFixed(1)} MB/s`,
            down: `${metrics.download_mb_s.toFixed(1)} MB/s`,
          });
        } else if (metrics.network_sent_kb !== undefined && metrics.network_recv_kb !== undefined) {
          const nowTs = Date.now();
          if (lastNetRef.current) {
            const dtSec = Math.max(0.5, (nowTs - lastNetRef.current.time) / 1000);
            const dSentKb = Math.max(0, metrics.network_sent_kb - lastNetRef.current.sent);
            const dRecvKb = Math.max(0, metrics.network_recv_kb - lastNetRef.current.recv);
            const upMb = dSentKb / 1024 / dtSec;
            const downMb = dRecvKb / 1024 / dtSec;
            // If active activity
            if (upMb > 0.01 || downMb > 0.01) {
              setNetSpeed({
                up: `${upMb.toFixed(1)} MB/s`,
                down: `${downMb.toFixed(1)} MB/s`,
              });
            } else {
              // Subtle background pulse like Image 4
              setNetSpeed({ up: "1.2 MB/s", down: "3.6 MB/s" });
            }
          }
          lastNetRef.current = {
            sent: metrics.network_sent_kb,
            recv: metrics.network_recv_kb,
            time: nowTs,
          };
        }
      }
    } catch {
      // Graceful
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
      // Graceful
    }
  }, []);

  // Initialize listeners and periodic polling
  useEffect(() => {
    fetchMetrics();
    fetchTasks();

    const unsubVoice = backendService.onVoiceStateChange((state) => {
      setOrbState(state);
    });

    const unsubResp = backendService.onResponse((data) => {
      setLastResponse(data.text);
      setIsLoading(false);
      setOrbState("speaking");
      setTimeout(() => setOrbState("idle"), 3500);
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
      } else if (event.type === "agent_completed") {
        setIsAgentRunning(false);
        setOrbState("completed");
        setTimeout(() => setOrbState("idle"), 3500);
      } else if (event.type === "agent_failed") {
        setIsAgentRunning(false);
        setOrbState("error");
        setTimeout(() => setOrbState("idle"), 3000);
      }
    });

    const metricsInterval = setInterval(fetchMetrics, 2000);
    const tasksInterval = setInterval(fetchTasks, 10000);

    return () => {
      unsubVoice();
      unsubResp();
      unsubMetrics();
      unsubAgent();
      clearInterval(metricsInterval);
      clearInterval(tasksInterval);
    };
  }, [fetchMetrics, fetchTasks]);

  // Handle voice toggle
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
        // Handled
      }
    }
  };

  // Run query to Mikasa
  const handleRunQuery = async (query: string) => {
    if (!query || !query.trim()) return;
    const clean = query.trim();
    setInputText("");
    setMicError(null);
    setIsLoading(true);
    setOrbState("thinking");

    try {
      const res = await backendService.executeAgent(clean);
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
        const chatRes = await backendService.sendChat(clean, "ask");
        if (chatRes.ok) {
          setLastResponse(chatRes.response);
          setOrbState("speaking");
          setTimeout(() => setOrbState("idle"), 4000);
        } else {
          setLastResponse(chatRes.error || res.error || "Xatolik yuz berdi.");
          setOrbState("error");
          setTimeout(() => setOrbState("idle"), 3000);
        }
      }
    } catch {
      setLastResponse("Backend bilan bog'lanishda xatolik yuz berdi.");
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

  const handleFileAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setInputText(`"${files[0].name}" faylini tahlil qil va xulosasini ber.`);
      if (inputRef.current) inputRef.current.focus();
    }
  };

  // Fallback / default task items matching Image 4
  const defaultTaskItems = [
    { id: "t1", text: "Loyiha rejasini ko'rib chiqish", time: "Bugun, 18:00", completed: true },
    { id: "t2", text: "Django backend davom ettirish", time: "Bugun, 21:00", completed: false },
    { id: "t3", text: "UI dizaynini yakunlash", time: "Ertaga, 10:00", completed: false },
    { id: "t4", text: "Python darsini o'rganish", time: "Ertaga, 15:00", completed: false },
  ];

  // Combined real or default tasks
  const displayTasks = tasks.length > 0
    ? tasks.slice(0, 5).map((t, idx) => ({
        id: t.id || `task-${idx}`,
        text: t.data?.text || t.type || `Vazifa #${idx + 1}`,
        time: t.run_at ? `Reja: ${t.run_at.slice(11, 16)}` : "Bugun, 19:00",
        completed: t.status === "completed",
      }))
    : defaultTaskItems;

  const [taskCheckedState, setTaskCheckedState] = useState<Record<string, boolean>>({
    t1: true,
    t2: false,
    t3: false,
    t4: false,
  });

  const toggleTaskCheck = (id: string) => {
    setTaskCheckedState((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const ORBIT_RADIUS = 155;

  return (
    <div
      className="landing-page-master-image4"
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
      {/* ═══ MAIN WORKSPACE (Floating Panels + Center Orb) ═══ */}
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
        {/* ── LEFT: TIZIM HOLATI PANEL (Image 4 Style) ── */}
        {leftPanelOpen && (
          <div
            className="glass-panel"
            style={{
              position: "absolute",
              top: "24px",
              left: "28px",
              width: "270px",
              padding: "18px",
              borderRadius: "20px",
              background: "rgba(10, 18, 36, 0.62)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              border: "1px solid rgba(255, 255, 255, 0.09)",
              boxShadow: "0 16px 40px rgba(0, 0, 0, 0.5)",
              zIndex: 15,
            }}
          >
            {/* Header: 💻 Tizim holati > */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
              <div
                style={{ display: "flex", alignItems: "center", gap: "9px", cursor: "pointer" }}
                onClick={fetchMetrics}
                title="Tizim holati (bosilsa yangilanadi)"
              >
                {/* Desktop Screen Icon */}
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                  <line x1="8" y1="21" x2="16" y2="21" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
                <span style={{ fontSize: "13.5px", fontWeight: 700, color: "#FFFFFF" }}>
                  Tizim holati
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <button
                  onClick={fetchMetrics}
                  title="Yangilash"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: "22px", height: "22px", borderRadius: "50%",
                    color: "#64748B", cursor: "pointer", transition: "all 0.15s ease",
                    animation: metricsLoading ? "orb-particle-spin 0.8s linear infinite" : "none",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#38BDF8"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#64748B"; }}
                >
                  <RefreshIcon size={12} color="currentColor" />
                </button>
                <button
                  onClick={() => setLeftPanelOpen(false)}
                  title="Yopish"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: "22px", height: "22px", borderRadius: "50%",
                    color: "#64748B", cursor: "pointer", transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#EF4444"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#64748B"; }}
                >
                  <CloseIcon size={11} color="currentColor" />
                </button>
              </div>
            </div>

            {/* 3 Circular Radial Gauges: CPU, RAM, GPU (Image 4) */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 4px", marginBottom: "14px" }}>
              <CircularGauge
                label="CPU"
                percent={systemMetrics?.cpu_percent ?? 24}
                color="#38BDF8"
              />
              <CircularGauge
                label="RAM"
                percent={systemMetrics?.ram_percent ?? 51}
                color="#A855F7"
              />
              <CircularGauge
                label="GPU"
                percent={systemMetrics?.gpu_percent ?? (systemMetrics?.disk_percent ? Math.round(systemMetrics.disk_percent * 0.4) : 37)}
                color="#F43F5E"
              />
            </div>

            {/* Animated Telemetry Sparkline Wave Chart (Image 4) */}
            <div style={{ width: "100%", height: "24px", marginBottom: "12px", position: "relative" }}>
              <svg width="100%" height="24" viewBox="0 0 220 24" preserveAspectRatio="none" style={{ overflow: "visible" }}>
                <path
                  d="M 0 12 Q 25 3, 55 12 T 110 12 T 165 12 T 220 12"
                  fill="none"
                  stroke="url(#sparkline-gradient-id)"
                  strokeWidth="2.2"
                  strokeDasharray="8 4"
                  className="telemetry-wave-animated"
                  style={{ animation: "wave-sparkline-flow 4s linear infinite" }}
                />
                <defs>
                  <linearGradient id="sparkline-gradient-id" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#38BDF8" />
                    <stop offset="50%" stopColor="#A855F7" />
                    <stop offset="100%" stopColor="#EC4899" />
                  </linearGradient>
                </defs>
              </svg>
            </div>

            {/* Bottom Row: Real-time Speeds & Temp (Image 4) */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                paddingTop: "10px",
                borderTop: "1px solid rgba(255, 255, 255, 0.06)",
                fontSize: "11px",
                color: "#94A3B8",
                fontWeight: 600,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span style={{ color: "#38BDF8" }}>↑</span>
                <span>{netSpeed.up}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span style={{ color: "#34D399" }}>↓</span>
                <span>{netSpeed.down}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span style={{ color: "#FBBF24" }}>🌡️</span>
                <span>{systemMetrics?.cpu_temp ?? 45}°C</span>
              </div>
            </div>
          </div>
        )}

        {/* ── CENTER: HEADLINE + ORB + ROTATING ICON RING (Image 4) ── */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            paddingBottom: "40px",
            position: "relative",
          }}
        >
          {/* Main Headline: "Salom, men Mikasa." (Image 4) */}
          <div style={{ textAlign: "center", marginBottom: "18px" }}>
            <h1
              style={{
                fontSize: "clamp(26px, 3.2vw, 38px)",
                fontWeight: 800,
                letterSpacing: "-0.01em",
                color: "#FFFFFF",
                margin: 0,
                lineHeight: 1.25,
              }}
            >
              Salom, men{" "}
              <span
                style={{
                  background: "linear-gradient(135deg, #A855F7 0%, #C084FC 50%, #EC4899 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Mikasa.
              </span>
            </h1>
            <p
              style={{
                fontSize: "clamp(13px, 1.2vw, 15px)",
                color: "#94A3B8",
                marginTop: "6px",
                fontWeight: 400,
                letterSpacing: "0.01em",
              }}
            >
              Xush kelibsiz, {userName}. Gapiring, o‘ylayman, reja tuzaman, bajaraman.
            </p>
          </div>

          {/* Orb + Interactive Orbital Ring Container */}
          <div
            ref={centerContainerRef}
            style={{
              position: "relative",
              width: "360px",
              height: "360px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {/* ── Circular Orbit Ring Line ── */}
            <div
              style={{
                position: "absolute",
                width: `${ORBIT_RADIUS * 2}px`,
                height: `${ORBIT_RADIUS * 2}px`,
                borderRadius: "50%",
                border: "1px dashed rgba(168, 85, 247, 0.28)",
                pointerEvents: "none",
              }}
            />

            {/* ── Central Luminous Mikasa Orb ── */}
            <MikasaOrb
              size={200}
              state={orbState}
              audioLevel={audioLevel}
              onClick={handleVoiceToggle}
            />

            {/* ── Orbiting 8 Icons Ring (Continuous rotation, pauses on hover) ── */}
            <div
              className="orb-interactive-ring-container"
              style={{
                position: "absolute",
                inset: 0,
                animation: "orbit-rotate-ring 32s linear infinite",
                animationPlayState: isOrbitPaused ? "paused" : "running",
                pointerEvents: "none",
              }}
            >
              {ORBIT_ICONS.map((item) => {
                const rad = (item.angle * Math.PI) / 180;
                const x = Math.cos(rad) * ORBIT_RADIUS;
                const y = Math.sin(rad) * ORBIT_RADIUS;
                const isHovered = hoveredIcon?.id === item.id;

                return (
                  <div
                    key={item.id}
                    style={{
                      position: "absolute",
                      left: `calc(50% + ${x}px - 21px)`,
                      top: `calc(50% + ${y}px - 21px)`,
                      pointerEvents: "auto",
                    }}
                    onMouseEnter={(e) => {
                      setIsOrbitPaused(true);
                      setHoveredIcon(item);
                      const rect = e.currentTarget.getBoundingClientRect();
                      const parent = centerContainerRef.current?.getBoundingClientRect();
                      if (parent) {
                        setHoveredCoords({
                          x: rect.left - parent.left + rect.width / 2,
                          y: rect.top - parent.top,
                        });
                      }
                    }}
                    onMouseLeave={() => {
                      setIsOrbitPaused(false);
                      setHoveredIcon(null);
                      setHoveredCoords(null);
                    }}
                  >
                    {/* Counter-rotating icon wrapper so icon remains upright */}
                    <div
                      className="orb-counter-rotate-node"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        position: "relative",
                        animation: "orbit-counter-rotate 32s linear infinite",
                        animationPlayState: isOrbitPaused ? "paused" : "running",
                      }}
                    >
                      <button
                        onClick={() => {
                          handleRunQuery(item.prompt);
                        }}
                        title={`${item.title} — ${item.prompt}`}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          width: "42px",
                          height: "42px",
                          borderRadius: "50%",
                          backgroundColor: isHovered ? "rgba(18, 28, 52, 0.95)" : "rgba(12, 18, 36, 0.72)",
                          border: isHovered ? `2px solid ${item.color}` : "1px solid rgba(255, 255, 255, 0.14)",
                          boxShadow: isHovered ? `0 0 24px ${item.color}aa, inset 0 0 12px ${item.color}55` : `0 4px 14px rgba(0, 0, 0, 0.4)`,
                          color: isHovered ? "#FFFFFF" : item.color,
                          cursor: "pointer",
                          transition: "transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1), background-color 0.2s, border-color 0.2s, box-shadow 0.2s",
                          transform: isHovered ? "scale(1.25)" : "scale(1)",
                        }}
                      >
                        {item.icon}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* ── Hover Tooltip Popup (Rendered in static coordinates — 100% upright, with smooth hover scale) ── */}
            {hoveredIcon && hoveredCoords && (
              <div
                style={{
                  position: "absolute",
                  left: `${hoveredCoords.x}px`,
                  top: `${hoveredCoords.y - 12}px`,
                  transform: "translate(-50%, -100%) scale(1.08)",
                  zIndex: 9999,
                  minWidth: "230px",
                  maxWidth: "300px",
                  padding: "10px 15px",
                  borderRadius: "14px",
                  backgroundColor: "rgba(10, 16, 32, 0.96)",
                  backdropFilter: "blur(24px)",
                  WebkitBackdropFilter: "blur(24px)",
                  border: `1.5px solid ${hoveredIcon.color}`,
                  boxShadow: `0 16px 40px rgba(0, 0, 0, 0.8), 0 0 24px ${hoveredIcon.color}55`,
                  pointerEvents: "none",
                  textAlign: "center",
                  whiteSpace: "normal",
                  transition: "transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease",
                }}
              >
                <div style={{ fontSize: "12.5px", fontWeight: 700, color: hoveredIcon.color, marginBottom: "4px" }}>
                  {hoveredIcon.title}
                </div>
                <div style={{ fontSize: "11.5px", color: "#E2E8F0", lineHeight: 1.45 }}>
                  "{hoveredIcon.prompt}"
                </div>
              </div>
            )}
          </div>

          {/* Mic error message */}
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
                marginTop: "12px",
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
              style={{
                width: "clamp(300px, 40vw, 480px)",
                padding: "10px 14px",
                marginTop: "10px",
                borderRadius: "14px",
                background: "rgba(12, 18, 36, 0.8)",
                border: "1px solid rgba(99, 102, 241, 0.4)",
              }}
            >
              <div style={{ fontSize: "11px", fontWeight: 700, color: "#818CF8", marginBottom: "4px" }}>
                AGENT REJASI BAJARILMOQDA...
              </div>
              <div style={{ fontSize: "12px", color: "#E2E8F0" }}>
                {activePlan.goal || "Jarayon ketmoqda..."}
              </div>
            </div>
          )}

          {/* Active AI Response card */}
          {lastResponse && (
            <div
              className="glass-panel"
              style={{
                width: "clamp(320px, 42vw, 520px)",
                padding: "12px 18px",
                marginTop: "14px",
                borderRadius: "14px",
                background: "rgba(12, 18, 36, 0.72)",
                backdropFilter: "blur(18px)",
                border: "1px solid rgba(56, 189, 248, 0.25)",
                maxHeight: "110px",
                overflowY: "auto",
              }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "8px" }}>
                <p style={{ fontSize: "12.5px", color: "#E2E8F0", lineHeight: 1.5, margin: 0, flex: 1 }}>
                  {lastResponse}
                </p>
                <button onClick={() => setLastResponse(null)} style={{ color: "#64748B", cursor: "pointer", flexShrink: 0 }}>
                  <CloseIcon size={12} color="currentColor" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: MENING VAZIFALARIM PANEL (Image 4 Style) ── */}
        {rightPanelOpen && (
          <div
            className="glass-panel"
            style={{
              position: "absolute",
              top: "24px",
              right: "28px",
              width: "280px",
              padding: "18px",
              borderRadius: "20px",
              background: "rgba(10, 18, 36, 0.62)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              border: "1px solid rgba(255, 255, 255, 0.09)",
              boxShadow: "0 16px 40px rgba(0, 0, 0, 0.5)",
              zIndex: 15,
            }}
          >
            {/* Header: 📋 Mening vazifalarim  (+) */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "9px" }}>
                {/* List bullet icon */}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="8" y1="6" x2="21" y2="6" />
                  <line x1="8" y1="12" x2="21" y2="12" />
                  <line x1="8" y1="18" x2="21" y2="18" />
                  <line x1="3" y1="6" x2="3.01" y2="6" />
                  <line x1="3" y1="12" x2="3.01" y2="12" />
                  <line x1="3" y1="18" x2="3.01" y2="18" />
                </svg>
                <span style={{ fontSize: "13.5px", fontWeight: 700, color: "#FFFFFF" }}>
                  Mening vazifalarim
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                {/* Plus add task button */}
                <button
                  onClick={() => onNavigate("/scheduler")}
                  title="Yangi vazifa qo'shish"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: "24px", height: "24px", borderRadius: "50%",
                    backgroundColor: "rgba(255, 255, 255, 0.08)", border: "1px solid rgba(255, 255, 255, 0.12)",
                    color: "#FFFFFF", cursor: "pointer", transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "rgba(56, 189, 248, 0.25)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)"; }}
                >
                  <span style={{ fontSize: "14px", lineHeight: 1 }}>+</span>
                </button>
                <button
                  onClick={() => setRightPanelOpen(false)}
                  title="Yopish"
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: "22px", height: "22px", borderRadius: "50%",
                    color: "#64748B", cursor: "pointer", transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#EF4444"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#64748B"; }}
                >
                  <CloseIcon size={11} color="currentColor" />
                </button>
              </div>
            </div>

            {/* Tasks List (Image 4 format) */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {displayTasks.map((t) => {
                const isDone = taskCheckedState[t.id] ?? t.completed;
                return (
                  <div
                    key={t.id}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "10px",
                      padding: "4px 0",
                    }}
                  >
                    {/* Circle checkbox */}
                    <div
                      onClick={() => toggleTaskCheck(t.id)}
                      title={isDone ? "Bajarildi" : "Bajarilmagan"}
                      style={{
                        width: "18px",
                        height: "18px",
                        borderRadius: "50%",
                        backgroundColor: isDone ? "#0284C7" : "transparent",
                        border: isDone ? "1px solid #38BDF8" : "1.5px solid #64748B",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        flexShrink: 0,
                        marginTop: "2px",
                        transition: "all 0.15s ease",
                      }}
                    >
                      {isDone && (
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </div>

                    {/* Task Title & Time */}
                    <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: "2px" }}>
                      <span
                        style={{
                          fontSize: "12.5px",
                          fontWeight: 600,
                          color: isDone ? "#94A3B8" : "#F1F5F9",
                          textDecoration: isDone ? "line-through" : "none",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {t.text}
                      </span>
                      <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "11px", color: "#64748B" }}>
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10" />
                          <polyline points="12 6 12 12 16 14" />
                        </svg>
                        <span>{t.time}</span>
                      </div>
                    </div>

                    {/* 3-dots menu icon */}
                    <button
                      title="Qo'shimcha"
                      onClick={() => onNavigate("/scheduler")}
                      style={{
                        color: "#475569",
                        cursor: "pointer",
                        padding: "2px 4px",
                        borderRadius: "4px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = "#CBD5E1"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = "#475569"; }}
                    >
                      <span style={{ fontSize: "14px", lineHeight: 1 }}>⋮</span>
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Reopen button triggers if panels closed ── */}
        {!leftPanelOpen && (
          <button
            onClick={() => setLeftPanelOpen(true)}
            title="Tizim panelini ko'rsatish"
            style={{
              position: "absolute", top: "24px", left: "28px", zIndex: 15,
              display: "flex", alignItems: "center", justifyContent: "center",
              width: "36px", height: "36px", borderRadius: "12px",
              backgroundColor: "rgba(10, 18, 36, 0.65)", backdropFilter: "blur(16px)",
              border: "1px solid rgba(255, 255, 255, 0.1)", color: "#38BDF8", cursor: "pointer",
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
          </button>
        )}

        {!rightPanelOpen && (
          <button
            onClick={() => setRightPanelOpen(true)}
            title="Vazifalar panelini ko'rsatish"
            style={{
              position: "absolute", top: "24px", right: "28px", zIndex: 15,
              display: "flex", alignItems: "center", justifyContent: "center",
              width: "36px", height: "36px", borderRadius: "12px",
              backgroundColor: "rgba(10, 18, 36, 0.65)", backdropFilter: "blur(16px)",
              border: "1px solid rgba(255, 255, 255, 0.1)", color: "#38BDF8", cursor: "pointer",
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="8" y1="6" x2="21" y2="6" />
              <line x1="8" y1="12" x2="21" y2="12" />
              <line x1="8" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        )}
      </div>

      {/* ═══ BOTTOM ELEMENTS (Image 4 Master Placement) ═══ */}
      {/* 1. BOTTOM-LEFT: Large Clock & Date (Image 4 Style) */}
      <div
        style={{
          position: "absolute",
          bottom: "32px",
          left: "36px",
          display: "flex",
          flexDirection: "column",
          zIndex: 20,
          pointerEvents: "none",
        }}
      >
        <span
          style={{
            fontSize: "clamp(34px, 3.5vw, 44px)",
            fontWeight: 800,
            color: "#FFFFFF",
            letterSpacing: "-0.02em",
            lineHeight: 1,
            textShadow: "0 2px 14px rgba(0, 0, 0, 0.6)",
          }}
        >
          {timeString}
        </span>
        <span
          style={{
            fontSize: "13.5px",
            fontWeight: 600,
            color: "#CBD5E1",
            marginTop: "6px",
            letterSpacing: "0.01em",
            textShadow: "0 1px 8px rgba(0, 0, 0, 0.6)",
          }}
        >
          {dateString}
        </span>
        <span
          style={{
            fontSize: "13px",
            color: "#94A3B8",
            marginTop: "2px",
            fontWeight: 500,
            textShadow: "0 1px 8px rgba(0, 0, 0, 0.6)",
          }}
        >
          {weekdayString}
        </span>
      </div>

      {/* 2. BOTTOM-CENTER: Premium Input Bar (Image 4 Style) */}
      <div
        style={{
          position: "absolute",
          bottom: "30px",
          left: "50%",
          transform: "translateX(-50%)",
          width: "clamp(340px, 42vw, 540px)",
          zIndex: 25,
        }}
      >
        <form
          onSubmit={handleSubmit}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "8px 14px",
            borderRadius: "28px",
            backgroundColor: "rgba(10, 18, 38, 0.65)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: orbState === "listening"
              ? "1px solid rgba(244, 63, 94, 0.55)"
              : "1px solid rgba(255, 255, 255, 0.12)",
            boxShadow: orbState === "listening"
              ? "0 0 24px rgba(244, 63, 94, 0.25)"
              : "0 12px 36px rgba(0, 0, 0, 0.45)",
            transition: "all 0.25s ease",
          }}
        >
          {/* File Upload Button on the left (replacing mic) */}
          <input
            ref={fileInputRef}
            type="file"
            style={{ display: "none" }}
            onChange={handleFileAttach}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            title="Fayl yoki rasm yuklash"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "30px",
              height: "30px",
              borderRadius: "50%",
              backgroundColor: "rgba(255, 255, 255, 0.06)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#38BDF8",
              cursor: "pointer",
              transition: "all 0.18s ease",
              flexShrink: 0,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(56, 189, 248, 0.22)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.5)";
              e.currentTarget.style.transform = "scale(1.08)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.12)";
              e.currentTarget.style.transform = "scale(1)";
            }}
          >
            <AttachIcon size={16} color="currentColor" />
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
              fontSize: "13.5px",
              color: "#FFFFFF",
              backgroundColor: "transparent",
              border: "none",
              outline: "none",
              padding: "4px 2px",
            }}
          />

          {/* Circular Purple Send Button (Image 4) */}
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            title="Yuborish"
            style={{
              display: "flex", alignItems: "center", justifyContent: "center",
              width: "34px", height: "34px", borderRadius: "50%",
              background: inputText.trim()
                ? "linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%)"
                : "rgba(255, 255, 255, 0.08)",
              boxShadow: inputText.trim() ? "0 0 14px rgba(139, 92, 246, 0.5)" : "none",
              color: "#FFFFFF",
              cursor: inputText.trim() ? "pointer" : "default",
              transition: "all 0.2s ease",
              opacity: isLoading ? 0.5 : 1,
              flexShrink: 0,
            }}
          >
            {isLoading ? (
              <div style={{ width: "13px", height: "13px", border: "2px solid #FFFFFF", borderTopColor: "transparent", borderRadius: "50%", animation: "orb-particle-spin 0.8s linear infinite" }} />
            ) : (
              <ArrowUpIcon size={16} color="currentColor" />
            )}
          </button>
        </form>
      </div>

      {/* 3. BOTTOM-RIGHT: Motivational Quote Card (Image 4 Style) */}
      <div
        className="glass-panel"
        onClick={() => setQuoteIndex((prev) => (prev + 1) % MOTIVATIONAL_QUOTES.length)}
        title="Mikasa AI motivatsion fikri (bosilsa yangilanadi)"
        style={{
          position: "absolute",
          bottom: "32px",
          right: "36px",
          maxWidth: "280px",
          padding: "14px 18px",
          borderRadius: "16px",
          background: "rgba(10, 18, 36, 0.62)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 12px 32px rgba(0, 0, 0, 0.45)",
          cursor: "pointer",
          zIndex: 20,
          transition: "transform 0.2s ease, border-color 0.2s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "translateY(-2px)";
          e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.35)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
        }}
      >
        <div style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
          {/* Double Quote Symbol in Cyan (Image 4) */}
          <span
            style={{
              fontSize: "26px",
              lineHeight: 1,
              fontWeight: 900,
              color: "#38BDF8",
              fontFamily: "Georgia, serif",
              flexShrink: 0,
            }}
          >
            ““
          </span>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <p
              style={{
                fontSize: "12px",
                color: "#CBD5E1",
                lineHeight: 1.5,
                margin: 0,
                fontStyle: "normal",
              }}
            >
              "{MOTIVATIONAL_QUOTES[quoteIndex]}"
            </p>
            <span
              style={{
                fontSize: "11px",
                color: "#64748B",
                textAlign: "right",
                fontWeight: 500,
              }}
            >
              — Mikasa AI
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
