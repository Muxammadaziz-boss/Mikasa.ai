import React, { useState, useEffect } from "react";
import { WindowControls } from "../components/WindowControls";
import { Avatar } from "../components/Avatar";
import { backendService, BackendStatus } from "../services/backendService";
import {
  ChatIcon,
  MemoryIcon,
  SchedulerIcon,
  SearchIcon,
} from "../components/icons/Icons";

interface AppShellProps {
  currentPath: string;
  userName?: string;
  userAvatar?: string;
  userAvatarUrl?: string;
  onNavigate: (path: string, initialPrompt?: string) => void;
  onOpenCommandPalette?: () => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentPath,
  userName = "Muxammadaziz",
  userAvatar,
  userAvatarUrl,
  onNavigate,
  onOpenCommandPalette,
  children,
}) => {
  const [backendState, setBackendState] = useState<"online" | "offline" | "connecting">("connecting");
  const [themeMode, setThemeMode] = useState<"dark" | "light">("dark");
  const [language, setLanguage] = useState<"UZ" | "RU" | "EN">("UZ");

  useEffect(() => {
    const unsub = backendService.onStatusChange((status: BackendStatus) => {
      setBackendState(status.status);
    });
    return () => unsub();
  }, []);

  const isHome = currentPath === "/";

  const effectiveInitials = (() => {
    const parts = (userName || "M").trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return (userName || "M").trim().slice(0, 2).toUpperCase();
  })();

  const currentAvatarStyle = userAvatar || "emerald";

  return (
    <div
      className="mikasa-app-shell"
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100vw",
        height: "100vh",
        backgroundColor: "var(--bg-darkest)",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Cinematic Abstract Wallpaper Layer */}
      <div className="cinematic-bg" />

      {/* Subtle Atmospheric Vignette Overlay */}
      <div className="cinematic-vignette" />

      {/* ═══ UNIFIED GLASS TOP NAVIGATION — IMAGE 4 STYLE ═══ */}
      <header
        data-tauri-drag-region
        className="mikasa-glass-topnav"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "var(--topnav-height, 56px)",
          padding: "0 20px",
          background: "rgba(8, 14, 28, 0.55)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          zIndex: 50,
          flexShrink: 0,
          position: "relative",
          userSelect: "none",
        }}
      >
        {/* ── LEFT: Stylized Logo + MIKASA AI ── */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexShrink: 0 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              cursor: "pointer",
            }}
            onClick={() => onNavigate("/")}
          >
            {/* Glowing Gradient M Logo Icon */}
            <div
              style={{
                width: "30px",
                height: "30px",
                borderRadius: "9px",
                background: "linear-gradient(135deg, #6366F1 0%, #A855F7 50%, #EC4899 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 16px rgba(168, 85, 247, 0.45)",
              }}
            >
              <span
                style={{
                  fontFamily: "system-ui, -apple-system, sans-serif",
                  fontSize: "17px",
                  fontWeight: 900,
                  color: "#FFFFFF",
                  lineHeight: 1,
                }}
              >
                M
              </span>
            </div>

            <span
              style={{
                fontFamily: "system-ui, -apple-system, sans-serif",
                fontSize: "16px",
                fontWeight: 800,
                letterSpacing: "0.07em",
                color: "#FFFFFF",
              }}
            >
              MIKASA <span style={{ color: "#818CF8" }}>AI</span>
            </span>

            {/* Online Status Pill */}
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                padding: "2px 7px",
                borderRadius: "12px",
                backgroundColor: "rgba(255, 255, 255, 0.04)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                fontSize: "10px",
                color: "#94A3B8",
                marginLeft: "4px",
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor:
                    backendState === "online" ? "#10B981"
                      : backendState === "connecting" ? "#F59E0B"
                      : "#EF4444",
                  boxShadow:
                    backendState === "online" ? "0 0 8px rgba(16, 185, 129, 0.8)"
                      : backendState === "connecting" ? "0 0 8px rgba(245, 158, 11, 0.8)"
                      : "0 0 8px rgba(239, 68, 68, 0.8)",
                }}
              />
              <span>
                {backendState === "online" ? "Online"
                  : backendState === "connecting" ? "Ulanmoqda..."
                  : "Offline"}
              </span>
            </div>
          </div>
        </div>

        {/* ── CENTER: Navigation Tabs (Image 4 Style) ── */}
        <nav
          className="mikasa-topnav-center"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "4px",
            flex: "0 1 auto",
            margin: "0 8px",
            minWidth: 0,
            overflowX: "auto",
            scrollbarWidth: "none",
          }}
        >
          {/* Bosh sahifa tab */}
          <button
            onClick={() => onNavigate("/")}
            title="Bosh sahifa"
            style={{
              padding: "5px 13px",
              borderRadius: "20px",
              backgroundColor: isHome ? "rgba(30, 58, 138, 0.45)" : "transparent",
              border: isHome ? "1px solid rgba(96, 165, 250, 0.4)" : "1px solid transparent",
              boxShadow: isHome ? "0 0 16px rgba(59, 130, 246, 0.3)" : "none",
              color: isHome ? "#93C5FD" : "#94A3B8",
              fontSize: "12.5px",
              fontWeight: isHome ? 600 : 500,
              cursor: "pointer",
              whiteSpace: "nowrap",
              flexShrink: 0,
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              if (!isHome) {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.05)";
                e.currentTarget.style.color = "#E2E8F0";
              }
            }}
            onMouseLeave={(e) => {
              if (!isHome) {
                e.currentTarget.style.backgroundColor = "transparent";
                e.currentTarget.style.color = "#94A3B8";
              }
            }}
          >
            Bosh sahifa
          </button>

          {/* Suxbatlashish */}
          <button
            onClick={() => onNavigate("/chat")}
            title="Suhbatlashish"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "5px 12px",
              borderRadius: "20px",
              backgroundColor: currentPath === "/chat" ? "rgba(30, 58, 138, 0.45)" : "transparent",
              border: currentPath === "/chat" ? "1px solid rgba(96, 165, 250, 0.4)" : "1px solid transparent",
              boxShadow: currentPath === "/chat" ? "0 0 16px rgba(59, 130, 246, 0.3)" : "none",
              color: currentPath === "/chat" ? "#93C5FD" : "#94A3B8",
              fontSize: "12.5px",
              fontWeight: currentPath === "/chat" ? 600 : 500,
              cursor: "pointer",
              whiteSpace: "nowrap",
              flexShrink: 0,
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              if (currentPath !== "/chat") {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.05)";
                e.currentTarget.style.color = "#E2E8F0";
              }
            }}
            onMouseLeave={(e) => {
              if (currentPath !== "/chat") {
                e.currentTarget.style.backgroundColor = "transparent";
                e.currentTarget.style.color = "#94A3B8";
              }
            }}
          >
            <ChatIcon size={13} color="currentColor" />
            <span>Suxbatlashish</span>
          </button>

          {/* Xotira */}
          <button
            onClick={() => onNavigate("/memory")}
            title="Xotira"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "5px 12px",
              borderRadius: "20px",
              backgroundColor: currentPath === "/memory" ? "rgba(30, 58, 138, 0.45)" : "transparent",
              border: currentPath === "/memory" ? "1px solid rgba(96, 165, 250, 0.4)" : "1px solid transparent",
              boxShadow: currentPath === "/memory" ? "0 0 16px rgba(59, 130, 246, 0.3)" : "none",
              color: currentPath === "/memory" ? "#93C5FD" : "#94A3B8",
              fontSize: "12.5px",
              fontWeight: currentPath === "/memory" ? 600 : 500,
              cursor: "pointer",
              whiteSpace: "nowrap",
              flexShrink: 0,
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              if (currentPath !== "/memory") {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.05)";
                e.currentTarget.style.color = "#E2E8F0";
              }
            }}
            onMouseLeave={(e) => {
              if (currentPath !== "/memory") {
                e.currentTarget.style.backgroundColor = "transparent";
                e.currentTarget.style.color = "#94A3B8";
              }
            }}
          >
            <MemoryIcon size={13} color="currentColor" />
            <span>Xotira</span>
          </button>

          {/* Rejalashtirish */}
          <button
            onClick={() => onNavigate("/scheduler")}
            title="Rejalashtirish"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "5px 12px",
              borderRadius: "20px",
              backgroundColor: currentPath === "/scheduler" ? "rgba(30, 58, 138, 0.45)" : "transparent",
              border: currentPath === "/scheduler" ? "1px solid rgba(96, 165, 250, 0.4)" : "1px solid transparent",
              boxShadow: currentPath === "/scheduler" ? "0 0 16px rgba(59, 130, 246, 0.3)" : "none",
              color: currentPath === "/scheduler" ? "#93C5FD" : "#94A3B8",
              fontSize: "12.5px",
              fontWeight: currentPath === "/scheduler" ? 600 : 500,
              cursor: "pointer",
              whiteSpace: "nowrap",
              flexShrink: 0,
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              if (currentPath !== "/scheduler") {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.05)";
                e.currentTarget.style.color = "#E2E8F0";
              }
            }}
            onMouseLeave={(e) => {
              if (currentPath !== "/scheduler") {
                e.currentTarget.style.backgroundColor = "transparent";
                e.currentTarget.style.color = "#94A3B8";
              }
            }}
          >
            <SchedulerIcon size={13} color="currentColor" />
            <span>Rejalashtirish</span>
          </button>

          {/* Search shortcut button */}
          {onOpenCommandPalette && (
            <button
              onClick={onOpenCommandPalette}
              title="Qidiruv (Ctrl+K)"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                backgroundColor: "transparent",
                border: "1px solid transparent",
                color: "#64748B",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)";
                e.currentTarget.style.color = "#E2E8F0";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "transparent";
                e.currentTarget.style.color = "#64748B";
              }}
            >
              <SearchIcon size={14} color="currentColor" />
            </button>
          )}
        </nav>

        {/* ── RIGHT: Theme + Language + Notification + Profile (NO MIC ICON!) ── */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0, justifyContent: "flex-end" }}>
          {/* Theme Mode Toggle (Moon icon in Image 4) */}
          <button
            onClick={() => setThemeMode((m) => (m === "dark" ? "light" : "dark"))}
            title={themeMode === "dark" ? "Tungi rejim faol" : "Kunduzgi rejim"}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "transparent",
              color: "#94A3B8",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#E2E8F0"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#94A3B8"; }}
          >
            {/* Moon Icon */}
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          </button>

          {/* Language Selector (UZ ⌄ in Image 4) */}
          <div
            onClick={() => setLanguage((l) => (l === "UZ" ? "RU" : l === "RU" ? "EN" : "UZ"))}
            title="Tilni o'zgartirish"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "4px 8px",
              borderRadius: "8px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              color: "#CBD5E1",
              fontSize: "11.5px",
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)"; }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.04)"; }}
          >
            <span>{language}</span>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </div>

          {/* Notification Bell with Badge (Image 4) */}
          <button
            title="Bildirishnomalar (1 ta yangi xabar)"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: "transparent",
              color: "#94A3B8",
              cursor: "pointer",
              position: "relative",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#E2E8F0"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#94A3B8"; }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            {/* Red badge with dot */}
            <span
              style={{
                position: "absolute",
                top: "5px",
                right: "6px",
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                backgroundColor: "#EF4444",
                boxShadow: "0 0 6px #EF4444",
              }}
            />
          </button>

          {/* User Profile Pill (No mic next to it!) */}
          <div
            onClick={() => onNavigate("/account")}
            title={`${userName} — Hisob sozlamalari`}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "7px",
              padding: "3px 8px 3px 4px",
              maxWidth: "145px",
              borderRadius: "24px",
              backgroundColor: currentPath === "/account" ? "rgba(56, 189, 248, 0.15)" : "rgba(255, 255, 255, 0.05)",
              border: currentPath === "/account"
                ? "1px solid rgba(56, 189, 248, 0.35)"
                : "1px solid rgba(255, 255, 255, 0.08)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.09)";
              e.currentTarget.style.borderColor = "rgba(168, 85, 247, 0.35)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = currentPath === "/account" ? "rgba(56, 189, 248, 0.15)" : "rgba(255, 255, 255, 0.05)";
              e.currentTarget.style.borderColor = currentPath === "/account" ? "rgba(56, 189, 248, 0.35)" : "rgba(255, 255, 255, 0.08)";
            }}
          >
            <Avatar initials={effectiveInitials} size={28} avatarStyle={currentAvatarStyle} avatarUrl={userAvatarUrl} />
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", lineHeight: 1.15, minWidth: 0, overflow: "hidden" }}>
              <span
                style={{
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#FFFFFF",
                  maxWidth: "80px",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  display: "block",
                }}
              >
                {userName}
              </span>
              <span style={{ fontSize: "10px", color: "#818CF8", fontWeight: 600 }}>
                Pro
              </span>
            </div>
          </div>

          {/* Window Controls */}
          <WindowControls />
        </div>
      </header>

      {/* ═══ MAIN CONTENT AREA — full width ═══ */}
      <main
        style={{
          display: "flex",
          flex: 1,
          width: "100%",
          height: "calc(100vh - var(--topnav-height, 56px))",
          overflow: "hidden",
          position: "relative",
          zIndex: 5,
        }}
      >
        {children}
      </main>
    </div>
  );
};
