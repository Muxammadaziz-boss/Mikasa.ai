import React, { useState, useEffect } from "react";
import { WindowControls } from "../components/WindowControls";
import { Avatar } from "../components/Avatar";
import { backendService, BackendStatus } from "../services/backendService";
import {
  ChatIcon,
  MemoryIcon,
  SchedulerIcon,
  CommandsIcon,
  PluginsIcon,
  MicIcon,
  SearchIcon,
} from "../components/icons/Icons";

interface AppShellProps {
  currentPath: string;
  userName?: string;
  userAvatar?: string;
  onNavigate: (path: string, initialPrompt?: string) => void;
  onOpenCommandPalette?: () => void;
  children: React.ReactNode;
}

interface NavTab {
  id: string;
  path: string;
  label: string;
  icon: React.ComponentType<{ size?: number; color?: string }>;
  accent: string;
  accentBg: string;
}

const NAV_TABS: NavTab[] = [
  { id: "chat", path: "/chat", label: "Suhbatlashish", icon: ChatIcon, accent: "#38BDF8", accentBg: "rgba(56, 189, 248, 0.15)" },
  { id: "memory", path: "/memory", label: "Xotira", icon: MemoryIcon, accent: "#C084FC", accentBg: "rgba(168, 85, 247, 0.15)" },
  { id: "scheduler", path: "/scheduler", label: "Rejalashtirish", icon: SchedulerIcon, accent: "#34D399", accentBg: "rgba(16, 185, 129, 0.15)" },
  { id: "commands", path: "/commands", label: "Buyruqlar", icon: CommandsIcon, accent: "#FBBF24", accentBg: "rgba(245, 158, 11, 0.15)" },
  { id: "plugins", path: "/plugins", label: "Plaginlar", icon: PluginsIcon, accent: "#F472B6", accentBg: "rgba(236, 72, 153, 0.15)" },
];

