// ========== ChatPage.tsx ==========
// Mikasa AI 7.0 — To'liq Funksional AI Suhbat Sahifasi
// Python Backend (core.ai_engine, main.py) bilan real vaqtda ishlaydi

import React, { useState, useEffect, useRef } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import {
  SparklesIcon,
  MicIcon,
  ArrowUpIcon,
  TrashIcon,
  HomeIcon,
  AttachIcon,
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
  userName = "Muxammadaziz",
  onNavigateHome,
  onNavigateVoice,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({ status: "connecting" });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const initialSentRef = useRef(false);

  // Status kuzatish
  useEffect(() => {
    const unsub = backendService.onStatusChange((s) => setBackendStatus(s));
    return () => unsub();
  }, []);

  // Avtomatik pastga skroll
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Agar Bosh sahifadan so'rov bilan o'tilgan bo'lsa, uni avtomatik jo'natish
  useEffect(() => {
    if (initialPrompt && !initialSentRef.current) {
      initialSentRef.current = true;
      handleSendMessage(initialPrompt);
    }
  }, [initialPrompt]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await backendService.sendChat(query, "ask");
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "mikasa",
        text: res.ok ? res.response : res.error || "Kechirasiz, javob olishda xatolik yuz berdi.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "mikasa",
        text: "Aloqa xatosi: " + (err.message || String(err)),
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleClearHistory = async () => {
    setMessages([]);
    await backendService.clearChat();
  };

  const quickPrompts = [
    "Salom Mikasa, nimalarga qodirsan?",
    "Kompyuterim parametrlarini aytib ber",
    "Bugungi sana va vaqt qanday?",
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
      }}
    >
      {/* 1. Yuqori sarlavha paneli (Header) */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 24px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
          backgroundColor: "rgba(8, 12, 20, 0.65)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button
            onClick={onNavigateHome}
            title="Bosh sahifaga qaytish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "32px",
              height: "32px",
              borderRadius: "10px",
              backgroundColor: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "var(--text-secondary)",
              cursor: "pointer",
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
                      : "rgba(239, 68, 68, 0.15)",
                  color:
                    backendStatus.status === "online" ? "#10B981" : "#EF4444",
                  fontWeight: 600,
                }}
              >
                {backendStatus.status === "online"
                  ? `Online (v${backendStatus.version || "7.1.0"})`
                  : "Offline"}
              </span>
            </div>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Mikasa AI intellektual yordamchisi bilan to'g'ridan-to'g'ri muloqot
            </span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <button
            onClick={handleClearHistory}
            title="Suhbatni tozalash"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "6px 12px",
              borderRadius: "8px",
              backgroundColor: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "var(--text-muted)",
              fontSize: "12px",
              cursor: "pointer",
            }}
          >
            <TrashIcon size={14} />
            <span>Tozalash</span>
          </button>
        </div>
      </div>

      {/* 2. Xabarlar maydoni (Messages Scroll Area) */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "24px 32px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
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
            }}
          >
            <div style={{ marginBottom: "8px" }}>
              <MikasaOrb size={110} state={isLoading ? "thinking" : "idle"} />
            </div>

            <h2
              className="text-metallic-gradient"
              style={{ fontSize: "24px", fontWeight: 700, margin: 0 }}
            >
              Mikasa AI Suhbatiga xush kelibsiz!
            </h2>

            <p style={{ fontSize: "13.5px", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>
              Salom, <strong>{backendStatus.user || userName}</strong>! Istalgan savolingizni bering, matnlarni tahlil qiling yoki kompyuteringiz boshqaruviga oid buyruqlarni yuboring.
            </p>

            {/* Quick Prompts */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "8px",
                width: "100%",
                marginTop: "12px",
              }}
            >
              {quickPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(p)}
                  style={{
                    padding: "10px 14px",
                    borderRadius: "12px",
                    backgroundColor: "rgba(12, 18, 30, 0.6)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    color: "var(--text-secondary)",
                    fontSize: "12px",
                    textAlign: "left",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "rgba(20, 28, 45, 0.75)";
                    e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.35)";
                    e.currentTarget.style.color = "#FFFFFF";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "rgba(12, 18, 30, 0.6)";
                    e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
                    e.currentTarget.style.color = "var(--text-secondary)";
                  }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: msg.sender === "user" ? "flex-end" : "flex-start",
                width: "100%",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "10px",
                  maxWidth: "80%",
                  flexDirection: msg.sender === "user" ? "row-reverse" : "row",
                }}
              >
                {/* Avatar / Icon */}
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "50%",
                    backgroundColor:
                      msg.sender === "user"
                        ? "rgba(2, 132, 199, 0.2)"
                        : "rgba(14, 165, 233, 0.25)",
                    border:
                      msg.sender === "user"
                        ? "1px solid rgba(56, 189, 248, 0.4)"
                        : "1px solid rgba(56, 189, 248, 0.6)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "11px",
                    fontWeight: 700,
                    color: "#FFFFFF",
                    flexShrink: 0,
                  }}
                >
                  {msg.sender === "user" ? "MA" : <SparklesIcon size={14} color="#38BDF8" />}
                </div>

                {/* Message Bubble */}
                <div
                  style={{
                    padding: "12px 16px",
                    borderRadius:
                      msg.sender === "user"
                        ? "18px 4px 18px 18px"
                        : "4px 18px 18px 18px",
                    backgroundColor:
                      msg.sender === "user"
                        ? "rgba(2, 132, 199, 0.25)"
                        : "rgba(14, 20, 32, 0.78)",
                    border:
                      msg.sender === "user"
                        ? "1px solid rgba(56, 189, 248, 0.35)"
                        : "1px solid rgba(255, 255, 255, 0.08)",
                    backdropFilter: "blur(20px)",
                    WebkitBackdropFilter: "blur(20px)",
                    color: "#FFFFFF",
                    fontSize: "14px",
                    lineHeight: 1.55,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {msg.text}
                </div>
              </div>

              {/* Timestamp */}
              <span
                style={{
                  fontSize: "10.5px",
                  color: "var(--text-muted)",
                  marginTop: "4px",
                  marginRight: msg.sender === "user" ? "38px" : 0,
                  marginLeft: msg.sender === "mikasa" ? "38px" : 0,
                }}
              >
                {msg.timestamp}
              </span>
            </div>
          ))
        )}

        {/* Typing indicator */}
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
                width: "28px",
                height: "28px",
                borderRadius: "50%",
                backgroundColor: "rgba(14, 165, 233, 0.25)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <SparklesIcon size={14} color="#38BDF8" />
            </div>
            <div
              style={{
                padding: "10px 16px",
                borderRadius: "4px 18px 18px 18px",
                backgroundColor: "rgba(14, 20, 32, 0.78)",
                border: "1px solid rgba(56, 189, 248, 0.3)",
                color: "var(--primary-glow)",
                fontSize: "13px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>Mikasa o‘ylamoqda...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Pastki Kompozer paneli (Composer Bar) */}
      <div
        style={{
          padding: "16px 24px 20px 24px",
          borderTop: "1px solid rgba(255, 255, 255, 0.06)",
          backgroundColor: "rgba(8, 12, 20, 0.65)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
        }}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          style={{
            display: "flex",
            alignItems: "center",
            width: "100%",
            height: "52px",
            borderRadius: "18px",
            backgroundColor: "rgba(10, 15, 25, 0.76)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(56, 189, 248, 0.22)",
            boxShadow:
              "0 10px 36px rgba(0, 0, 0, 0.45), 0 0 24px rgba(2, 132, 199, 0.12), inset 0 1px 1px rgba(255, 255, 255, 0.1)",
            padding: "5px 7px 5px 15px",
            gap: "8px",
          }}
        >
          <button
            type="button"
            title="Fayl biriktirish"
            style={{
              background: "transparent",
              border: "none",
              color: "rgba(255, 255, 255, 0.6)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <AttachIcon size={18} />
          </button>

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Mikasa bilan suhbatlashing... (Enter yuborish)"
            disabled={isLoading}
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#FFFFFF",
              fontSize: "14px",
            }}
          />

          <button
            type="button"
            onClick={onNavigateVoice}
            title="Ovozli muloqot rejimiga o‘tish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "34px",
              height: "34px",
              borderRadius: "10px",
              color: "rgba(255, 255, 255, 0.65)",
              background: "transparent",
              border: "none",
              cursor: "pointer",
            }}
          >
            <MicIcon size={17} />
          </button>

          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            title="Yuborish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "36px",
              height: "36px",
              borderRadius: "50%",
              backgroundColor: input.trim() && !isLoading ? "#0284C7" : "rgba(255, 255, 255, 0.08)",
              color: "#FFFFFF",
              border: input.trim() && !isLoading ? "1px solid rgba(56, 189, 248, 0.5)" : "none",
              cursor: input.trim() && !isLoading ? "pointer" : "default",
              transition: "all 0.15s ease",
            }}
          >
            <ArrowUpIcon size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};
