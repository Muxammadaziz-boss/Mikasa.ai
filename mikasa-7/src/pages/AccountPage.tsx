// ========== AccountPage.tsx ==========
// Mikasa AI 7.1.0 — Phase 15: Foydalanuvchi Hisobi va Tizim Sozlamalari
// Profil, Tashqi ko'rinish, Ovoz, AI modeli, Bildirishnomalar, Maxfiylik va Dastur haqida

import React, { useState, useEffect } from "react";
import {
  UserIcon,
  HomeIcon,
  SparklesIcon,
  CheckIcon,
  PaletteIcon,
  VolumeIcon,
  CpuIcon,
  BellIcon,
  ShieldIcon,
  InfoIcon,
  KeyIcon,
  PlayIcon,
  TrashIcon,
} from "../components/icons/Icons";
import { Avatar } from "../components/Avatar";
import {
  backendService,
  AccountSettings,
} from "../services/backendService";

interface AccountPageProps {
  onNavigateHome: () => void;
  onUserUpdated?: (name: string, avatar?: string) => void;
}

type TabType =
  | "profile"
  | "appearance"
  | "voice"
  | "ai"
  | "notifications"
  | "privacy"
  | "about";

const AVATAR_PALETTES = [
  { id: "emerald", name: "Zumrad Zangori", color: "#10B981" },
  { id: "blue", name: "Kiber Moviy", color: "#0284C7" },
  { id: "purple", name: "Neon Binafsha", color: "#8B5CF6" },
  { id: "cyan", name: "Yorqin Feruza", color: "#06B6D4" },
  { id: "gold", name: "Oltin Quyosh", color: "#F59E0B" },
  { id: "rose", name: "Nozik Atirgul", color: "#F43F5E" },
];

