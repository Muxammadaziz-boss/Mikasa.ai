// ========== AccountPage.tsx ==========
// Mikasa AI 7.1.0 — Foydalanuvchi Hisobi va Tizim Sozlamalari
// config.json, foydalanuvchi_ismi.txt va ovoz_turi.txt bilan bog'langan

import React, { useState, useEffect } from "react";
import {
  UserIcon,
  HomeIcon,
  SparklesIcon,
  CheckIcon,
} from "../components/icons/Icons";
import {
  backendService,
  AccountSettings,
} from "../services/backendService";

interface AccountPageProps {
  onNavigateHome: () => void;
  onUserUpdated?: (name: string) => void;
}

export const AccountPage: React.FC<AccountPageProps> = ({ onNavigateHome, onUserUpdated }) => {
  const [name, setName] = useState(() => localStorage.getItem("mikasa_user_name") || "Ustoz");
  const [voiceType, setVoiceType] = useState<"ayol" | "erkak">("ayol");
  const [ttsSpeed, setTtsSpeed] = useState<number>(2.0);
  const [theme, setTheme] = useState<string>("dark");
  const [aiModel, setAiModel] = useState<string>("gemini");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchAccount = async () => {
      setLoading(true);
      const data: AccountSettings = await backendService.getAccount();
      if (mounted && data.ok) {
        const freshName = data.name || localStorage.getItem("mikasa_user_name") || "Ustoz";
        setName(freshName);
        setVoiceType(data.voice_type || "ayol");
        setTtsSpeed(data.tts_speed || 2.0);
        setTheme(data.theme || "dark");
        setAiModel(data.ai_model || "gemini");
        setLoading(false);
      }
    };
    fetchAccount();
    return () => {
      mounted = false;
    };
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSaving) return;
    setIsSaving(true);
    setSaveSuccess(false);

    const trimmedName = name.trim() || "Ustoz";
    const res = await backendService.updateAccount({
      name: trimmedName,
      voice_type: voiceType,
      tts_speed: ttsSpeed,
      theme,
    });

    if (res.ok) {
      setSaveSuccess(true);
      onUserUpdated?.(trimmedName);
      setTimeout(() => setSaveSuccess(false), 4000);
    }
    setIsSaving(false);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        background: "var(--bg-gradient)",
        color: "var(--text-primary)",
        overflowY: "auto",
        position: "relative",
      }}
    >
      {/* Header Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 28px",
          borderBottom: "1px solid var(--border-subtle)",
          background: "rgba(10, 15, 29, 0.75)",
          backdropFilter: "blur(20px)",
          position: "sticky",
          top: 0,
          zIndex: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: "50%",
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <UserIcon size={20} color="var(--primary-glow)" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>
                Hisob va Sozlamalar
              </h1>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 12,
                  background: "rgba(16, 185, 129, 0.15)",
                  color: "var(--primary-glow)",
                  fontWeight: 500,
                  border: "1px solid rgba(16, 185, 129, 0.2)",
                }}
              >
                v7.1.0
              </span>
            </div>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
              Foydalanuvchi profili, ovoz tanlovi va tizim parametrlari
            </p>
          </div>
        </div>

        <button
          onClick={onNavigateHome}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
            padding: "8px 14px",
            borderRadius: 8,
            fontSize: 12,
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "var(--text-primary)";
            e.currentTarget.style.borderColor = "var(--border-strong)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "var(--text-secondary)";
            e.currentTarget.style.borderColor = "var(--border-subtle)";
          }}
        >
          <HomeIcon size={14} />
          <span>Bosh sahifa</span>
        </button>
      </div>

      {/* Main Container */}
      <div
        style={{
          maxWidth: 900,
          width: "100%",
          margin: "0 auto",
          padding: "24px 28px 48px",
          display: "flex",
          flexDirection: "column",
          gap: 24,
        }}
      >
        {saveSuccess && (
          <div
            style={{
              padding: "12px 18px",
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.4)",
              borderRadius: 10,
              color: "#34d399",
              fontSize: 13,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <SparklesIcon size={16} color="#34d399" />
            <span>Sozlamalar muvaffaqiyatli saqlandi va kuchga kirdi!</span>
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
            Sozlamalar yuklanmoqda...
          </div>
        ) : (
          <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {/* Section 1: User Profile */}
            <div
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 14,
                padding: "20px 24px",
                display: "flex",
                flexDirection: "column",
                gap: 16,
              }}
            >
              <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Shaxsiy Profil</h2>

              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <label style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  Sizning Ismingiz
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{
                    background: "rgba(0, 0, 0, 0.25)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "10px 14px",
                    color: "var(--text-primary)",
                    fontSize: 14,
                    outline: "none",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "var(--primary-glow)")}
                  onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
                />
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  Mikasa sizga ushbu ism bilan murojaat qiladi
                </span>
              </div>
            </div>

            {/* Section 2: Voice Settings */}
            <div
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 14,
                padding: "20px 24px",
                display: "flex",
                flexDirection: "column",
                gap: 16,
              }}
            >
              <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Mikasa Ovozi va Nutq</h2>

              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <label style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  Ovoz Turini Tanlang
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div
                    onClick={() => setVoiceType("ayol")}
                    style={{
                      background:
                        voiceType === "ayol"
                          ? "rgba(16, 185, 129, 0.12)"
                          : "rgba(255, 255, 255, 0.02)",
                      border: `1.5px solid ${
                        voiceType === "ayol" ? "var(--primary-glow)" : "var(--border-subtle)"
                      }`,
                      borderRadius: 10,
                      padding: "14px 16px",
                      cursor: "pointer",
                      display: "flex",
                      flexDirection: "column",
                      gap: 4,
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <strong style={{ fontSize: 14, color: "var(--text-primary)" }}>
                        Madina (Ayol)
                      </strong>
                      {voiceType === "ayol" && (
                        <CheckIcon size={14} color="var(--primary-glow)" />
                      )}
                    </div>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Yumshoq, muloyim va aniq intonatsiya
                    </span>
                  </div>

                  <div
                    onClick={() => setVoiceType("erkak")}
                    style={{
                      background:
                        voiceType === "erkak"
                          ? "rgba(16, 185, 129, 0.12)"
                          : "rgba(255, 255, 255, 0.02)",
                      border: `1.5px solid ${
                        voiceType === "erkak" ? "var(--primary-glow)" : "var(--border-subtle)"
                      }`,
                      borderRadius: 10,
                      padding: "14px 16px",
                      cursor: "pointer",
                      display: "flex",
                      flexDirection: "column",
                      gap: 4,
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <strong style={{ fontSize: 14, color: "var(--text-primary)" }}>
                        Sardor (Erkak)
                      </strong>
                      {voiceType === "erkak" && (
                        <CheckIcon size={14} color="var(--primary-glow)" />
                      )}
                    </div>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Jiddiy, ishonchli va chuqur tembr
                    </span>
                  </div>
                </div>
              </div>

              {/* TTS Speed Slider */}
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                    Nutq Tezligi (TTS Speed)
                  </label>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "var(--primary-glow)" }}>
                    {ttsSpeed}x
                  </span>
                </div>
                <input
                  type="range"
                  min={1.0}
                  max={2.5}
                  step={0.1}
                  value={ttsSpeed}
                  onChange={(e) => setTtsSpeed(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "var(--primary-glow)", cursor: "pointer" }}
                />
              </div>
            </div>

            {/* Section 3: AI Engine Info */}
            <div
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 14,
                padding: "20px 24px",
                display: "flex",
                flexDirection: "column",
                gap: 14,
              }}
            >
              <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Sun'iy Intellekt Modeli</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
                <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 12, borderRadius: 8 }}>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Model</span>
                  <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, textTransform: "capitalize" }}>
                    {aiModel}
                  </div>
                </div>
                <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 12, borderRadius: 8 }}>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Backend Porti</span>
                  <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>127.0.0.1:18420</div>
                </div>
                <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 12, borderRadius: 8 }}>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Desktop Dvigatel</span>
                  <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, color: "var(--primary-glow)" }}>
                    Tauri 2 (Native Rust)
                  </div>
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="submit"
                disabled={isSaving}
                style={{
                  background: "var(--primary-glow)",
                  color: "#052e16",
                  border: "none",
                  borderRadius: 10,
                  padding: "12px 28px",
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: isSaving ? "default" : "pointer",
                  transition: "all 0.15s ease",
                  boxShadow: "0 4px 14px rgba(16, 185, 129, 0.3)",
                }}
              >
                {isSaving ? "Saqlanmoqda..." : "Sozlamalarni Saqlash"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
export default AccountPage;
