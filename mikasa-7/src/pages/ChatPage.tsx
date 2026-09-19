// ========== ChatPage.tsx ==========
// Mikasa AI 7.x — Production AI Messaging Interface [Phase 9]
// Inspired by Quiet Intelligence, modern messaging layouts, and desktop speed

import React, { useState, useEffect, useRef } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import { MarkdownView } from "../components/MarkdownView";
import {
  SparklesIcon,
  ArrowUpIcon,
  TrashIcon,
  HomeIcon,
  AttachIcon,
  CopyIcon,
  CheckIcon,
  RefreshIcon,
  PlusIcon,
  ImageIcon,
  CollapseSidebarIcon,
  ExpandSidebarIcon,
  ChatIcon,
} from "../components/icons/Icons";
import { backendService, BackendStatus } from "../services/backendService";

export interface Message {
  id: string;
  sender: "user" | "mikasa";
  text: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: Message[];
}

export interface ChatGalleryImage {
  id: string;
  url: string;
  prompt?: string;
  timestamp: string;
  sessionId?: string;
}

interface ChatPageProps {
  initialPrompt?: string;
  userName?: string;
  onNavigateHome: () => void;
  onNavigateVoice?: () => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({
  initialPrompt,
  userName = "Ustoz",
  onNavigateHome,
}) => {
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    try {
      const raw = localStorage.getItem("mikasa_chat_sessions");
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
    return [];
  });

  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    return localStorage.getItem("mikasa_active_session_id") || "session_default";
  });

  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [sidebarTab, setSidebarTab] = useState<"chats" | "images">("chats");
  const [previewImage, setPreviewImage] = useState<ChatGalleryImage | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({ status: "connecting" });
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Agentic Multi-Step State (Planning & Reasoning 2.0)
  const [activeAgent, setActiveAgent] = useState<{
    planId: string;
    goal: string;
    status: "running" | "paused" | "completed" | "failed" | "aborted";
    planVersion?: number;
    replanCount?: number;
    replanReason?: string;
    steps: Array<{
      step_id: string;
      order: number;
      tool: string;
      capability?: string;
      dependencies?: string[];
      status: "pending" | "running" | "completed" | "failed" | "waiting_confirmation" | "blocked";
      reason?: string;
    }>;
    confirmation?: {
      stepId: string;
      tool: string;
      risk: string;
      prompt: string;
    } | null;
  } | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const initialSentRef = useRef(false);

  const userDisplayName = userName || backendStatus.user || "Ustoz";
  const userInitials = userDisplayName
    .trim()
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() || "U";

  // Backend status subscription
  useEffect(() => {
    const unsub = backendService.onStatusChange((s) => setBackendStatus(s));
    return () => unsub();
  }, []);

  // Agent Events Subscription
  useEffect(() => {
    const unsub = backendService.onAgentEvent((evt) => {
      if (evt.type === "agent_plan_created") {
        setActiveAgent({
          planId: evt.data.plan_id,
          goal: evt.data.goal || "Vazifa bajarilmoqda",
          status: "running",
          planVersion: evt.data.plan_version || 1,
          replanCount: 0,
          steps: [],
          confirmation: null,
        });
      } else if (evt.type === "agent_plan_replanned") {
        setActiveAgent((prev) => {
          if (!prev) return prev;
          const steps = prev.steps.map((s) =>
            s.step_id === evt.data.step_id
              ? { ...s, tool: evt.data.tool || s.tool, status: "running" as const }
              : s
          );
          return {
            ...prev,
            steps,
            planVersion: evt.data.version || (prev.planVersion ? prev.planVersion + 1 : 2),
            replanCount: evt.data.replan_count || (prev.replanCount ? prev.replanCount + 1 : 1),
            replanReason: evt.data.reason,
          };
        });
      } else if (evt.type === "agent_step_started") {
        setActiveAgent((prev) => {
          if (!prev) return prev;
          const existing = prev.steps.find((s) => s.step_id === evt.data.step_id);
          const steps = existing
            ? prev.steps.map((s) => (s.step_id === evt.data.step_id ? { ...s, status: "running" as const } : s))
            : [
                ...prev.steps,
                {
                  step_id: evt.data.step_id,
                  order: evt.data.order,
                  tool: evt.data.tool,
                  capability: evt.data.capability,
                  dependencies: evt.data.dependencies,
                  status: "running" as const,
                },
              ];
          return { ...prev, steps, status: "running" };
        });
      } else if (evt.type === "agent_step_completed") {
        setActiveAgent((prev) => {
          if (!prev) return prev;
          const steps = prev.steps.map((s) =>
            s.step_id === evt.data.step_id ? { ...s, status: "completed" as const } : s
          );
          return { ...prev, steps };
        });
      } else if (evt.type === "agent_verification") {
        setActiveAgent((prev) => {
          if (!prev) return prev;
          const steps = prev.steps.map((s) =>
            s.step_id === evt.data.step_id ? { ...s, reason: evt.data.reason } : s
          );
          return { ...prev, steps };
        });
      } else if (evt.type === "agent_confirmation_required") {
        setActiveAgent((prev) => {
          if (!prev) return prev;
          const steps = prev.steps.map((s) =>
            s.step_id === evt.data.step_id ? { ...s, status: "waiting_confirmation" as const } : s
          );
          return {
            ...prev,
            status: "paused",
            steps,
            confirmation: {
              stepId: evt.data.step_id,
              tool: evt.data.tool,
              risk: evt.data.risk,
              prompt: evt.data.prompt,
            },
          };
        });
      } else if (evt.type === "agent_completed") {
        setActiveAgent((prev) => (prev ? { ...prev, status: "completed", confirmation: null } : null));
      } else if (evt.type === "agent_aborted") {
        setActiveAgent((prev) => (prev ? { ...prev, status: "aborted", confirmation: null } : null));
      }
    });
    return () => unsub();
  }, []);

  // Initial load: restore sessions or sync from backend memory
  useEffect(() => {
    const raw = localStorage.getItem("mikasa_chat_sessions");
    if (!raw || JSON.parse(raw).length === 0) {
      const loadHistory = async () => {
        try {
          const mem = await backendService.getMemory();
          let initialMsgs: Message[] = [];
          if (mem.ok && mem.conversations && mem.conversations.length > 0) {
            mem.conversations.forEach((c, idx) => {
              if (c.user) {
                initialMsgs.push({
                  id: `hist-u-${idx}`,
                  sender: "user",
                  text: c.user,
                  timestamp: c.time || "",
                });
              }
              if (c.agent) {
                initialMsgs.push({
                  id: `hist-a-${idx}`,
                  sender: "mikasa",
                  text: c.agent,
                  timestamp: c.time || "",
                });
              }
            });
          }
          const defaultSession: ChatSession = {
            id: "session_default",
            title: initialMsgs.length > 0 ? (initialMsgs[0].text.slice(0, 28) + (initialMsgs[0].text.length > 28 ? "..." : "")) : "Boshlang'ich suhbat",
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: initialMsgs,
          };
          setSessions([defaultSession]);
          setActiveSessionId("session_default");
          setMessages(initialMsgs);
          try {
            localStorage.setItem("mikasa_chat_sessions", JSON.stringify([defaultSession]));
            localStorage.setItem("mikasa_active_session_id", "session_default");
          } catch {}
        } catch {}
      };
      loadHistory();
    } else {
      try {
        const parsed: ChatSession[] = JSON.parse(raw);
        const savedActiveId = localStorage.getItem("mikasa_active_session_id") || parsed[0]?.id || "session_default";
        const current = parsed.find((s) => s.id === savedActiveId) || parsed[0];
        if (current) {
          setActiveSessionId(current.id);
          setMessages(current.messages || []);
        }
      } catch {}
    }
  }, []);

  // Extract all gallery images from messages across all sessions
  const allGalleryImages = React.useMemo(() => {
    const list: ChatGalleryImage[] = [];
    const seen = new Set<string>();

    sessions.forEach((sess) => {
      sess.messages.forEach((msg) => {
        // Markdown image: ![alt](url)
        const mdRegex = /!\[(.*?)\]\(((?:https?:\/\/|data:image\/|\/)[^\s\)]+)\)/g;
        let m;
        while ((m = mdRegex.exec(msg.text)) !== null) {
          const url = m[2];
          if (!seen.has(url)) {
            seen.add(url);
            list.push({
              id: `${sess.id}_img_${list.length}`,
              url,
              prompt: m[1] || "AI tomonidan yaratilgan tasvir",
              timestamp: msg.timestamp,
              sessionId: sess.id,
            });
          }
        }
        // Direct image URLs
        const directRegex = /(https?:\/\/[^\s"'<>]+\.(?:png|jpg|jpeg|webp|svg|gif))/gi;
        while ((m = directRegex.exec(msg.text)) !== null) {
          const url = m[1];
          if (!seen.has(url)) {
            seen.add(url);
            list.push({
              id: `${sess.id}_img_${list.length}`,
              url,
              prompt: "AI tasviri",
              timestamp: msg.timestamp,
              sessionId: sess.id,
            });
          }
        }
      });
    });

    return list;
  }, [sessions]);

  // Handle "+ Yangi suhbat" (New Chat)
  const handleNewChat = () => {
    const newId = "session_" + Date.now();
    const newSession: ChatSession = {
      id: newId,
      title: "Yangi suhbat",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: [],
    };
    setSessions((prev) => {
      const next = [newSession, ...prev];
      try {
        localStorage.setItem("mikasa_chat_sessions", JSON.stringify(next));
      } catch {}
      return next;
    });
    setActiveSessionId(newId);
    setMessages([]);
    try {
      localStorage.setItem("mikasa_active_session_id", newId);
    } catch {}
    setTimeout(() => textareaRef.current?.focus(), 80);
  };

  // Handle selecting chat session
  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
    try {
      localStorage.setItem("mikasa_active_session_id", id);
    } catch {}
    const target = sessions.find((s) => s.id === id);
    setMessages(target?.messages || []);
  };

  // Handle deleting a chat session
  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessions((prev) => {
      const remaining = prev.filter((s) => s.id !== id);
      if (remaining.length === 0) {
        const freshId = "session_" + Date.now();
        const fresh: ChatSession = {
          id: freshId,
          title: "Yangi suhbat",
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: [],
        };
        setActiveSessionId(freshId);
        setMessages([]);
        try {
          localStorage.setItem("mikasa_chat_sessions", JSON.stringify([fresh]));
          localStorage.setItem("mikasa_active_session_id", freshId);
        } catch {}
        return [fresh];
      } else {
        try {
          localStorage.setItem("mikasa_chat_sessions", JSON.stringify(remaining));
        } catch {}
        if (activeSessionId === id) {
          setActiveSessionId(remaining[0].id);
          setMessages(remaining[0].messages || []);
          try {
            localStorage.setItem("mikasa_active_session_id", remaining[0].id);
          } catch {}
        }
        return remaining;
      }
    });
  };

  // Auto-scroll to bottom on new messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Handle initial prompt from landing page or command palette
  useEffect(() => {
    if (initialPrompt && !initialSentRef.current) {
      initialSentRef.current = true;
      handleSendMessage(initialPrompt);
    }
  }, [initialPrompt]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend !== undefined ? textToSend : input).trim();
    if (!query || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const newMessagesWithUser = [...messages, userMsg];
    setMessages(newMessagesWithUser);

    // Synchronize user message with session state & localStorage
    setSessions((prev) => {
      const target = prev.find((s) => s.id === activeSessionId);
      const isGenericTitle = !target || target.title === "Yangi suhbat" || target.title === "Boshlang'ich suhbat";
      const title = isGenericTitle ? (query.slice(0, 30) + (query.length > 30 ? "..." : "")) : target.title;
      const updated = prev.map((s) =>
        s.id === activeSessionId
          ? { ...s, title, updatedAt: Date.now(), messages: newMessagesWithUser }
          : s
      );
      try {
        localStorage.setItem("mikasa_chat_sessions", JSON.stringify(updated));
      } catch {}
      return updated;
    });

    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setIsLoading(true);

    try {
      const res = await backendService.sendChat(query, "ask");
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "mikasa",
        text: res.ok ? res.response : `**Javob qaytarishda xatolik**\n\n${res.error || "Backend so'rovni qayta ishlay olmadi."}\n\nQayta urinib ko'ring yoki boshqa savolni so'rang.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => {
        const next = [...prev, botMsg];
        setSessions((prevSessions) => {
          const updated = prevSessions.map((s) =>
            s.id === activeSessionId
              ? { ...s, updatedAt: Date.now(), messages: next }
              : s
          );
          try {
            localStorage.setItem("mikasa_chat_sessions", JSON.stringify(updated));
          } catch {}
          return updated;
        });
        return next;
      });
    } catch (err: any) {
      const errorDetail = err.message || String(err);
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "mikasa",
        text: `**Javob olishda xatolik yuz berdi**\n\nSabab: ${errorDetail}\n\nBackend serveriga ulanishda muammo bo'lishi mumkin. Iltimos, qayta urinib ko'ring yoki backend holatini tekshiring.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => {
        const next = [...prev, errMsg];
        setSessions((prevSessions) => {
          const updated = prevSessions.map((s) =>
            s.id === activeSessionId
              ? { ...s, updatedAt: Date.now(), messages: next }
              : s
          );
          try {
            localStorage.setItem("mikasa_chat_sessions", JSON.stringify(updated));
          } catch {}
          return updated;
        });
        return next;
      });
    } finally {
      setIsLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleRegenerate = async () => {
    if (isLoading || messages.length === 0) return;
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].sender === "user") {
        await handleSendMessage(messages[i].text);
        break;
      }
    }
  };

  const handleCopyMessage = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {}
  };

  const handleClearHistory = async () => {
    setMessages([]);
    setSessions((prev) => {
      const updated = prev.map((s) =>
        s.id === activeSessionId ? { ...s, updatedAt: Date.now(), messages: [] } : s
      );
      try {
        localStorage.setItem("mikasa_chat_sessions", JSON.stringify(updated));
      } catch {}
      return updated;
    });
    await backendService.clearChat();
  };

  const handleTextareaKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 130)}px`;
    }
  };

  const handleConfirmAgent = async (planId: string, stepId: string, approve: boolean) => {
    setActiveAgent((prev) =>
      prev ? { ...prev, confirmation: null, status: approve ? "running" : "aborted" } : null
    );
    try {
      await backendService.confirmAgentStep(planId, stepId, approve);
    } catch (e) {
      console.error("Confirm agent error", e);
    }
  };

  const handleAbortAgent = async (planId: string) => {
    try {
      await backendService.abortAgentPlan(planId);
      setActiveAgent((prev) => (prev ? { ...prev, status: "aborted", confirmation: null } : null));
    } catch (e) {
      console.error("Abort agent error", e);
    }
  };

  const quickPrompts = [
    "Salom Mikasa, nimalarga qodirsan?",
    "Kompyuterim parametrlarini aytib ber",
    "Menda qanday ilovalar o'rnatilgan?",
    "Dasturlash bo'yicha maslahat ber",
  ];

  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0];

  return (
    <div
      className="chat-page-container"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        position: "relative",
        zIndex: 2,
        overflow: "hidden",
        backgroundColor: "transparent",
      }}
    >
      {/* 1. Header Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 20px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          backgroundColor: "rgba(8, 14, 28, 0.65)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          zIndex: 10,
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* Sidebar Toggle Button */}
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            title={sidebarOpen ? "Chap panelni yashirish" : "Chap panelni ko'rsatish"}
            aria-label="Chap panelni yoqish/o'chirish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
          >
            {sidebarOpen ? <CollapseSidebarIcon size={16} /> : <ExpandSidebarIcon size={16} />}
          </button>

          <button
            onClick={onNavigateHome}
            title="Bosh sahifaga qaytish"
            aria-label="Bosh sahifaga qaytish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
          >
            <HomeIcon size={16} />
          </button>

          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "15px", fontWeight: 700, color: "#FFFFFF" }}>
                AI Suhbat
              </span>
              {activeSession && (
                <span
                  style={{
                    fontSize: "11px",
                    padding: "2px 8px",
                    borderRadius: "6px",
                    backgroundColor: "rgba(56, 189, 248, 0.15)",
                    border: "1px solid rgba(56, 189, 248, 0.3)",
                    color: "#38BDF8",
                    fontWeight: 600,
                    maxWidth: "180px",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                  title={activeSession.title}
                >
                  {activeSession.title}
                </span>
              )}
              <span
                style={{
                  fontSize: "11px",
                  padding: "1px 6px",
                  borderRadius: "6px",
                  backgroundColor:
                    backendStatus.status === "online"
                      ? "rgba(16, 185, 129, 0.15)"
                      : backendStatus.status === "connecting"
                      ? "rgba(245, 158, 11, 0.15)"
                      : "rgba(239, 68, 68, 0.15)",
                  color:
                    backendStatus.status === "online"
                      ? "#10B981"
                      : backendStatus.status === "connecting"
                      ? "#F59E0B"
                      : "#EF4444",
                  fontWeight: 600,
                }}
              >
                {backendStatus.status === "online"
                  ? "Online"
                  : backendStatus.status === "connecting"
                  ? "Ulanmoqda..."
                  : "Offline"}
              </span>
            </div>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Mikasa AI bilan to'g'ridan-to'g'ri intellektual muloqot
            </span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {/* "+ Yangi suhbat" button */}
          <button
            onClick={handleNewChat}
            title="Yangi suhbat ochish"
            aria-label="Yangi suhbat ochish"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 13px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, rgba(2, 132, 199, 0.25), rgba(99, 102, 241, 0.25))",
              border: "1px solid rgba(56, 189, 248, 0.35)",
              color: "#38BDF8",
              fontSize: "12px",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "linear-gradient(135deg, rgba(2, 132, 199, 0.4), rgba(99, 102, 241, 0.4))";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "linear-gradient(135deg, rgba(2, 132, 199, 0.25), rgba(99, 102, 241, 0.25))";
              e.currentTarget.style.color = "#38BDF8";
            }}
          >
            <PlusIcon size={14} />
            <span>Yangi suhbat</span>
          </button>

          {messages.length > 0 && (
            <button
              onClick={handleRegenerate}
              disabled={isLoading}
              title="Oxirgi javobni qayta olish"
              aria-label="Oxirgi javobni qayta olish"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "8px",
                backgroundColor: "rgba(255, 255, 255, 0.04)",
                border: "1px solid var(--border)",
                color: "var(--text-secondary)",
                fontSize: "12px",
                cursor: isLoading ? "default" : "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)";
                  e.currentTarget.style.color = "#FFFFFF";
                }
              }}
              onMouseLeave={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
                  e.currentTarget.style.color = "var(--text-secondary)";
                }
              }}
            >
              <RefreshIcon size={13} />
              <span>Qayta olish</span>
            </button>
          )}

          <button
            onClick={handleClearHistory}
            title="Suhbat tarixini tozalash"
            aria-label="Suhbat tarixini tozalash"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 12px",
              borderRadius: "8px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid var(--border)",
              color: "var(--text-muted)",
              fontSize: "12px",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
              e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
              e.currentTarget.style.color = "#EF4444";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)";
              e.currentTarget.style.borderColor = "var(--border)";
              e.currentTarget.style.color = "var(--text-muted)";
            }}
          >
            <TrashIcon size={13} />
            <span>Tozalash</span>
          </button>
        </div>
      </div>

      {/* 2. Main Content Split: Sidebar + Chat Column */}
      <div
        style={{
          display: "flex",
          flex: 1,
          height: "calc(100% - 57px)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* ── Collapsible Left Glass Sidebar ── */}
        {sidebarOpen && (
          <aside
            style={{
              width: "270px",
              minWidth: "270px",
              maxWidth: "270px",
              height: "100%",
              backgroundColor: "rgba(8, 14, 28, 0.75)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              borderRight: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              flexDirection: "column",
              padding: "14px 12px",
              gap: "12px",
              overflow: "hidden",
              zIndex: 8,
              flexShrink: 0,
            }}
          >
            {/* Top: "+ Yangi suhbat" button */}
            <button
              onClick={handleNewChat}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                width: "100%",
                padding: "10px 14px",
                borderRadius: "12px",
                background: "linear-gradient(135deg, rgba(2, 132, 199, 0.35), rgba(99, 102, 241, 0.35))",
                border: "1px solid rgba(56, 189, 248, 0.4)",
                boxShadow: "0 4px 16px rgba(2, 132, 199, 0.2)",
                color: "#FFFFFF",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-1px)";
                e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.7)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.4)";
              }}
            >
              <PlusIcon size={16} />
              <span>+ Yangi suhbat</span>
            </button>

            {/* Sub-Navigation Tabs: "Suhbatlar" vs "Barcha suratlar" */}
            <div
              style={{
                display: "flex",
                gap: "4px",
                padding: "3px",
                borderRadius: "10px",
                backgroundColor: "rgba(255, 255, 255, 0.04)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
              }}
            >
              <button
                onClick={() => setSidebarTab("chats")}
                style={{
                  flex: 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px",
                  padding: "6px 8px",
                  borderRadius: "8px",
                  backgroundColor: sidebarTab === "chats" ? "rgba(56, 189, 248, 0.18)" : "transparent",
                  border: sidebarTab === "chats" ? "1px solid rgba(56, 189, 248, 0.35)" : "1px solid transparent",
                  color: sidebarTab === "chats" ? "#38BDF8" : "#94A3B8",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                <ChatIcon size={13} />
                <span>Suhbatlar</span>
                <span style={{ fontSize: "10px", opacity: 0.75 }}>({sessions.length})</span>
              </button>

              <button
                onClick={() => setSidebarTab("images")}
                style={{
                  flex: 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px",
                  padding: "6px 8px",
                  borderRadius: "8px",
                  backgroundColor: sidebarTab === "images" ? "rgba(236, 72, 153, 0.18)" : "transparent",
                  border: sidebarTab === "images" ? "1px solid rgba(236, 72, 153, 0.35)" : "1px solid transparent",
                  color: sidebarTab === "images" ? "#F472B6" : "#94A3B8",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                <ImageIcon size={13} />
                <span>Suratlar</span>
                <span style={{ fontSize: "10px", opacity: 0.75 }}>({allGalleryImages.length})</span>
              </button>
            </div>

            {/* Tab Body */}
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "6px",
                paddingRight: "2px",
              }}
            >
              {sidebarTab === "chats" ? (
                sessions.length === 0 ? (
                  <div style={{ textAlign: "center", padding: "30px 10px", color: "#64748B", fontSize: "12px" }}>
                    Suhbatlar arxivi bo'sh
                  </div>
                ) : (
                  sessions.map((sess) => {
                    const isActive = sess.id === activeSessionId;
                    return (
                      <div
                        key={sess.id}
                        onClick={() => handleSelectSession(sess.id)}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "9px 12px",
                          borderRadius: "10px",
                          backgroundColor: isActive ? "rgba(56, 189, 248, 0.12)" : "rgba(255, 255, 255, 0.02)",
                          border: isActive ? "1px solid rgba(56, 189, 248, 0.3)" : "1px solid rgba(255, 255, 255, 0.04)",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                          gap: "8px",
                        }}
                        onMouseEnter={(e) => {
                          if (!isActive) e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)";
                        }}
                        onMouseLeave={(e) => {
                          if (!isActive) e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.02)";
                        }}
                      >
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px", minWidth: 0, flex: 1 }}>
                          <span
                            style={{
                              fontSize: "12.5px",
                              fontWeight: isActive ? 600 : 500,
                              color: isActive ? "#FFFFFF" : "#CBD5E1",
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {sess.title || "Yangi suhbat"}
                          </span>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ fontSize: "10.5px", color: "#64748B" }}>
                              {new Date(sess.updatedAt || sess.createdAt).toLocaleDateString("uz-UZ", {
                                month: "short",
                                day: "numeric",
                              })}
                            </span>
                            <span style={{ fontSize: "10px", color: "#475569" }}>•</span>
                            <span style={{ fontSize: "10.5px", color: "#64748B" }}>
                              {sess.messages?.length || 0} xabar
                            </span>
                          </div>
                        </div>

                        <button
                          onClick={(e) => handleDeleteSession(sess.id, e)}
                          title="Suhbatni o'chirish"
                          style={{
                            background: "transparent",
                            border: "none",
                            color: "#64748B",
                            cursor: "pointer",
                            padding: "4px",
                            borderRadius: "6px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            opacity: isActive ? 0.8 : 0.4,
                            transition: "all 0.15s ease",
                            flexShrink: 0,
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.color = "#EF4444";
                            e.currentTarget.style.backgroundColor = "rgba(239, 68, 68, 0.1)";
                            e.currentTarget.style.opacity = "1";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.color = "#64748B";
                            e.currentTarget.style.backgroundColor = "transparent";
                            e.currentTarget.style.opacity = isActive ? "0.8" : "0.4";
                          }}
                        >
                          <TrashIcon size={12} />
                        </button>
                      </div>
                    );
                  })
                )
              ) : (
                /* Barcha suratlar Gallery */
                allGalleryImages.length === 0 ? (
                  <div
                    style={{
                      textAlign: "center",
                      padding: "40px 14px",
                      color: "#94A3B8",
                      fontSize: "12px",
                      lineHeight: 1.6,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <div
                      style={{
                        width: "44px",
                        height: "44px",
                        borderRadius: "12px",
                        backgroundColor: "rgba(236, 72, 153, 0.1)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#F472B6",
                      }}
                    >
                      <ImageIcon size={22} />
                    </div>
                    <span>Hozircha suratlar yo'q.</span>
                    <span style={{ fontSize: "11px", color: "#64748B" }}>
                      Mikasaga "Toshkent shahri surati" yoki rasm chizish haqida buyruq bering.
                    </span>
                    <button
                      onClick={() => handleSendMessage("Menga zamonaviy Toshkent shahri haqida chiroyli tasvir tavsifini yozib ber")}
                      style={{
                        marginTop: "6px",
                        padding: "6px 12px",
                        borderRadius: "8px",
                        backgroundColor: "rgba(236, 72, 153, 0.15)",
                        border: "1px solid rgba(236, 72, 153, 0.3)",
                        color: "#F472B6",
                        fontSize: "11px",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Rasm so'rash
                    </button>
                  </div>
                ) : (
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(2, 1fr)",
                      gap: "8px",
                    }}
                  >
                    {allGalleryImages.map((img) => (
                      <div
                        key={img.id}
                        onClick={() => setPreviewImage(img)}
                        title={img.prompt}
                        style={{
                          position: "relative",
                          aspectRatio: "1/1",
                          borderRadius: "8px",
                          overflow: "hidden",
                          border: "1px solid rgba(255, 255, 255, 0.1)",
                          cursor: "pointer",
                          backgroundColor: "rgba(0, 0, 0, 0.4)",
                          transition: "transform 0.15s ease, border-color 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = "scale(1.03)";
                          e.currentTarget.style.borderColor = "rgba(236, 72, 153, 0.6)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = "scale(1)";
                          e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.1)";
                        }}
                      >
                        <img
                          src={img.url}
                          alt={img.prompt || "Surat"}
                          style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                            display: "block",
                          }}
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                      </div>
                    ))}
                  </div>
                )
              )}
            </div>
          </aside>
        )}

        {/* ── Main Chat Column ── */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            height: "100%",
            overflow: "hidden",
            minWidth: 0,
          }}
        >
          {/* 2. Messages Scroll Area */}
          <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px clamp(16px, 3vw, 32px)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          className="chat-readable-container"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "20px",
            width: "100%",
            flex: 1,
          }}
        >
          {messages.length === 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                margin: "auto 0",
                textAlign: "center",
                gap: "16px",
                maxWidth: "520px",
                alignSelf: "center",
                width: "100%",
              }}
            >
              <div style={{ marginBottom: "6px" }}>
                <MikasaOrb size="100px" state={isLoading ? "thinking" : "idle"} />
              </div>

              <h2
                className="text-metallic-gradient"
                style={{ fontSize: "24px", fontWeight: 700, margin: 0 }}
              >
                Mikasa AI Suhbatiga xush kelibsiz!
              </h2>

              <p style={{ fontSize: "13.5px", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>
                Salom, <strong>{userDisplayName}</strong>! Istalgan savolingizni bering, dasturlash va apparat holatini so'rang yoki kompyuteringiz boshqaruviga oid buyruqlarni yuboring.
              </p>

              {/* Quick Prompts */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: "8px",
                  width: "100%",
                  marginTop: "8px",
                }}
              >
              {quickPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(p)}
                  style={{
                    padding: "11px 14px",
                    borderRadius: "12px",
                    backgroundColor: "var(--surface)",
                    border: "1px solid var(--border)",
                    color: "var(--text-secondary)",
                    fontSize: "12px",
                    textAlign: "left",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--surface-elevated)";
                    e.currentTarget.style.borderColor = "var(--primary-glow)";
                    e.currentTarget.style.color = "#FFFFFF";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--surface)";
                    e.currentTarget.style.borderColor = "var(--border)";
                    e.currentTarget.style.color = "var(--text-secondary)";
                  }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.sender === "user";
            const isCopied = copiedId === msg.id;

            return (
              <div
                key={msg.id}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: isUser ? "flex-end" : "flex-start",
                  width: "100%",
                  position: "relative",
                }}
              >
                {/* Sender Title and Time Header */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    marginBottom: "4px",
                    padding: isUser ? "0 4px 0 0" : "0 0 0 4px",
                  }}
                >
                  <span style={{ fontSize: "12px", fontWeight: 600, color: isUser ? "var(--primary-glow)" : "#FFFFFF" }}>
                    {isUser ? userDisplayName : "Mikasa AI"}
                  </span>
                  <span style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>
                    {msg.timestamp}
                  </span>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "10px",
                    maxWidth: "84%",
                    flexDirection: isUser ? "row-reverse" : "row",
                  }}
                >
                  {/* Avatar Icon */}
                  <div
                    style={{
                      width: "30px",
                      height: "30px",
                      borderRadius: "50%",
                      backgroundColor: isUser
                        ? "rgba(2, 132, 199, 0.2)"
                        : "rgba(14, 165, 233, 0.25)",
                      border: isUser
                        ? "1px solid rgba(56, 189, 248, 0.4)"
                        : "1px solid rgba(56, 189, 248, 0.6)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "11px",
                      fontWeight: 700,
                      color: "#FFFFFF",
                      flexShrink: 0,
                      boxShadow: isUser ? "none" : "0 0 12px rgba(2, 132, 199, 0.25)",
                    }}
                  >
                    {isUser ? userInitials : <SparklesIcon size={14} color="#38BDF8" />}
                  </div>

                  {/* Message Bubble Container */}
                  <div
                    style={{
                      position: "relative",
                      padding: "12px 18px",
                      borderRadius: isUser
                        ? "18px 4px 18px 18px"
                        : "4px 18px 18px 18px",
                      backgroundColor: isUser
                        ? "rgba(2, 132, 199, 0.72)"
                        : "rgba(10, 18, 36, 0.72)",
                      backdropFilter: "blur(20px)",
                      WebkitBackdropFilter: "blur(20px)",
                      border: isUser
                        ? "1px solid rgba(56, 189, 248, 0.4)"
                        : "1px solid rgba(255, 255, 255, 0.1)",
                      color: "#FFFFFF",
                      fontSize: "14px",
                      lineHeight: 1.6,
                      boxShadow: isUser
                        ? "0 4px 20px rgba(2, 132, 199, 0.25)"
                        : "0 8px 24px rgba(0, 0, 0, 0.4)",
                    }}
                  >
                    {isUser ? (
                      <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{msg.text}</div>
                    ) : (
                      <MarkdownView content={msg.text} />
                    )}

                    {/* Copy action button at bottom right of bubble */}
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "flex-end",
                        marginTop: "6px",
                      }}
                    >
                      <button
                        onClick={() => handleCopyMessage(msg.id, msg.text)}
                        title="Xabarni nusxalash"
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                          background: "transparent",
                          border: "none",
                          color: isCopied ? "#10B981" : "rgba(255, 255, 255, 0.4)",
                          cursor: "pointer",
                          fontSize: "11px",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          transition: "all 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          if (!isCopied) e.currentTarget.style.color = "#FFFFFF";
                        }}
                        onMouseLeave={(e) => {
                          if (!isCopied) e.currentTarget.style.color = "rgba(255, 255, 255, 0.4)";
                        }}
                      >
                        {isCopied ? <CheckIcon size={12} color="#10B981" /> : <CopyIcon size={12} color="currentColor" />}
                        <span>{isCopied ? "Nusxalandi" : "Nusxa"}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}

        {/* Thinking Indicator */}
        {isLoading && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              alignSelf: "flex-start",
            }}
          >
            <div
              style={{
                width: "30px",
                height: "30px",
                borderRadius: "50%",
                backgroundColor: "rgba(14, 165, 233, 0.25)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 12px rgba(56, 189, 248, 0.35)",
              }}
            >
              <SparklesIcon size={15} color="#38BDF8" />
            </div>
            <div
              style={{
                padding: "10px 16px",
                borderRadius: "4px 18px 18px 18px",
                backgroundColor: "var(--surface)",
                border: "1px solid rgba(56, 189, 248, 0.3)",
                color: "var(--primary-glow)",
                fontSize: "13px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <div
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: "var(--primary-glow)",
                  animation: "pulse 1s infinite",
                }}
              />
              <span>Mikasa o‘ylamoqda...</span>
            </div>
          </div>
        )}

        </div>

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Composer Section (Multiline, Enter to Send, Shift+Enter for Newline) */}
      <div
        style={{
          padding: "12px clamp(16px, 3vw, 24px) 16px clamp(16px, 3vw, 24px)",
          borderTop: "1px solid var(--border)",
          backgroundColor: "var(--surface)",
        }}
      >
        <div className="chat-readable-container" style={{ width: "100%" }}>
          {/* Agentic Multi-Step Progress & Confirmation Card */}
          {activeAgent && (
            <div
              style={{
                marginBottom: "12px",
                padding: "12px 16px",
                borderRadius: "14px",
                backgroundColor: "var(--surface-elevated)",
                border: activeAgent.confirmation
                  ? "1px solid rgba(245, 158, 11, 0.6)"
                  : activeAgent.status === "completed"
                  ? "1px solid rgba(16, 185, 129, 0.5)"
                  : "1px solid rgba(56, 189, 248, 0.4)",
                boxShadow: "0 6px 20px rgba(0, 0, 0, 0.35)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "8px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "15px" }}>⚡</span>
                  <span style={{ fontSize: "13px", fontWeight: 600, color: "#FFFFFF" }}>
                    Agentlik Rejasi: {activeAgent.goal}
                  </span>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 600,
                      padding: "1px 6px",
                      borderRadius: "4px",
                      backgroundColor:
                        activeAgent.planVersion && activeAgent.planVersion > 1
                          ? "rgba(168, 85, 247, 0.2)"
                          : "rgba(255, 255, 255, 0.1)",
                      color:
                        activeAgent.planVersion && activeAgent.planVersion > 1
                          ? "#C084FC"
                          : "var(--text-secondary)",
                      border:
                        activeAgent.planVersion && activeAgent.planVersion > 1
                          ? "1px solid rgba(168, 85, 247, 0.4)"
                          : "1px solid rgba(255, 255, 255, 0.15)",
                    }}
                  >
                    v{activeAgent.planVersion || 1}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span
                    style={{
                      fontSize: "11px",
                      padding: "2px 8px",
                      borderRadius: "6px",
                      backgroundColor:
                        activeAgent.status === "completed"
                          ? "rgba(16, 185, 129, 0.2)"
                          : activeAgent.status === "paused"
                          ? "rgba(245, 158, 11, 0.2)"
                          : activeAgent.status === "aborted"
                          ? "rgba(239, 68, 68, 0.2)"
                          : "rgba(56, 189, 248, 0.2)",
                      color:
                        activeAgent.status === "completed"
                          ? "#10B981"
                          : activeAgent.status === "paused"
                          ? "#F59E0B"
                          : activeAgent.status === "aborted"
                          ? "#EF4444"
                          : "#38BDF8",
                    }}
                  >
                    {activeAgent.status === "completed"
                      ? "Muvaffaqiyatli"
                      : activeAgent.status === "paused"
                      ? "Tasdiqlash kutilmoqda"
                      : activeAgent.status === "aborted"
                      ? "To'xtatildi"
                      : "Bajarilmoqda..."}
                  </span>
                  {activeAgent.status === "running" && (
                    <button
                      type="button"
                      onClick={() => handleAbortAgent(activeAgent.planId)}
                      style={{
                        padding: "3px 8px",
                        borderRadius: "6px",
                        backgroundColor: "rgba(239, 68, 68, 0.2)",
                        border: "1px solid rgba(239, 68, 68, 0.4)",
                        color: "#EF4444",
                        fontSize: "11px",
                        cursor: "pointer",
                      }}
                    >
                      ⏹️ To'xtatish
                    </button>
                  )}
                  {(activeAgent.status === "completed" ||
                    activeAgent.status === "aborted" ||
                    activeAgent.status === "failed") && (
                    <button
                      type="button"
                      onClick={() => setActiveAgent(null)}
                      style={{
                        padding: "2px 6px",
                        borderRadius: "6px",
                        backgroundColor: "transparent",
                        border: "none",
                        color: "var(--text-muted)",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>

              {/* Replanning Banner */}
              {activeAgent.replanReason && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "6px 10px",
                    marginBottom: "8px",
                    borderRadius: "8px",
                    backgroundColor: "rgba(168, 85, 247, 0.12)",
                    border: "1px solid rgba(168, 85, 247, 0.3)",
                    fontSize: "11.5px",
                    color: "#E9D5FF",
                  }}
                >
                  <span>🔄</span>
                  <span>
                    <strong>Qayta rejalashtirildi (v{activeAgent.planVersion}):</strong> {activeAgent.replanReason}
                  </span>
                </div>
              )}

              {/* Steps Checklist */}
              {activeAgent.steps.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "4px", margin: "8px 0" }}>
                  {activeAgent.steps.map((s, idx) => (
                    <div
                      key={s.step_id || idx}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        fontSize: "12px",
                        padding: "4px 8px",
                        borderRadius: "6px",
                        backgroundColor: "rgba(255, 255, 255, 0.03)",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span>
                          {s.status === "completed"
                            ? "✅"
                            : s.status === "running"
                            ? "⏳"
                            : s.status === "failed"
                            ? "❌"
                            : s.status === "blocked"
                            ? "🚫"
                            : "⚪"}
                        </span>
                        <span style={{ color: s.status === "running" ? "#38BDF8" : "var(--text-secondary)" }}>
                          {idx + 1}. {s.tool}
                        </span>
                        {s.capability && (
                          <span
                            style={{
                              fontSize: "10px",
                              padding: "1px 5px",
                              borderRadius: "4px",
                              backgroundColor: "rgba(56, 189, 248, 0.1)",
                              color: "#38BDF8",
                            }}
                          >
                            {s.capability}
                          </span>
                        )}
                        {s.dependencies && s.dependencies.length > 0 && (
                          <span
                            style={{
                              fontSize: "10px",
                              padding: "1px 5px",
                              borderRadius: "4px",
                              backgroundColor: "rgba(255, 255, 255, 0.05)",
                              color: "var(--text-muted)",
                            }}
                          >
                            dep: {s.dependencies.join(", ")}
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                        {s.reason || s.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* High-Risk Confirmation Box */}
              {activeAgent.confirmation && (
                <div
                  style={{
                    marginTop: "10px",
                    padding: "10px 12px",
                    borderRadius: "10px",
                    backgroundColor: "rgba(245, 158, 11, 0.12)",
                    border: "1px solid rgba(245, 158, 11, 0.4)",
                  }}
                >
                  <div
                    style={{
                      fontSize: "12.5px",
                      fontWeight: 600,
                      color: "#F59E0B",
                      marginBottom: "4px",
                    }}
                  >
                    ⚠️ Xavfli amal tasdiqlashni talab etadi:
                  </div>
                  <div style={{ fontSize: "12px", color: "#FFFFFF", marginBottom: "8px" }}>
                    {activeAgent.confirmation.prompt}
                  </div>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfirmAgent(activeAgent.planId, activeAgent.confirmation!.stepId, true)
                      }
                      style={{
                        padding: "6px 14px",
                        borderRadius: "8px",
                        backgroundColor: "rgba(16, 185, 129, 0.25)",
                        border: "1px solid #10B981",
                        color: "#10B981",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      ✅ Tasdiqlash va davom etish
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        handleConfirmAgent(activeAgent.planId, activeAgent.confirmation!.stepId, false)
                      }
                      style={{
                        padding: "6px 14px",
                        borderRadius: "8px",
                        backgroundColor: "rgba(239, 68, 68, 0.2)",
                        border: "1px solid #EF4444",
                        color: "#EF4444",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      ❌ Bekor qilish
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
          style={{
            display: "flex",
            alignItems: "flex-end",
            width: "100%",
            minHeight: "48px",
            borderRadius: "16px",
            backgroundColor: "rgba(10, 18, 36, 0.75)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(56, 189, 248, 0.25)",
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.08)",
            padding: "6px 8px 6px 14px",
            gap: "8px",
            transition: "all 0.15s ease",
          }}
          onFocusCapture={(e) => {
            e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.55)";
            e.currentTarget.style.boxShadow = "0 8px 36px rgba(0, 0, 0, 0.55), 0 0 18px rgba(2, 132, 199, 0.25)";
          }}
          onBlurCapture={(e) => {
            e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.25)";
            e.currentTarget.style.boxShadow = "0 8px 32px rgba(0, 0, 0, 0.45)";
          }}
        >
          {/* Attachment Button */}
          <button
            type="button"
            title="Fayl biriktirish"
            aria-label="Fayl biriktirish"
            style={{
              background: "transparent",
              border: "none",
              color: "rgba(255, 255, 255, 0.5)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "8px",
              borderRadius: "8px",
              transition: "all 0.15s ease",
              flexShrink: 0,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
              e.currentTarget.style.color = "rgba(255, 255, 255, 0.5)";
            }}
          >
            <AttachIcon size={17} />
          </button>

          {/* Multiline auto-expanding textarea */}
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={handleTextareaKeyDown}
            placeholder="Mikasa bilan suhbatlashing... (Enter yuborish, Shift+Enter yangi qator)"
            disabled={isLoading}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#FFFFFF",
              fontSize: "14px",
              fontFamily: "inherit",
              resize: "none",
              maxHeight: "130px",
              lineHeight: 1.5,
              padding: "6px 0",
              overflowY: "auto",
            }}
          />

          {/* Glowing Circular Send Button */}
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            title="Yuborish"
            aria-label="Yuborish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "34px",
              height: "34px",
              borderRadius: "50%",
              backgroundColor: input.trim() && !isLoading ? "#0284C7" : "rgba(255, 255, 255, 0.08)",
              color: "#FFFFFF",
              border: input.trim() && !isLoading ? "1px solid rgba(56, 189, 248, 0.5)" : "none",
              boxShadow: input.trim() && !isLoading ? "0 0 14px rgba(56, 189, 248, 0.45)" : "none",
              cursor: input.trim() && !isLoading ? "pointer" : "default",
              transition: "all 0.15s ease",
              flexShrink: 0,
            }}
            onMouseEnter={(e) => {
              if (input.trim() && !isLoading) {
                e.currentTarget.style.backgroundColor = "#0369A1";
                e.currentTarget.style.transform = "scale(1.05)";
              }
            }}
            onMouseLeave={(e) => {
              if (input.trim() && !isLoading) {
                e.currentTarget.style.backgroundColor = "#0284C7";
                e.currentTarget.style.transform = "scale(1)";
              }
            }}
          >
            <ArrowUpIcon size={15} />
          </button>
        </form>
        </div>
      </div>
    </div>
  </div>

  {/* 3. Image Lightbox Preview Modal */}
  {previewImage && (
    <div
      onClick={() => setPreviewImage(null)}
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.85)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: "92vw",
          maxHeight: "90vh",
          backgroundColor: "rgba(10, 16, 32, 0.95)",
          borderRadius: "18px",
          border: "1px solid rgba(255, 255, 255, 0.15)",
          boxShadow: "0 25px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(56, 189, 248, 0.15)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "14px 20px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <span style={{ fontSize: "13.5px", fontWeight: 700, color: "#FFFFFF" }}>
            {previewImage.prompt || "Tasvir"}
          </span>
          <button
            onClick={() => setPreviewImage(null)}
            style={{
              background: "transparent",
              border: "none",
              color: "#94A3B8",
              cursor: "pointer",
              fontSize: "18px",
              lineHeight: 1,
              padding: "4px 8px",
              borderRadius: "6px",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#FFFFFF")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#94A3B8")}
          >
            ✕
          </button>
        </div>
        <div
          style={{
            padding: "16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            maxHeight: "68vh",
            overflow: "hidden",
          }}
        >
          <img
            src={previewImage.url}
            alt={previewImage.prompt}
            style={{
              maxWidth: "100%",
              maxHeight: "65vh",
              objectFit: "contain",
              borderRadius: "10px",
              boxShadow: "0 10px 30px rgba(0, 0, 0, 0.5)",
            }}
          />
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 20px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            gap: "12px",
          }}
        >
          <span style={{ fontSize: "11px", color: "#64748B" }}>
            {previewImage.timestamp}
          </span>
          <a
            href={previewImage.url}
            target="_blank"
            rel="noopener noreferrer"
            download="mikasa-image.png"
            style={{
              padding: "7px 16px",
              borderRadius: "8px",
              backgroundColor: "rgba(56, 189, 248, 0.2)",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              color: "#38BDF8",
              fontSize: "12px",
              fontWeight: 600,
              textDecoration: "none",
              transition: "all 0.15s ease",
            }}
          >
            Yuklab olish
          </a>
        </div>
      </div>
    </div>
  )}
</div>
  );
};
