import React, { useState, useRef } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import {
  MicIcon,
  ChatIcon,
  SparklesIcon,
  CommandsIcon,
  FileTextIcon,
  AttachIcon,
  ArrowUpIcon,
  TrashIcon,
} from "../components/icons/Icons";

interface LandingPageProps {
  userName?: string;
  onNavigate: (path: string, initialPrompt?: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  userName = "Muxammadaziz",
  onNavigate,
}) => {
  const [inputText, setInputText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleClear = () => {
    setInputText("");
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = inputText.trim();
    if (!query) return;
    setInputText("");
    onNavigate("/chat", query);
  };

  const handleQuickAction = (mode: "ask" | "command" | "summary") => {
    if (mode === "ask") {
      setInputText("Savol: ");
      inputRef.current?.focus();
    } else if (mode === "command") {
      onNavigate("/commands");
    } else if (mode === "summary") {
      setInputText("Quyidagi matnni tahlil qilib xulosa ber: ");
      inputRef.current?.focus();
    }
  };

  return (
    <div
      className="landing-page"
      style={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
        padding: "20px 24px 32px 24px",
        overflowY: "auto",
        overflowX: "hidden",
        zIndex: 2,
        userSelect: "none",
      }}
    >
      <div
        className="landing-hero-container"
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          maxWidth: "580px",
          width: "100%",
          margin: "auto 0",
          gap: "clamp(10px, 1.7vh, 16px)",
        }}
      >
        {/* 1. MIKASA ORB (Primary Visual Focal Point) */}
        <div
          className="hero-orb-wrapper"
          style={{
            cursor: "pointer",
            marginTop: "2px",
            marginBottom: "2px",
            transition: "transform 0.2s ease",
          }}
          onClick={() => onNavigate("/voice")}
          title="Ovozli muloqotni boshlash"
        >
          <MikasaOrb size="clamp(145px, 16vw, 180px)" state="idle" />
        </div>

        {/* 2. GREETING (Salom, Muxammadaziz / Qanday yordam beray?) */}
        <div style={{ textAlign: "center" }}>
          <h1
            className="text-metallic-gradient"
            style={{
              fontSize: "clamp(30px, 3.6vw, 38px)",
              fontWeight: 700,
              letterSpacing: "-0.02em",
              lineHeight: 1.15,
              marginBottom: "4px",
            }}
          >
            Salom, {userName}
          </h1>

          <p
            style={{
              fontSize: "clamp(14.5px, 1.6vw, 16.5px)",
              color: "var(--text-secondary)",
              fontWeight: 400,
              letterSpacing: "0.01em",
            }}
          >
            Qanday yordam beray?
          </p>
        </div>

        {/* 3. ONLINE STATUS (Subtle indicator, not a heavy badge) */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "7px",
            padding: "2px 8px",
            fontSize: "11.5px",
            color: "var(--text-muted)",
            letterSpacing: "0.02em",
          }}
        >
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: "#10B981",
              boxShadow: "0 0 8px rgba(16, 185, 129, 0.7)",
            }}
          />
          <span style={{ color: "#94A3B8" }}>Online</span>
        </div>

        {/* 4. PRIMARY VOICE ACTION (Tinglashni boshlash) */}
        <div style={{ width: "100%", display: "flex", justifyContent: "center" }}>
          <button
            onClick={() => onNavigate("/voice")}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              padding: "11px 28px",
              borderRadius: "var(--radius-pill)",
              background: "linear-gradient(135deg, #0284C7 0%, #0369A1 100%)",
              border: "1px solid rgba(56, 189, 248, 0.45)",
              boxShadow: "0 4px 22px rgba(2, 132, 199, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.35)",
              color: "#FFFFFF",
              fontSize: "14px",
              fontWeight: 600,
              letterSpacing: "0.02em",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-1px)";
              e.currentTarget.style.boxShadow = "0 6px 26px rgba(2, 132, 199, 0.55)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 4px 22px rgba(2, 132, 199, 0.4)";
            }}
          >
            <MicIcon size={16} color="#FFFFFF" />
            <span>Tinglashni boshlash</span>
          </button>
        </div>

        {/* 5. SECONDARY BUTTONS (Tozalash & Chat — quieter visual weight) */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "10px",
          }}
        >
          <button
            onClick={handleClear}
            title="Yozuvni tozalash"
            aria-label="Yozuvni tozalash"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              padding: "8px 16px",
              borderRadius: "var(--radius-pill)",
              backgroundColor: "rgba(14, 20, 32, 0.5)",
              border: "1px solid rgba(255, 255, 255, 0.07)",
              color: "var(--text-muted)",
              fontSize: "12.5px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(14, 20, 32, 0.5)";
              e.currentTarget.style.color = "var(--text-muted)";
            }}
          >
            <TrashIcon size={13} color="currentColor" />
            <span>Tozalash</span>
          </button>

          <button
            onClick={() => onNavigate("/chat")}
            title="AI Suhbat sahifasiga o'tish"
            aria-label="AI Suhbat sahifasiga o'tish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              padding: "8px 18px",
              borderRadius: "var(--radius-pill)",
              backgroundColor: "rgba(14, 20, 32, 0.5)",
              border: "1px solid rgba(56, 189, 248, 0.18)",
              color: "var(--text-secondary)",
              fontSize: "12.5px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(2, 132, 199, 0.14)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.35)";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(14, 20, 32, 0.5)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.18)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
          >
            <ChatIcon size={13} color="var(--primary-glow)" />
            <span>Chat</span>
          </button>
        </div>

        {/* 6. QUICK ACTIONS (So‘rash, Buyruq, Xulosa — placed ABOVE Composer) */}
        <div
          className="landing-quick-actions"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "10px",
            width: "100%",
            marginTop: "2px",
          }}
        >
          {/* Card 1: So'rash */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => handleQuickAction("ask")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "14px",
              backgroundColor: "rgba(12, 18, 30, 0.6)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              border: "1px solid rgba(56, 189, 248, 0.28)",
              boxShadow: "0 0 16px rgba(2, 132, 199, 0.12)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(20, 28, 45, 0.75)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.5)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(12, 18, 30, 0.6)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.28)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "26px",
                height: "26px",
                borderRadius: "8px",
                backgroundColor: "rgba(2, 132, 199, 0.2)",
                flexShrink: 0,
              }}
            >
              <SparklesIcon size={14} color="var(--primary-glow)" />
            </div>

            <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
              <span style={{ fontSize: "13px", fontWeight: 600, color: "#FFFFFF" }}>
                So‘rash
              </span>
              <span style={{ fontSize: "10.5px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                Savol berish
              </span>
            </div>
          </div>

          {/* Card 2: Buyruq */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => handleQuickAction("command")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "14px",
              backgroundColor: "rgba(12, 18, 30, 0.6)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(20, 28, 45, 0.75)";
              e.currentTarget.style.borderColor = "rgba(245, 158, 11, 0.4)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(12, 18, 30, 0.6)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "26px",
                height: "26px",
                borderRadius: "8px",
                backgroundColor: "rgba(245, 158, 11, 0.15)",
                flexShrink: 0,
              }}
            >
              <CommandsIcon size={13} color="#F59E0B" />
            </div>

            <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
              <span style={{ fontSize: "13px", fontWeight: 600, color: "#FFFFFF" }}>
                Buyruq
              </span>
              <span style={{ fontSize: "10.5px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                Tizim amallari
              </span>
            </div>
          </div>

          {/* Card 3: Xulosa */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => handleQuickAction("summary")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "14px",
              backgroundColor: "rgba(12, 18, 30, 0.6)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(20, 28, 45, 0.75)";
              e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.4)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(12, 18, 30, 0.6)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "26px",
                height: "26px",
                borderRadius: "8px",
                backgroundColor: "rgba(139, 92, 246, 0.15)",
                flexShrink: 0,
              }}
            >
              <FileTextIcon size={13} color="#A78BFA" />
            </div>

            <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
              <span style={{ fontSize: "13px", fontWeight: 600, color: "#FFFFFF" }}>
                Xulosa
              </span>
              <span style={{ fontSize: "10.5px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                Matn tahlili
              </span>
            </div>
          </div>
        </div>

        {/* 7. AI COMPOSER (Floating focused input at the bottom of hero stack) */}
        <form
          onSubmit={handleSubmit}
          className="landing-composer"
          style={{
            display: "flex",
            alignItems: "center",
            width: "100%",
            height: "54px",
            borderRadius: "20px",
            backgroundColor: "rgba(10, 15, 25, 0.76)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(56, 189, 248, 0.22)",
            boxShadow: "0 10px 36px rgba(0, 0, 0, 0.45), 0 0 24px rgba(2, 132, 199, 0.12), inset 0 1px 1px rgba(255, 255, 255, 0.1)",
            padding: "5px 7px 5px 15px",
            gap: "10px",
            transition: "all 0.2s ease",
            marginTop: "2px",
          }}
          onFocusCapture={(e) => {
            e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.5)";
            e.currentTarget.style.boxShadow = "0 12px 40px rgba(0, 0, 0, 0.5), 0 0 28px rgba(2, 132, 199, 0.22)";
          }}
          onBlurCapture={(e) => {
            e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.22)";
            e.currentTarget.style.boxShadow = "0 10px 36px rgba(0, 0, 0, 0.45), 0 0 24px rgba(2, 132, 199, 0.12)";
          }}
        >
          {/* Attachment button */}
          <button
            type="button"
            title="Fayl biriktirish"
            aria-label="Fayl biriktirish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "32px",
              height: "32px",
              borderRadius: "10px",
              color: "rgba(255, 255, 255, 0.6)",
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
              e.currentTarget.style.color = "rgba(255, 255, 255, 0.6)";
            }}
          >
            <AttachIcon size={18} />
          </button>

          {/* Text input with concise placeholder */}
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Nima yordam kerak?"
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

          {/* Microphone button */}
          <button
            type="button"
            onClick={() => onNavigate("/voice")}
            title="Ovozli gapirish"
            aria-label="Ovozli gapirish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "34px",
              height: "34px",
              borderRadius: "10px",
              color: "rgba(255, 255, 255, 0.65)",
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

          {/* Circular Glowing Send Button */}
          <button
            type="submit"
            title="Yuborish"
            aria-label="Yuborish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "36px",
              height: "36px",
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
    </div>
  );
};
