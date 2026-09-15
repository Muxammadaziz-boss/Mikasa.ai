// ========== ChatPage.tsx ==========
// Mikasa AI 7.x — Production AI Messaging Interface [Phase 9]
// Inspired by Quiet Intelligence, modern messaging layouts, and desktop speed

import React, { useState, useEffect, useRef } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import { MarkdownView } from "../components/MarkdownView";
import {
  SparklesIcon,
  MicIcon,
  ArrowUpIcon,
  TrashIcon,
  HomeIcon,
  AttachIcon,
  CopyIcon,
  CheckIcon,
  RefreshIcon,
} from "../components/icons/Icons";
import { backendService, BackendStatus } from "../services/backendService";

interface Message {
  id: string;
  sender: "user" | "mikasa";
  text: string;
  timestamp: string;
}

interface ChatPageProps {
  initialPrompt?: string;
  userName?: string;
  onNavigateHome: () => void;
  onNavigateVoice: () => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({
  initialPrompt,
  userName = "Ustoz",
  onNavigateHome,
  onNavigateVoice,
}) => {
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

  // Initial load: fetch existing memory conversation history
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const mem = await backendService.getMemory();
        if (mem.ok && mem.conversations && mem.conversations.length > 0) {
          const loaded: Message[] = [];
          mem.conversations.forEach((c, idx) => {
            if (c.user) {
              loaded.push({
                id: `hist-u-${idx}`,
                sender: "user",
                text: c.user,
                timestamp: c.time || "",
              });
            }
            if (c.agent) {
              loaded.push({
                id: `hist-a-${idx}`,
                sender: "mikasa",
                text: c.agent,
                timestamp: c.time || "",
              });
            }
          });
          setMessages((prev) => (prev.length === 0 ? loaded : prev));
        }
      } catch {}
    };
    loadHistory();
  }, []);

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

    setMessages((prev) => [...prev, userMsg]);
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
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorDetail = err.message || String(err);
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "mikasa",
        text: `**Javob olishda xatolik yuz berdi**\n\nSabab: ${errorDetail}\n\nBackend serveriga ulanishda muammo bo'lishi mumkin. Iltimos, qayta urinib ko'ring yoki backend holatini tekshiring.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleRegenerate = async () => {
    if (isLoading || messages.length === 0) return;
    // Find last user query
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
        backgroundColor: "var(--bg-darkest)",
      }}
    >
      {/* 1. Header Toolbar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 24px",
          borderBottom: "1px solid var(--border)",
          backgroundColor: "var(--surface)",
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
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
                        ? "rgba(2, 132, 199, 0.28)"
                        : "var(--surface)",
                      border: isUser
                        ? "1px solid rgba(56, 189, 248, 0.35)"
                        : "1px solid var(--border)",
                      color: "#FFFFFF",
                      fontSize: "14px",
                      lineHeight: 1.6,
                      boxShadow: isUser
                        ? "0 4px 20px rgba(2, 132, 199, 0.15)"
                        : "0 4px 20px rgba(0, 0, 0, 0.3)",
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
            backgroundColor: "var(--bg-darkest)",
            border: "1px solid rgba(56, 189, 248, 0.22)",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.05)",
            padding: "6px 8px 6px 14px",
            gap: "8px",
            transition: "all 0.15s ease",
          }}
          onFocusCapture={(e) => {
            e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.55)";
            e.currentTarget.style.boxShadow = "0 6px 28px rgba(0, 0, 0, 0.5), 0 0 18px rgba(2, 132, 199, 0.25)";
          }}
          onBlurCapture={(e) => {
            e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.22)";
            e.currentTarget.style.boxShadow = "0 4px 20px rgba(0, 0, 0, 0.4)";
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

          {/* Voice Page Jump Button */}
          <button
            type="button"
            onClick={onNavigateVoice}
            title="Ovozli muloqot rejimiga o‘tish"
            aria-label="Ovozli muloqot rejimiga o‘tish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "34px",
              height: "34px",
              borderRadius: "8px",
              color: "rgba(255, 255, 255, 0.65)",
              background: "transparent",
              border: "none",
              cursor: "pointer",
              transition: "all 0.15s ease",
              flexShrink: 0,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.color = "var(--primary-glow)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
              e.currentTarget.style.color = "rgba(255, 255, 255, 0.65)";
            }}
          >
            <MicIcon size={17} />
          </button>

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
  );
};
