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
        padding: "20px 24px 30px 24px",
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
          maxWidth: "600px",
          width: "100%",
          margin: "auto 0",
          gap: "16px",
        }}
      >
        {/* Centered AI Orb with calm breathing animation */}
        <div
          className="hero-orb-wrapper"
          style={{
            cursor: "pointer",
            marginBottom: "4px",
            transition: "transform 0.2s ease",
          }}
          onClick={() => onNavigate("/voice")}
          title="Ovozli muloqotni boshlash"
        >
          <MikasaOrb size={145} state="idle" />
        </div>

        {/* Hero Greeting Typography */}
        <div style={{ textAlign: "center" }}>
          <h1
            className="text-metallic-gradient"
            style={{
              fontSize: "clamp(28px, 4vw, 38px)",
              fontWeight: 700,
              letterSpacing: "-0.02em",
              lineHeight: 1.15,
              marginBottom: "6px",
            }}
          >
            Salom, {userName}
          </h1>

          <p
            style={{
              fontSize: "clamp(14px, 1.8vw, 17px)",
              color: "var(--text-secondary)",
              fontWeight: 400,
              letterSpacing: "0.01em",
            }}
          >
            Bugun sizga qanday yordam bera olaman?
          </p>
        </div>

        {/* Real Status Badge */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "7px",
            padding: "4px 14px",
            borderRadius: "var(--radius-pill)",
            backgroundColor: "rgba(16, 185, 129, 0.1)",
            border: "1px solid rgba(16, 185, 129, 0.25)",
            fontSize: "12px",
            color: "#6EE7B7",
            letterSpacing: "0.02em",
          }}
        >
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: "#10B981",
              boxShadow: "0 0 8px #10B981",
            }}
          />
          <span>Online</span>
        </div>

        {/* Primary Voice CTA & Secondary Actions Bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "10px",
            width: "100%",
            marginTop: "2px",
          }}
        >
          <button
            onClick={() => onNavigate("/voice")}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              padding: "10px 24px",
              borderRadius: "var(--radius-pill)",
              background: "linear-gradient(135deg, #0284C7 0%, #0369A1 100%)",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              boxShadow: "0 4px 20px rgba(2, 132, 199, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.3)",
              color: "#FFFFFF",
              fontSize: "13.5px",
              fontWeight: 600,
              letterSpacing: "0.02em",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "translateY(-1px)";
              e.currentTarget.style.boxShadow = "0 6px 24px rgba(2, 132, 199, 0.45)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "0 4px 20px rgba(2, 132, 199, 0.35)";
            }}
          >
            <MicIcon size={16} color="#FFFFFF" />
            <span>Tinglashni boshlash</span>
          </button>

          <button
            onClick={handleClear}
            title="Yozuvni tozalash"
            aria-label="Yozuvni tozalash"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              padding: "10px 16px",
              borderRadius: "var(--radius-pill)",
              backgroundColor: "rgba(14, 19, 31, 0.55)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "var(--text-secondary)",
              fontSize: "13px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.color = "#FFFFFF";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(14, 19, 31, 0.55)";
              e.currentTarget.style.color = "var(--text-secondary)";
            }}
          >
            <TrashIcon size={14} color="currentColor" />
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
              padding: "10px 18px",
              borderRadius: "var(--radius-pill)",
              backgroundColor: "rgba(14, 19, 31, 0.55)",
              border: "1px solid rgba(56, 189, 248, 0.2)",
              color: "var(--text-primary)",
              fontSize: "13px",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(2, 132, 199, 0.18)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.4)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(14, 19, 31, 0.55)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.2)";
            }}
          >
            <ChatIcon size={14} color="var(--primary-glow)" />
            <span>Chat</span>
          </button>
        </div>

        {/* Central AI Composer Capsule */}
        <form
          onSubmit={handleSubmit}
          className="landing-composer"
          style={{
            display: "flex",
            alignItems: "center",
            width: "100%",
            height: "56px",
            borderRadius: "20px",
            backgroundColor: "rgba(10, 15, 25, 0.72)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(56, 189, 248, 0.25)",
            boxShadow: "0 10px 36px rgba(0, 0, 0, 0.45), 0 0 24px rgba(2, 132, 199, 0.15), inset 0 1px 1px rgba(255, 255, 255, 0.12)",
            padding: "6px 8px 6px 16px",
            gap: "10px",
            transition: "all 0.2s ease",
          }}
          onFocusCapture={(e) => {
            e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.55)";
            e.currentTarget.style.boxShadow = "0 12px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(2, 132, 199, 0.25)";
          }}
          onBlurCapture={(e) => {
            e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.25)";
            e.currentTarget.style.boxShadow = "0 10px 36px rgba(0, 0, 0, 0.45), 0 0 24px rgba(2, 132, 199, 0.15)";
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
              width: "34px",
              height: "34px",
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
            <AttachIcon size={19} />
          </button>

          {/* Text input */}
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Menga yozing..."
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#FFFFFF",
              fontSize: "15px",
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
              width: "36px",
              height: "36px",
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
            <MicIcon size={18} />
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
              width: "38px",
              height: "38px",
              borderRadius: "50%",
              backgroundColor: "#0284C7",
              boxShadow: "0 0 16px rgba(56, 189, 248, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.4)",
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
            <ArrowUpIcon size={17} color="#FFFFFF" />
          </button>
        </form>

        {/* 3 Quick Action Suggestion Cards matching the reference layout */}
        <div
          className="landing-quick-actions"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "12px",
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
              gap: "12px",
              padding: "14px 16px",
              borderRadius: "16px",
              backgroundColor: "rgba(12, 18, 30, 0.65)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              boxShadow: "0 0 18px rgba(2, 132, 199, 0.15)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(20, 28, 45, 0.8)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.5)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(12, 18, 30, 0.65)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.3)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "28px",
                height: "28px",
                borderRadius: "8px",
                backgroundColor: "rgba(2, 132, 199, 0.2)",
                flexShrink: 0,
              }}
            >
              <SparklesIcon size={15} color="var(--primary-glow)" />
            </div>

            <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
              <span style={{ fontSize: "13.5px", fontWeight: 600, color: "#FFFFFF" }}>
                So‘rash
              </span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
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
              gap: "12px",
              padding: "14px 16px",
              borderRadius: "16px",
              backgroundColor: "rgba(12, 18, 30, 0.65)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(20, 28, 45, 0.8)";
              e.currentTarget.style.borderColor = "rgba(245, 158, 11, 0.4)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(12, 18, 30, 0.65)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "28px",
                height: "28px",
                borderRadius: "8px",
                backgroundColor: "rgba(245, 158, 11, 0.15)",
                flexShrink: 0,
              }}
            >
              <CommandsIcon size={14} color="#F59E0B" />
            </div>

            <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
              <span style={{ fontSize: "13.5px", fontWeight: 600, color: "#FFFFFF" }}>
                Buyruq
              </span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
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
              gap: "12px",
              padding: "14px 16px",
              borderRadius: "16px",
              backgroundColor: "rgba(12, 18, 30, 0.65)",
              backdropFilter: "blur(20px)",
              WebkitBackdropFilter: "blur(20px)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(20, 28, 45, 0.8)";
              e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.4)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(12, 18, 30, 0.65)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "28px",
                height: "28px",
                borderRadius: "8px",
                backgroundColor: "rgba(139, 92, 246, 0.15)",
                flexShrink: 0,
              }}
            >
              <FileTextIcon size={14} color="#A78BFA" />
            </div>

            <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
              <span style={{ fontSize: "13.5px", fontWeight: 600, color: "#FFFFFF" }}>
                Xulosa
              </span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                Matn tahlili
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
