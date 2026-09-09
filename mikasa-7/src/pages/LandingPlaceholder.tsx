import React, { useState } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import { StatusIndicator } from "../components/StatusIndicator";
import { Button } from "../components/Button";
import { SparklesIcon, MicIcon, ChatIcon, CommandsIcon, CircleDotIcon, AttachIcon, SendIcon } from "../components/icons/Icons";

interface LandingPlaceholderProps {
  onNavigate: (path: string) => void;
}

export const LandingPlaceholder: React.FC<LandingPlaceholderProps> = ({ onNavigate }) => {
  const [inputText, setInputText] = useState("");

  const handleClear = () => {
    setInputText("");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    // In future, will pass prompt to chat
    setInputText("");
    onNavigate("/chat");
  };

  return (
    <div
      className="landing-placeholder"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        width: "100%",
        padding: "24px",
        overflowY: "auto",
        userSelect: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          maxWidth: "520px",
          width: "100%",
          margin: "auto 0",
        }}
      >
        {/* Subtle Top Sparkle */}
        <div style={{ marginBottom: "6px", opacity: 0.8 }}>
          <SparklesIcon size={14} color="var(--primary-glow)" />
        </div>

        {/* Central Orb Foundation */}
        <div style={{ marginBottom: "16px" }}>
          <MikasaOrb size={150} state="idle" />
        </div>

        {/* Confident Greeting */}
        <h1
          style={{
            fontSize: "var(--font-size-display)",
            fontWeight: 700,
            letterSpacing: "-0.01em",
            color: "var(--text-primary)",
            marginBottom: "4px",
            textAlign: "center",
          }}
        >
          Salom, Muxammadaziz
        </h1>

        <p
          style={{
            fontSize: "var(--font-size-title)",
            color: "var(--text-secondary)",
            marginBottom: "12px",
            textAlign: "center",
          }}
        >
          Qanday yordam beray?
        </p>

        {/* Genuine Status Indicator */}
        <div style={{ marginBottom: "20px" }}>
          <StatusIndicator online={true} label="Online" />
        </div>

        {/* Primary Action Button (Voice CTA) */}
        <Button
          variant="primary"
          size="lg"
          icon={<MicIcon size={18} color="#FFFFFF" />}
          onClick={() => onNavigate("/voice")}
          style={{ width: "320px", height: "44px", marginBottom: "12px" }}
        >
          Tinglashni boshlash
        </Button>

        {/* Secondary Action Buttons */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            style={{
              width: "100px",
              height: "32px",
              border: "1px solid var(--border)",
              color: "var(--text-muted)",
            }}
          >
            Tozalash
          </Button>

          <Button
            variant="glass"
            size="sm"
            icon={<ChatIcon size={14} color="var(--primary-glow)" />}
            onClick={() => onNavigate("/chat")}
            style={{ width: "100px", height: "32px" }}
          >
            Chat
          </Button>
        </div>

        {/* 3 Quick Action Suggestion Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: "10px",
            width: "100%",
            marginBottom: "20px",
          }}
        >
          <SuggestionCard
            icon={<SparklesIcon size={15} color="var(--primary-glow)" />}
            title="So‘rash"
            subtitle="Savol berish"
            onClick={() => onNavigate("/chat")}
          />
          <SuggestionCard
            icon={<CommandsIcon size={15} color="var(--secondary)" />}
            title="Buyruq"
            subtitle="Tizim amallari"
            onClick={() => onNavigate("/commands")}
          />
          <SuggestionCard
            icon={<CircleDotIcon size={12} color="var(--accent)" />}
            title="Xulosa"
            subtitle="Matn tahlili"
            onClick={() => onNavigate("/chat")}
          />
        </div>

        {/* Compact AI Composer */}
        <form
          onSubmit={handleSubmit}
          style={{
            display: "flex",
            alignItems: "center",
            width: "100%",
            height: "46px",
            borderRadius: "var(--radius-pill)",
            backgroundColor: "var(--bg-input)",
            border: "1px solid var(--border)",
            padding: "4px 8px 4px 12px",
            transition: "border-color 0.15s ease",
          }}
          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--primary)")}
          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
        >
          <button
            type="button"
            title="Fayl biriktirish"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "30px",
              height: "30px",
              borderRadius: "50%",
              color: "var(--text-muted)",
              cursor: "pointer",
            }}
          >
            <AttachIcon size={15} />
          </button>

          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Nima yordam kerak?"
            style={{
              flex: 1,
              background: "transparent",
              color: "var(--text-primary)",
              padding: "0 10px",
              fontSize: "var(--font-size-body)",
            }}
          />

          <button
            type="submit"
            title={inputText.trim() ? "Yuborish" : "Ovozli muloqot"}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: inputText.trim() ? "var(--primary)" : "var(--surface-hover)",
              color: inputText.trim() ? "#FFFFFF" : "var(--primary-glow)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            {inputText.trim() ? <SendIcon size={14} /> : <MicIcon size={15} />}
          </button>
        </form>
      </div>
    </div>
  );
};

const SuggestionCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  onClick: () => void;
}> = ({ icon, title, subtitle, onClick }) => {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "4px",
        padding: "10px 12px",
        borderRadius: "var(--radius-md)",
        backgroundColor: "var(--surface)",
        border: "1px solid var(--border-subtle)",
        cursor: "pointer",
        transition: "all 0.15s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "var(--surface-hover)";
        e.currentTarget.style.borderColor = "var(--glass-border)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "var(--surface)";
        e.currentTarget.style.borderColor = "var(--border-subtle)";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
        {icon}
        <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{title}</span>
      </div>
      <span style={{ fontSize: "10.5px", color: "var(--text-muted)" }}>{subtitle}</span>
    </div>
  );
};