export const AccountPage: React.FC<AccountPageProps> = ({ onNavigateHome, onUserUpdated }) => {
  const [activeTab, setActiveTab] = useState<TabType>("profile");
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [testingVoice, setTestingVoice] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);

  // Profile Form State
  const [name, setName] = useState(() => localStorage.getItem("mikasa_user_name") || "Ustoz");
  const [avatar, setAvatar] = useState(() => localStorage.getItem("mikasa_user_avatar") || "emerald");
  const [role, setRole] = useState("Dasturchi / Muhandis");
  const [bio, setBio] = useState("Mikasa AI shaxsiy sun'iy intellekt yordamchisi");
  const [language, setLanguage] = useState("uz");

  // Appearance State
  const [theme, setTheme] = useState("dark");
  const [colorScheme, setColorScheme] = useState("green");
  const [animations, setAnimations] = useState(true);
  const [compactMode, setCompactMode] = useState(false);
  const [glassmorphism, setGlassmorphism] = useState(true);

  // Voice State
  const [voiceType, setVoiceType] = useState<"ayol" | "erkak">("ayol");
  const [ttsSpeed, setTtsSpeed] = useState<number>(2.0);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [vadEnabled, setVadEnabled] = useState(true);

  // AI State
  const [aiModel, setAiModel] = useState("gemini");
  const [aiMode, setAiMode] = useState("balanced");
  const [thinkingEnabled, setThinkingEnabled] = useState(true);
  const [geminiApiKey, setGeminiApiKey] = useState("");
  const [hasGeminiKey, setHasGeminiKey] = useState(false);

  // Notifications State
  const [notifScheduler, setNotifScheduler] = useState(true);
  const [notifVoice, setNotifVoice] = useState(true);
  const [notifSoundEffects, setNotifSoundEffects] = useState(true);

  // Privacy State
  const [localStorageOnly, setLocalStorageOnly] = useState(true);
  const [telemetryDisabled, setTelemetryDisabled] = useState(true);
  const [saveConversations, setSaveConversations] = useState(true);

  // App Info State
  const [appInfo, setAppInfo] = useState({
    name: "Mikasa AI",
    version: "7.1.0",
    codename: "Quiet Intelligence",
    engine: "Tauri 2.0 (Native Rust) + Python 3.11+",
    architecture: "Windows x64 Native Desktop",
    developer: "Mikasa Core Team",
    license: "Personal / Commercial AI Assistant",
  });

  useEffect(() => {
    let mounted = true;
    const fetchAccount = async () => {
      setLoading(true);
      const data: AccountSettings = await backendService.getAccount();
      if (mounted && data) {
        const freshName = data.name || localStorage.getItem("mikasa_user_name") || "Ustoz";
        const freshAvatar = data.avatar || localStorage.getItem("mikasa_user_avatar") || "emerald";
        setName(freshName);
        setAvatar(freshAvatar);
        if (data.role) setRole(data.role);
        if (data.bio) setBio(data.bio);
        if (data.language) setLanguage(data.language);

        setVoiceType(data.voice_type || "ayol");
        setTtsSpeed(data.tts_speed || 2.0);
        if (data.auto_speak !== undefined) setAutoSpeak(data.auto_speak);
        if (data.vad_enabled !== undefined) setVadEnabled(data.vad_enabled);

        setTheme(data.theme || "dark");
        if (data.color_scheme) setColorScheme(data.color_scheme);
        if (data.animations !== undefined) setAnimations(data.animations);
        if (data.compact_mode !== undefined) setCompactMode(data.compact_mode);
        if (data.glassmorphism !== undefined) setGlassmorphism(data.glassmorphism);

        setAiModel(data.ai_model || "gemini");
        if (data.ai_mode) setAiMode(data.ai_mode);
        if (data.thinking_enabled !== undefined) setThinkingEnabled(data.thinking_enabled);
        if (data.has_gemini_key !== undefined) setHasGeminiKey(data.has_gemini_key);

        if (data.notifications) {
          setNotifScheduler(data.notifications.scheduler ?? true);
          setNotifVoice(data.notifications.voice ?? true);
          setNotifSoundEffects(data.notifications.sound_effects ?? true);
        }

        if (data.privacy) {
          setLocalStorageOnly(data.privacy.local_storage_only ?? true);
          setTelemetryDisabled(data.privacy.telemetry_disabled ?? true);
          setSaveConversations(data.privacy.save_conversations ?? true);
        }

        if (data.app_info) {
          setAppInfo((prev) => ({ ...prev, ...data.app_info }));
        }

        setLoading(false);
      }
    };
    fetchAccount();
    return () => {
      mounted = false;
    };
  }, []);

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (isSaving) return;
    setIsSaving(true);
    setSaveSuccess(false);

    const trimmedName = name.trim() || "Ustoz";
    const payload: Partial<AccountSettings> & { gemini_api_key?: string } = {
      name: trimmedName,
      avatar,
      role: role.trim(),
      bio: bio.trim(),
      language,
      voice_type: voiceType,
      tts_speed: ttsSpeed,
      auto_speak: autoSpeak,
      vad_enabled: vadEnabled,
      theme,
      color_scheme: colorScheme,
      animations,
      compact_mode: compactMode,
      glassmorphism,
      ai_model: aiModel,
      ai_mode: aiMode,
      thinking_enabled: thinkingEnabled,
      notifications: {
        scheduler: notifScheduler,
        voice: notifVoice,
        sound_effects: notifSoundEffects,
        system_status: true,
      },
      privacy: {
        local_storage_only: localStorageOnly,
        telemetry_disabled: telemetryDisabled,
        save_conversations: saveConversations,
      },
    };

    if (geminiApiKey.trim()) {
      payload.gemini_api_key = geminiApiKey.trim();
    }

    const res = await backendService.updateAccount(payload);

    if (res.ok) {
      setSaveSuccess(true);
      if (geminiApiKey.trim()) setHasGeminiKey(true);
      onUserUpdated?.(trimmedName, avatar);
      setTimeout(() => setSaveSuccess(false), 4000);
    }
    setIsSaving(false);
  };

  const handleTestVoice = async () => {
    if (testingVoice) return;
    setTestingVoice(true);
    const testText =
      voiceType === "ayol"
        ? "Assalomu alaykum! Men Madinaman. Mikasa AI tizimida sizga har tomonlama yordam berishga tayyorman."
        : "Assalomu alaykum! Men Sardorman. Mikasa AI tizimida vazifalarni aniq va tezkor bajarishga tayyorman.";
    await backendService.speakText(testText);
    setTimeout(() => setTestingVoice(false), 2500);
  };

  const handleClearHistory = async () => {
    if (clearingHistory) return;
    setClearingHistory(true);
    try {
      await backendService.clearHistory();
      await backendService.clearChat();
      setClearSuccess(true);
      setTimeout(() => setClearSuccess(false), 3000);
    } catch {
      // ignore
    } finally {
      setClearingHistory(false);
    }
  };

  const effectiveInitials = (() => {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.trim().slice(0, 2).toUpperCase() || "U";
  })();

  const tabs: Array<{ id: TabType; label: string; icon: React.ComponentType<{ size?: number; color?: string }> }> = [
    { id: "profile", label: "Profil", icon: UserIcon },
    { id: "appearance", label: "Tashqi ko'rinish", icon: PaletteIcon },
    { id: "voice", label: "Ovoz", icon: VolumeIcon },
    { id: "ai", label: "AI Modeli", icon: CpuIcon },
    { id: "notifications", label: "Bildirishnomalar", icon: BellIcon },
    { id: "privacy", label: "Maxfiylik", icon: ShieldIcon },
    { id: "about", label: "Dastur haqida", icon: InfoIcon },
  ];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        background: "var(--bg-gradient, #0A0F1D)",
        color: "var(--text-primary, #F8FAFC)",
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
          borderBottom: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
          background: "rgba(10, 15, 29, 0.85)",
          backdropFilter: "blur(20px)",
          position: "sticky",
          top: 0,
          zIndex: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Avatar initials={effectiveInitials} size={42} avatarStyle={avatar} />
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
                  color: "var(--primary-glow, #10B981)",
                  fontWeight: 500,
                  border: "1px solid rgba(16, 185, 129, 0.25)",
                }}
              >
                v7.1.0
              </span>
            </div>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary, #94A3B8)" }}>
              Foydalanuvchi profili, ovoz, AI modeli va tizim parametrlari
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={() => handleSave()}
            disabled={isSaving}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "var(--primary-glow, #10B981)",
              color: "#052e16",
              border: "none",
              padding: "8px 18px",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 600,
              cursor: isSaving ? "default" : "pointer",
              transition: "all 0.15s ease",
              boxShadow: "0 2px 10px rgba(16, 185, 129, 0.3)",
            }}
          >
            <CheckIcon size={14} color="#052e16" />
            <span>{isSaving ? "Saqlanmoqda..." : "Saqlash"}</span>
          </button>

          <button
            onClick={onNavigateHome}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid var(--border-subtle, rgba(255,255,255,0.08))",
              color: "var(--text-secondary, #94A3B8)",
              padding: "8px 14px",
              borderRadius: 8,
              fontSize: 12,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--text-primary, #F8FAFC)";
              e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.2)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--text-secondary, #94A3B8)";
              e.currentTarget.style.borderColor = "var(--border-subtle, rgba(255,255,255,0.08))";
            }}
          >
            <HomeIcon size={14} />
            <span>Bosh sahifa</span>
          </button>
        </div>
      </div>

      {/* Main Content Area with Navigation Tabs */}
      <div
        style={{
          maxWidth: 960,
          width: "100%",
          margin: "0 auto",
          padding: "24px 28px 48px",
          display: "flex",
          flexDirection: "column",
          gap: 20,
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
              animation: "fadeIn 0.2s ease-out",
            }}
          >
            <SparklesIcon size={16} color="#34d399" />
            <span>Sozlamalar muvaffaqiyatli saqlandi va barcha xizmatlarga joriy etildi!</span>
          </div>
        )}

        {/* Tab Navigation Pill Bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "rgba(13, 19, 31, 0.8)",
            padding: "5px 6px",
            borderRadius: 12,
            border: "1px solid rgba(255, 255, 255, 0.06)",
            overflowX: "auto",
          }}
        >
          {tabs.map((tab) => {
            const IconComp = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "8px 14px",
                  borderRadius: 8,
                  border: "none",
                  background: isActive ? "rgba(16, 185, 129, 0.18)" : "transparent",
                  color: isActive ? "#34D399" : "var(--text-secondary, #94A3B8)",
                  fontSize: 12.5,
                  fontWeight: isActive ? 600 : 500,
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.color = "#FFFFFF";
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.color = "var(--text-secondary, #94A3B8)";
                }}
              >
                <IconComp size={15} color={isActive ? "#34D399" : "currentColor"} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "60px", color: "var(--text-secondary, #94A3B8)" }}>
            Sozlamalar yuklanmoqda...
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* TAB 1: PROFIL */}
            {activeTab === "profile" && (
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
                  borderRadius: 14,
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 20,
                }}
              >
                <div>
                  <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Foydalanuvchi Profili</h2>
                  <p style={{ margin: 0, fontSize: 12.5, color: "var(--text-secondary, #94A3B8)" }}>
                    Sizning ismingiz, avataringiz va shaxsiy parametrlaringiz
                  </p>
                </div>

                {/* Avatar Palette Selector */}
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                    Profil Avatari Rang Uslubi
                  </label>
                  <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
                    <Avatar initials={effectiveInitials} size={64} avatarStyle={avatar} />
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      {AVATAR_PALETTES.map((pal) => (
                        <div
                          key={pal.id}
                          onClick={() => setAvatar(pal.id)}
                          title={pal.name}
                          style={{
                            width: 32,
                            height: 32,
                            borderRadius: "50%",
                            backgroundColor: pal.color,
                            cursor: "pointer",
                            border: avatar === pal.id ? "3px solid #FFFFFF" : "2px solid rgba(255,255,255,0.15)",
                            boxShadow: avatar === pal.id ? `0 0 12px ${pal.color}` : "none",
                            transition: "all 0.15s ease",
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Username Input */}
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                    Ismingiz (Murojaat uchun)
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Masalan: Ustoz yoki Muhammadaziz"
                    style={{
                      background: "rgba(0, 0, 0, 0.25)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      borderRadius: 8,
                      padding: "10px 14px",
                      color: "var(--text-primary, #F8FAFC)",
                      fontSize: 14,
                      outline: "none",
                    }}
                    onFocus={(e) => (e.target.style.borderColor = "var(--primary-glow, #10B981)")}
                    onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
                  />
                  <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                    Mikasa suhbat va bildirishnomalarda sizga ushbu ism bilan murojaat qiladi
                  </span>
                </div>

                {/* Occupation / Role */}
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                    Kasb / Faoliyat yo'nalishi
                  </label>
                  <input
                    type="text"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    placeholder="Masalan: Dasturchi, Muhandis, Talaba..."
                    style={{
                      background: "rgba(0, 0, 0, 0.25)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      borderRadius: 8,
                      padding: "10px 14px",
                      color: "var(--text-primary, #F8FAFC)",
                      fontSize: 14,
                      outline: "none",
                    }}
                    onFocus={(e) => (e.target.style.borderColor = "var(--primary-glow, #10B981)")}
                    onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
                  />
                </div>

                {/* Bio / About Notes */}
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                    Qisqacha tavsif (AI xotirasi uchun)
                  </label>
                  <textarea
                    rows={2}
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    placeholder="O'zingiz haqingizda qisqacha ma'lumot..."
                    style={{
                      background: "rgba(0, 0, 0, 0.25)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      borderRadius: 8,
                      padding: "10px 14px",
                      color: "var(--text-primary, #F8FAFC)",
                      fontSize: 13.5,
                      outline: "none",
                      resize: "none",
                    }}
                    onFocus={(e) => (e.target.style.borderColor = "var(--primary-glow, #10B981)")}
                    onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
                  />
                </div>

                {/* Language Selection */}
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                    Asosiy muloqot tili
                  </label>
                  <div style={{ display: "flex", gap: 12 }}>
                    {[
                      { id: "uz", label: "O'zbekcha (Lotin)" },
                      { id: "ru", label: "Русский" },
                      { id: "en", label: "English" },
                    ].map((lang) => (
                      <div
                        key={lang.id}
                        onClick={() => setLanguage(lang.id)}
                        style={{
                          padding: "10px 16px",
                          borderRadius: 8,
                          background:
                            language === lang.id ? "rgba(16, 185, 129, 0.15)" : "rgba(255, 255, 255, 0.02)",
                          border: `1.5px solid ${
                            language === lang.id ? "var(--primary-glow, #10B981)" : "rgba(255, 255, 255, 0.08)"
                          }`,
                          cursor: "pointer",
                          fontSize: 13,
                          fontWeight: language === lang.id ? 600 : 400,
                          transition: "all 0.15s ease",
                        }}
                      >
                        {lang.label}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: TASHQI KO'RINISH (APPEARANCE) */}
            {activeTab === "appearance" && (
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
                  borderRadius: 14,
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 20,
                }}
              >
                <div>
                  <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Tashqi Ko'rinish va Mavzular</h2>
                  <p style={{ margin: 0, fontSize: 12.5, color: "var(--text-secondary, #94A3B8)" }}>
                    Quiet Intelligence dizayn tizimi, mavzu va vizual effektlar
                  </p>
                </div>

                {/* Theme Selector */}
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                    Ilova Mavzusi
                  </label>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                    {[
                      {
                        id: "dark",
                        title: "Quiet Dark",
                        desc: "Klassik 80% to'q fon (#0E1422) va zumrad aksenti",
                      },
                      {
                        id: "oled",
                        title: "OLED Qora",
                        desc: "Mutlaq qora (#000000), kontrast va energiya tejovchi",
                      },
                      {
                        id: "cyber",
                        title: "Midnight Cyber",
                        desc: "Chuqur to'q ko'k kiber fon va yorqin konturlar",
                      },
                    ].map((thm) => (
                      <div
                        key={thm.id}
                        onClick={() => setTheme(thm.id)}
                        style={{
                          background:
                            theme === thm.id ? "rgba(16, 185, 129, 0.12)" : "rgba(255, 255, 255, 0.02)",
                          border: `1.5px solid ${
                            theme === thm.id ? "var(--primary-glow, #10B981)" : "rgba(255, 255, 255, 0.08)"
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
                          <strong style={{ fontSize: 13.5 }}>{thm.title}</strong>
                          {theme === thm.id && <CheckIcon size={14} color="#10B981" />}
                        </div>
                        <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                          {thm.desc}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Toggles */}
                <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 6 }}>
                  {/* Smooth Animations Toggle */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 16px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Silliq Animatsiyalar (Transitions)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Mikasa interfeysi animatsiyalarini faollashtirish
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={animations}
                      onChange={(e) => setAnimations(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>

                  {/* Glassmorphism Toggle */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 16px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Shaffof Shisha Effekti (Glassmorphism Blur)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Yon panel va yuqori sarlavhalarda nozik blur effektini ko'rsatish
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={glassmorphism}
                      onChange={(e) => setGlassmorphism(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>

                  {/* Compact Sidebar Mode */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 16px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Ixcham Yon Panel (Compact Mode)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Yon panelni sukut bo'yicha yig'ilgan holda ochish
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={compactMode}
                      onChange={(e) => setCompactMode(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: OVOZ SOZLAMALARI (VOICE) */}
            {activeTab === "voice" && (
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
                  borderRadius: 14,
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 20,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div>
                    <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Mikasa Nutqi va Ovoz Dvigateli</h2>
                    <p style={{ margin: 0, fontSize: 12.5, color: "var(--text-secondary, #94A3B8)" }}>
                      Tabiiy o'zbek tili neyron modeli, tezlik va ovozli sinov
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleTestVoice}
                    disabled={testingVoice}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      background: testingVoice ? "rgba(16, 185, 129, 0.3)" : "rgba(16, 185, 129, 0.15)",
                      border: "1px solid rgba(16, 185, 129, 0.35)",
                      color: "#34D399",
                      padding: "8px 16px",
                      borderRadius: 8,
                      fontSize: 12.5,
                      fontWeight: 600,
                      cursor: testingVoice ? "default" : "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <PlayIcon size={13} color="#34D399" />
                    <span>{testingVoice ? "Ovoz yangramoqda..." : "Ovozni sinash"}</span>
                  </button>
                </div>

                {/* Voice Selection Cards */}
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
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
                          voiceType === "ayol" ? "var(--primary-glow, #10B981)" : "rgba(255, 255, 255, 0.08)"
                        }`,
                        borderRadius: 10,
                        padding: "16px 18px",
                        cursor: "pointer",
                        display: "flex",
                        flexDirection: "column",
                        gap: 4,
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <strong style={{ fontSize: 14 }}>Madina (Ayol ovozi)</strong>
                        {voiceType === "ayol" && <CheckIcon size={14} color="#10B981" />}
                      </div>
                      <span style={{ fontSize: 12, color: "var(--text-muted, #64748B)" }}>
                        uz-UZ-MadinaNeural · Yumshoq, muloyim va ravon intonatsiya
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
                          voiceType === "erkak" ? "var(--primary-glow, #10B981)" : "rgba(255, 255, 255, 0.08)"
                        }`,
                        borderRadius: 10,
                        padding: "16px 18px",
                        cursor: "pointer",
                        display: "flex",
                        flexDirection: "column",
                        gap: 4,
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <strong style={{ fontSize: 14 }}>Sardor (Erkak ovozi)</strong>
                        {voiceType === "erkak" && <CheckIcon size={14} color="#10B981" />}
                      </div>
                      <span style={{ fontSize: 12, color: "var(--text-muted, #64748B)" }}>
                        uz-UZ-SardorNeural · Jiddiy, ishonchli va aniq tembr
                      </span>
                    </div>
                  </div>
                </div>

                {/* TTS Speed Slider */}
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 4 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                      Nutq Tezligi (TTS Speed)
                    </label>
                    <span style={{ fontSize: 13.5, fontWeight: 600, color: "var(--primary-glow, #10B981)" }}>
                      {ttsSpeed.toFixed(1)}x
                    </span>
                  </div>
                  <input
                    type="range"
                    min={1.0}
                    max={2.5}
                    step={0.1}
                    value={ttsSpeed}
                    onChange={(e) => setTtsSpeed(parseFloat(e.target.value))}
                    style={{ width: "100%", accentColor: "var(--primary-glow, #10B981)", cursor: "pointer" }}
                  />
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-muted, #64748B)" }}>
                    <span>1.0x (Sokin)</span>
                    <span>1.5x (Normal)</span>
                    <span>2.0x (Tezkor - Standart)</span>
                    <span>2.5x (Maksimal)</span>
                  </div>
                </div>

                {/* Audio Features */}
                <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 8 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 16px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>AI Javoblarini Avtomatik O'qish (Auto-Speak)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Suhbat va ovozli muloqot rejimida javoblarni ovoz chiqarib o'qish
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={autoSpeak}
                      onChange={(e) => setAutoSpeak(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "12px 16px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Ovoz Sezgirligi (VAD - Voice Activity Detection)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Faqat inson nutqi yangraganda mikrofonni faollashtirish va jimlikda avtomatik to'xtash
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={vadEnabled}
                      onChange={(e) => setVadEnabled(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: AI SOZLAMALARI (AI ENGINE) */}
            {activeTab === "ai" && (
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
                  borderRadius: 14,
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 20,
                }}
              >
                <div>
                  <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Sun'iy Intellekt Dvigateli</h2>
                  <p style={{ margin: 0, fontSize: 12.5, color: "var(--text-secondary, #94A3B8)" }}>
                    Google Gemini, OpenRouter va mahalliy buyruqlar yadrosi
                  </p>
                </div>

                {/* Model Selector Cards */}
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                    Faol AI Modeli
                  </label>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 10 }}>
                    {[
                      {
                        id: "gemini",
                        name: "Google Gemini 1.5 (Flash / Pro)",
                        badge: "Tavsiya etiladi",
                        badgeColor: "#10B981",
                        desc: "Katta kontekst, chuqur fikrlash (Thinking mode) va mukammal o'zbek tili mantiqi.",
                      },
                      {
                        id: "openrouter",
                        name: "OpenRouter (GPT-4o / Claude 3.5)",
                        badge: "Universal",
                        badgeColor: "#3B82F6",
                        desc: "Muqobil bulutli yirik til modellari tarmog'i.",
                      },
                      {
                        id: "local",
                        name: "Mikasa Mahalliy Qoidalar (Local Dispatcher)",
                        badge: "Oflayn",
                        badgeColor: "#F59E0B",
                        desc: "Internet talab qilinmaydi: Windows ilovalarini ochish, ovozni boshqarish, taymerlar.",
                      },
                    ].map((mod) => (
                      <div
                        key={mod.id}
                        onClick={() => setAiModel(mod.id)}
                        style={{
                          background:
                            aiModel === mod.id ? "rgba(16, 185, 129, 0.12)" : "rgba(255, 255, 255, 0.02)",
                          border: `1.5px solid ${
                            aiModel === mod.id ? "var(--primary-glow, #10B981)" : "rgba(255, 255, 255, 0.08)"
                          }`,
                          borderRadius: 10,
                          padding: "14px 18px",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          transition: "all 0.15s ease",
                        }}
                      >
                        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <strong style={{ fontSize: 14 }}>{mod.name}</strong>
                            <span
                              style={{
                                fontSize: 10.5,
                                padding: "1px 7px",
                                borderRadius: 8,
                                background: `${mod.badgeColor}20`,
                                color: mod.badgeColor,
                                fontWeight: 600,
                              }}
                            >
                              {mod.badge}
                            </span>
                          </div>
                          <span style={{ fontSize: 12, color: "var(--text-muted, #64748B)" }}>
                            {mod.desc}
                          </span>
                        </div>
                        {aiModel === mod.id && <CheckIcon size={16} color="#10B981" />}
                      </div>
                    ))}
                  </div>
                </div>

                {/* API Key Configuration */}
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                      Gemini API Kaliti (GEMINI_API_KEY)
                    </label>
                    <span
                      style={{
                        fontSize: 11,
                        color: hasGeminiKey ? "#34D399" : "#F59E0B",
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                      }}
                    >
                      <KeyIcon size={12} color="currentColor" />
                      {hasGeminiKey ? "Kalit o'rnatilgan (Faol)" : "Kalit kiritilmagan"}
                    </span>
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type={showApiKey ? "text" : "password"}
                      value={geminiApiKey}
                      onChange={(e) => setGeminiApiKey(e.target.value)}
                      placeholder={hasGeminiKey ? "••••••••••••••••••••••••••••••••" : "AIzaSy..."}
                      style={{
                        flex: 1,
                        background: "rgba(0, 0, 0, 0.25)",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        borderRadius: 8,
                        padding: "10px 14px",
                        color: "var(--text-primary, #F8FAFC)",
                        fontSize: 13.5,
                        fontFamily: "monospace",
                        outline: "none",
                      }}
                      onFocus={(e) => (e.target.style.borderColor = "var(--primary-glow, #10B981)")}
                      onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      style={{
                        padding: "0 14px",
                        background: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        borderRadius: 8,
                        color: "var(--text-secondary, #94A3B8)",
                        fontSize: 12,
                        cursor: "pointer",
                      }}
                    >
                      {showApiKey ? "Yashirish" : "Ko'rsatish"}
                    </button>
                  </div>
                  <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                    Kalit xavfsiz holda faqat ushbu kompyuterda lokal saqlanadi
                  </span>
                </div>

                {/* Thinking AI Toggle */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "12px 16px",
                    background: "rgba(0, 0, 0, 0.2)",
                    borderRadius: 10,
                  }}
                >
                  <div>
                    <div style={{ fontSize: 13.5, fontWeight: 500 }}>Fikrlovchi AI (Gemini Thinking Mode)</div>
                    <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                      Murakkab savollarga javob berishdan oldin ichki mantiqiy fikrlash zanjirini yuritish
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={thinkingEnabled}
                    onChange={(e) => setThinkingEnabled(e.target.checked)}
                    style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                  />
                </div>

                {/* Cognitive Mode */}
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <label style={{ fontSize: 13, color: "var(--text-secondary, #94A3B8)" }}>
                    Kognitiv Xarakter va Javob Uslubi
                  </label>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                    {[
                      { id: "precise", title: "Aniq va Qat'iy", desc: "Tizim va kod buyruqlari" },
                      { id: "balanced", title: "Muvozanatli", desc: "Kundalik savol-javob" },
                      { id: "creative", title: "Ijodiy", desc: "G'oyalar va erkin suhbat" },
                    ].map((m) => (
                      <div
                        key={m.id}
                        onClick={() => setAiMode(m.id)}
                        style={{
                          background:
                            aiMode === m.id ? "rgba(16, 185, 129, 0.12)" : "rgba(255, 255, 255, 0.02)",
                          border: `1.5px solid ${
                            aiMode === m.id ? "var(--primary-glow, #10B981)" : "rgba(255, 255, 255, 0.08)"
                          }`,
                          borderRadius: 8,
                          padding: "12px 14px",
                          cursor: "pointer",
                          display: "flex",
                          flexDirection: "column",
                          gap: 3,
                          transition: "all 0.15s ease",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                          <strong style={{ fontSize: 13 }}>{m.title}</strong>
                          {aiMode === m.id && <CheckIcon size={13} color="#10B981" />}
                        </div>
                        <span style={{ fontSize: 11, color: "var(--text-muted, #64748B)" }}>
                          {m.desc}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 5: BILDIRISHNOMALAR (NOTIFICATIONS) */}
            {activeTab === "notifications" && (
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
                  borderRadius: 14,
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 16,
                }}
              >
                <div>
                  <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Tizim Bildirishnomalari</h2>
                  <p style={{ margin: 0, fontSize: 12.5, color: "var(--text-secondary, #94A3B8)" }}>
                    Rejalashtiruvchi signallari va ovozli bildirishnomalar boshqaruvi
                  </p>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 18px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Rejalashtiruvchi Eslatmalari (Scheduler Alarms)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Vaqti kelgan vazifalar bo'yicha ekranda jonli ogohlantirish bannerini ko'rsatish
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={notifScheduler}
                      onChange={(e) => setNotifScheduler(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 18px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Ovozli Eslatmalar (Spoken Reminders)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Eslatma vaqti kelganda Mikasa ovozi bilan matnni o'qib eshittirish
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={notifVoice}
                      onChange={(e) => setNotifVoice(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 18px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Interfeys Tovushlari (UI Sound Effects)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Mikrofon ochilishi, vazifa bajarilishi va xatolik signallari
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={notifSoundEffects}
                      onChange={(e) => setNotifSoundEffects(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* TAB 6: MAXFIYLIK VA XAVFSIZLIK (PRIVACY) */}
            {activeTab === "privacy" && (
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
                  borderRadius: 14,
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 20,
                }}
              >
                <div>
                  <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Maxfiylik va Ma'lumotlar Xavfsizligi</h2>
                  <p style={{ margin: 0, fontSize: 12.5, color: "var(--text-secondary, #94A3B8)" }}>
                    100% lokal xotira, telemetriya bloklanishi va ma'lumotlarni tozalash
                  </p>
                </div>

                <div
                  style={{
                    padding: "14px 18px",
                    background: "rgba(16, 185, 129, 0.08)",
                    border: "1px solid rgba(16, 185, 129, 0.2)",
                    borderRadius: 10,
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 12,
                  }}
                >
                  <ShieldIcon size={20} color="#10B981" />
                  <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                    <strong style={{ fontSize: 13.5, color: "#34D399" }}>
                      Mahalliy Xavfsizlik Kafolati
                    </strong>
                    <span style={{ fontSize: 12, color: "var(--text-secondary, #94A3B8)", lineHeight: 1.5 }}>
                      Mikasa sizning xotirangiz, eslatmalaringiz, suhbatlaringiz va tizim buyruqlaringizni
                      faqat kompyuteringizning mahalliy <code>data/</code> katalogida saqlaydi. Tashqi serverlarga
                      hech qanday shaxsiy ma'lumot jo'natilmaydi.
                    </span>
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 18px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Faqat Mahalliy Xotira (Local Storage Only)</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Barcha fayllar lokal saqlanadi
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={localStorageOnly}
                      onChange={(e) => setLocalStorageOnly(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "14px 18px",
                      background: "rgba(0, 0, 0, 0.2)",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 500 }}>Telemetriya va Kuzatuvni O'chirish</div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Hech qanday foydalanish statistikasi yoki xatolik hisobotlari tashqariga chiqmaydi
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={telemetryDisabled}
                      onChange={(e) => setTelemetryDisabled(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#10B981", cursor: "pointer" }}
                    />
                  </div>
                </div>

                {/* Actions: Clear History */}
                <div style={{ borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 600, color: "#F87171" }}>
                        Suhbatlar Tarixini Tozalash
                      </div>
                      <div style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>
                        Saqlangan barcha AI suhbatlari va kontekst tarixini qaytarib bo'lmaydigan tarzda o'chiradi
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={handleClearHistory}
                      disabled={clearingHistory}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        background: "rgba(239, 68, 68, 0.15)",
                        border: "1px solid rgba(239, 68, 68, 0.3)",
                        color: "#F87171",
                        padding: "8px 16px",
                        borderRadius: 8,
                        fontSize: 12.5,
                        fontWeight: 600,
                        cursor: clearingHistory ? "default" : "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <TrashIcon size={14} color="#F87171" />
                      <span>{clearingHistory ? "Tozalanmoqda..." : "Tarixni tozalash"}</span>
                    </button>
                  </div>

                  {clearSuccess && (
                    <div style={{ marginTop: 10, fontSize: 12, color: "#34D399" }}>
                      Suhbatlar tarixi muvaffaqiyatli tozalandi.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 7: DASTUR HAQIDA (ABOUT) */}
            {activeTab === "about" && (
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle, rgba(255,255,255,0.07))",
                  borderRadius: 14,
                  padding: "24px 28px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 20,
                }}
              >
                <div>
                  <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Dastur Haqida</h2>
                  <p style={{ margin: 0, fontSize: 12.5, color: "var(--text-secondary, #94A3B8)" }}>
                    Mikasa AI 7.1.0 tizim arxitekturasi va texnik xususiyatlari
                  </p>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 14, borderRadius: 10 }}>
                    <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>Ilova Nomi</span>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>{appInfo.name}</div>
                  </div>

                  <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 14, borderRadius: 10 }}>
                    <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>Versiya</span>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, color: "#10B981" }}>
                      {appInfo.version} ({appInfo.codename})
                    </div>
                  </div>

                  <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 14, borderRadius: 10 }}>
                    <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>Desktop Dvigateli</span>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>{appInfo.engine}</div>
                  </div>

                  <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 14, borderRadius: 10 }}>
                    <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>Backend API Porti</span>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>127.0.0.1:18420 (Asinxron)</div>
                  </div>

                  <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 14, borderRadius: 10 }}>
                    <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>Tizim Arxitekturasi</span>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>{appInfo.architecture}</div>
                  </div>

                  <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 14, borderRadius: 10 }}>
                    <span style={{ fontSize: 11.5, color: "var(--text-muted, #64748B)" }}>Ishlab chiquvchi</span>
                    <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>{appInfo.developer}</div>
                  </div>
                </div>

                <div
                  style={{
                    padding: "14px 18px",
                    background: "rgba(255, 255, 255, 0.02)",
                    borderRadius: 10,
                    border: "1px solid rgba(255, 255, 255, 0.06)",
                    fontSize: 12,
                    color: "var(--text-muted, #64748B)",
                    lineHeight: 1.6,
                  }}
                >
                  Mikasa AI — bu aqlli ovozli yordamchi va kompyuter boshqaruv tizimi bo'lib,
                  Quiet Intelligence konsepsiyasi asosida ishlab chiqilgan.
                  Har qanday savol va takliflar uchun tizim mualliflariga murojaat qilishingiz mumkin.
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AccountPage;