export const AppShell: React.FC<AppShellProps> = ({
  currentPath,
  userName = "Ustoz",
  userAvatar,
  onNavigate,
  onOpenCommandPalette,
  children,
}) => {
  const [backendState, setBackendState] = useState<"online" | "offline" | "connecting">("connecting");

  useEffect(() => {
    const unsub = backendService.onStatusChange((status: BackendStatus) => {
      setBackendState(status.status);
    });
    return () => unsub();
  }, []);

  const isHome = currentPath === "/";

  const effectiveInitials = (() => {
    const parts = (userName || "U").trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return (userName || "U").trim().slice(0, 2).toUpperCase();
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

      {/* ═══ UNIFIED GLASS TOP NAVIGATION ═══ */}
      <header
        data-tauri-drag-region
        className="mikasa-glass-topnav"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "var(--topnav-height)",
          padding: "0 16px",
          background: "rgba(6, 10, 20, 0.6)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.07)",
          zIndex: 50,
          flexShrink: 0,
          position: "relative",
          userSelect: "none",
        }}
      >
        {/* ── LEFT: Brand + Status ── */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", minWidth: "220px" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              cursor: "pointer",
            }}
            onClick={() => onNavigate("/")}
          >
            <span
              style={{
                fontFamily: "system-ui, -apple-system, sans-serif",
                fontSize: "16px",
                fontWeight: 800,
                letterSpacing: "0.08em",
                background: "linear-gradient(135deg, #FFFFFF 0%, #93C5FD 50%, #38BDF8 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              MIKASA AI
            </span>
            <span
              style={{
                fontSize: "9px",
                fontWeight: 600,
                padding: "1px 5px",
                borderRadius: "5px",
                backgroundColor: "rgba(56, 189, 248, 0.12)",
                color: "#38BDF8",
                border: "1px solid rgba(56, 189, 248, 0.25)",
              }}
            >
              v7.2
            </span>
          </div>

          {/* Online Status */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "5px",
              padding: "2px 8px",
              borderRadius: "16px",
              backgroundColor: "rgba(255, 255, 255, 0.03)",
              border: "1px solid rgba(255, 255, 255, 0.05)",
              fontSize: "10.5px",
              color: "#94A3B8",
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
                  backendState === "online" ? "0 0 8px rgba(16, 185, 129, 0.7)"
                    : backendState === "connecting" ? "0 0 8px rgba(245, 158, 11, 0.7)"
                    : "0 0 8px rgba(239, 68, 68, 0.7)",
              }}
            />
            <span>
              {backendState === "online" ? "Online"
                : backendState === "connecting" ? "Ulanmoqda..."
                : "Offline"}
            </span>
          </div>
        </div>

        {/* ── CENTER: Navigation Tabs ── */}
        <nav
          className="mikasa-topnav-center"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            position: "absolute",
            left: "50%",
            transform: "translateX(-50%)",
          }}
        >
          {/* Home button */}
          <button
            onClick={() => onNavigate("/")}
            title="Bosh sahifa"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              padding: "6px 12px",
              borderRadius: "10px",
              backgroundColor: isHome ? "rgba(56, 189, 248, 0.15)" : "transparent",
              border: isHome ? "1px solid rgba(56, 189, 248, 0.3)" : "1px solid transparent",
              color: isHome ? "#38BDF8" : "#94A3B8",
              fontSize: "12px",
              fontWeight: isHome ? 600 : 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              if (!isHome) {
                e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)";
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
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </button>

          {NAV_TABS.map((tab) => {
            const isActive = currentPath === tab.path;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => onNavigate(tab.path)}
                title={tab.label}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "10px",
                  backgroundColor: isActive ? tab.accentBg : "transparent",
                  border: isActive
                    ? `1px solid ${tab.accent}44`
                    : "1px solid transparent",
                  color: isActive ? tab.accent : "#94A3B8",
                  fontSize: "12px",
                  fontWeight: isActive ? 600 : 500,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  whiteSpace: "nowrap",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.06)";
                    e.currentTarget.style.color = "#E2E8F0";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = "transparent";
                    e.currentTarget.style.color = "#94A3B8";
                  }
                }}
              >
                <Icon size={14} color="currentColor" />
                <span>{tab.label}</span>
              </button>
            );
          })}

          {/* Search shortcut */}
          {onOpenCommandPalette && (
            <button
              onClick={onOpenCommandPalette}
              title="Qidiruv (Ctrl+K)"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "30px",
                height: "30px",
                borderRadius: "8px",
                backgroundColor: "transparent",
                border: "1px solid transparent",
                color: "#64748B",
                cursor: "pointer",
                transition: "all 0.15s ease",
                marginLeft: "4px",
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

        {/* ── RIGHT: Profile + Voice + WindowControls ── */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "220px", justifyContent: "flex-end" }}>
          {/* Voice shortcut */}
          <button
            onClick={() => onNavigate("/voice")}
            title="Ovozli muloqot"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "30px",
              height: "30px",
              borderRadius: "8px",
              backgroundColor: currentPath === "/voice" ? "rgba(244, 63, 94, 0.15)" : "transparent",
              border: currentPath === "/voice" ? "1px solid rgba(244, 63, 94, 0.3)" : "1px solid transparent",
              color: currentPath === "/voice" ? "#F43F5E" : "#64748B",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              if (currentPath !== "/voice") {
                e.currentTarget.style.backgroundColor = "rgba(244, 63, 94, 0.1)";
                e.currentTarget.style.color = "#F43F5E";
              }
            }}
            onMouseLeave={(e) => {
              if (currentPath !== "/voice") {
                e.currentTarget.style.backgroundColor = "transparent";
                e.currentTarget.style.color = "#64748B";
              }
            }}
          >
            <MicIcon size={14} color="currentColor" />
          </button>

          {/* User Profile */}
          <div
            onClick={() => onNavigate("/account")}
            title={`${userName} — Hisob sozlamalari`}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "7px",
              padding: "3px 10px 3px 4px",
              borderRadius: "20px",
              backgroundColor: currentPath === "/account" ? "rgba(56, 189, 248, 0.12)" : "rgba(255, 255, 255, 0.04)",
              border: currentPath === "/account"
                ? "1px solid rgba(56, 189, 248, 0.3)"
                : "1px solid rgba(255, 255, 255, 0.07)",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)";
              e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = currentPath === "/account" ? "rgba(56, 189, 248, 0.12)" : "rgba(255, 255, 255, 0.04)";
              e.currentTarget.style.borderColor = currentPath === "/account" ? "rgba(56, 189, 248, 0.3)" : "rgba(255, 255, 255, 0.07)";
            }}
          >
            <Avatar initials={effectiveInitials} size={24} avatarStyle={currentAvatarStyle} />
            <span style={{ fontSize: "12px", fontWeight: 600, color: "#E2E8F0" }}>
              {userName}
            </span>
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
          height: "calc(100vh - var(--topnav-height))",
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
