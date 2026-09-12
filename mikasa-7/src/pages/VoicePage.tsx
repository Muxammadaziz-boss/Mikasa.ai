// ========== VoicePage.tsx ==========
// Mikasa AI 7.0 — Ovozli Muloqot Sahifasi
// Markaziy interaktiv MikasaOrb va real vaqtli STT/TTS ovoz boshqaruvi

import React, { useState, useEffect } from "react";
import { MikasaOrb } from "../components/MikasaOrb";
import {
  MicIcon,
  HomeIcon,
  ChatIcon,
  UserIcon,
  SparklesIcon,
  RefreshIcon,
} from "../components/icons/Icons";
import { backendService, VoiceState, BackendStatus } from "../services/backendService";

interface VoicePageProps {
  userName?: string;
  onNavigateHome: () => void;
  onNavigateChat: () => void;
}

export const VoicePage: React.FC<VoicePageProps> = ({
  userName = "Ustoz",
  onNavigateHome,
  onNavigateChat,
}) => {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({ status: "connecting" });
  const [userTranscript, setUserTranscript] = useState<string>("");
  const [lastTranscript, setLastTranscript] = useState<string>("");

  useEffect(() => {
    const unsubVoice = backendService.onVoiceStateChange((state) => {
      setVoiceState(state);
    });
    const unsubStatus = backendService.onStatusChange((status) => {
      setBackendStatus(status);
    });
    const unsubResp = backendService.onResponse((data) => {
      setLastTranscript(data.text);
    });
    const unsubTranscript = backendService.onTranscript((data) => {
      if (data.sender === "user") {
        setUserTranscript(data.text);
      } else {
        setLastTranscript(data.text);
      }
    });
    return () => {
      unsubVoice();
      unsubStatus();
      unsubResp();
      unsubTranscript();
    };
  }, []);

  const handleToggleVoice = async () => {
    if (voiceState === "listening") {
      await backendService.stopVoice();
    } else {
      setUserTranscript("");
      setLastTranscript("");
      await backendService.startVoice();
    }
  };

  const handleReplayVoice = async () => {
    if (lastTranscript) {
      await backendService.speakText(lastTranscript);
    }
  };

  const effectiveOrbState: "idle" | "listening" | "thinking" | "speaking" | "loading" | "error" | "offline" =
    backendStatus.status === "offline"
      ? "offline"
      : backendStatus.status === "connecting"
      ? "loading"
      : voiceState;

  const getStateDescription = () => {
    switch (effectiveOrbState) {
      case "listening":
        return "Sizni eshitmoqdaman... Gapiring";
      case "thinking":
        return "Mikasa o'ylamoqda...";
      case "speaking":
        return "Mikasa gapirmoqda...";
      case "offline":
        return "Ovoz tizimi hozirda mavjud emas. Backend serveriga ulanishda muammo. Qayta ulanish kutilmoqda...";
      case "loading":
        return "Audio tizimiga ulanilmoqda...";
      case "error":
        return "Ovoz tizimida xatolik yuz berdi. Mikrofon ruxsatini tekshiring yoki qayta urinib ko'ring.";
      case "idle":
      default:
        return "Muloqotni boshlash uchun tugmani bosing";
    }
  };

  return (
    <div
      className="voice-page-container"
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
      {/* 1. Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 24px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
          backgroundColor: "rgba(8, 12, 20, 0.65)",
          backdropFilter: "blur(20px)",
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
            <span style={{ fontSize: "15px", fontWeight: 700, color: "#FFFFFF" }}>
              Ovozli muloqot
            </span>
            <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              {backendStatus.status === "online" ? "Python Audio Service Faol" : "Backendga ulanilmoqda..."}
            </div>
          </div>
        </div>

        <button
          onClick={onNavigateChat}
          title="Matnli chatga o‘tish"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 14px",
            borderRadius: "10px",
            backgroundColor: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            color: "var(--text-secondary)",
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          <ChatIcon size={14} />
          <span>Matnli suhbat</span>
        </button>
      </div>

      {/* 2. Markaziy yirik Orb va Ovoz holati */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "32px",
          gap: "24px",
          textAlign: "center",
          overflowY: "auto",
        }}
      >
        <div
          onClick={handleToggleVoice}
          style={{
            cursor: "pointer",
            transition: "transform 0.2s ease",
            transform: voiceState === "listening" || voiceState === "speaking" ? "scale(1.05)" : "scale(1)",
          }}
          title={voiceState === "listening" ? "Tinglashni to'xtatish" : "Tinglashni boshlash"}
        >
          <MikasaOrb size={200} state={effectiveOrbState} />
        </div>

        <div>
          <h2
            className="text-metallic-gradient"
            style={{ fontSize: "28px", fontWeight: 700, margin: "0 0 8px 0" }}
          >
            Salom, {userName || backendStatus.user || "Ustoz"}
          </h2>
          <p
            style={{
              fontSize: "15px",
              color: voiceState === "listening" ? "var(--primary-glow)" : voiceState === "speaking" ? "#10B981" : "var(--text-secondary)",
              fontWeight: 500,
              margin: 0,
              transition: "color 0.2s ease",
            }}
          >
            {getStateDescription()}
          </p>
        </div>

        {/* Foydalanuvchi aytgan so'z */}
        {userTranscript && (
          <div
            style={{
              maxWidth: "520px",
              width: "100%",
              padding: "10px 16px",
              borderRadius: "14px",
              backgroundColor: "rgba(2, 132, 199, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              color: "#FFFFFF",
              fontSize: "13.5px",
              textAlign: "left",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "var(--primary-glow)", fontWeight: 600, marginBottom: "4px" }}>
              <UserIcon size={13} color="var(--primary-glow)" />
              <span>Siz aytgan buyruq:</span>
            </div>
            {userTranscript}
          </div>
        )}

        {/* So'nggi javob / transkript kartochkasi */}
        {lastTranscript && (
          <div
            style={{
              maxWidth: "520px",
              width: "100%",
              padding: "14px 18px",
              borderRadius: "16px",
              backgroundColor: "rgba(12, 18, 30, 0.72)",
              backdropFilter: "blur(24px)",
              border: "1px solid rgba(56, 189, 248, 0.25)",
              color: "#FFFFFF",
              fontSize: "13.5px",
              lineHeight: 1.5,
              textAlign: "left",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "var(--primary-glow)", fontWeight: 600 }}>
                <SparklesIcon size={13} color="var(--primary-glow)" />
                <span>Mikasa javobi:</span>
              </div>
              <button
                onClick={handleReplayVoice}
                title="Ovozni qayta tinglash"
                style={{
                  background: "rgba(255, 255, 255, 0.08)",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                  borderRadius: "6px",
                  padding: "3px 8px",
                  color: "#38BDF8",
                  fontSize: "11px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "5px",
                }}
              >
                <RefreshIcon size={12} color="#38BDF8" />
                <span>Qayta eshitish</span>
              </button>
            </div>
            {lastTranscript}
          </div>
        )}

        {/* Asosiy Ovoz Boshqaruv Tugmasi */}
        <button
          onClick={handleToggleVoice}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            padding: "14px 36px",
            borderRadius: "var(--radius-pill)",
            background:
              voiceState === "listening"
                ? "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
                : "linear-gradient(135deg, #0284C7 0%, #0369A1 100%)",
            border:
              voiceState === "listening"
                ? "1px solid rgba(239, 68, 68, 0.55)"
                : "1px solid rgba(56, 189, 248, 0.45)",
            boxShadow:
              voiceState === "listening"
                ? "0 6px 28px rgba(239, 68, 68, 0.45)"
                : "0 6px 28px rgba(2, 132, 199, 0.45)",
            color: "#FFFFFF",
            fontSize: "15px",
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.15s ease",
            marginTop: "12px",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = "translateY(-2px)")}
          onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0)")}
        >
          <MicIcon size={18} color="#FFFFFF" />
          <span>{voiceState === "listening" ? "Tinglashni to‘xtatish" : "Tinglashni boshlash"}</span>
        </button>
      </div>
    </div>
  );
};
