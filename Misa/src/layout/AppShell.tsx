import React, { useState, useRef, useEffect } from "react";
import { WindowControls } from "../components/WindowControls";
import { Avatar } from "../components/Avatar";
import { DeviceSelector } from "../components/DeviceSelector";
import { MisaLogo } from "../components/MisaLogo";
import {
  HomeIcon,
  ChatIcon,
  CommandsIcon,
  DatabaseIcon,
  SchedulerIcon,
  PluginsIcon,
  SettingsIcon,
  RemoteControlIcon,
  LaptopIcon,
  TelegramIcon,
  SearchIcon,
  MicIcon,
} from "../components/icons/Icons";

interface AppShellProps {
  children: React.ReactNode;
  activePath: string;
  onNavigate: (path: string) => void;
  onOpenCommandPalette?: () => void;
  userName?: string;
  avatarStyle?: string;
}

const PRIMARY_NAV_ITEMS = [
  { path: "/", label: "Asosiy sahifa", icon: HomeIcon },
  { path: "/chat", label: "Suhbat", icon: ChatIcon },
  { path: "/memory", label: "Xotira", icon: DatabaseIcon },
  { path: "/scheduler", label: "Rejalashtirish", icon: SchedulerIcon },
];

const EXTRA_NAV_ITEMS = [
  { path: "/commands", label: "Buyruqlar Markazi", desc: "29+ tizim va AI vositalari", icon: CommandsIcon },
  { path: "/plugins", label: "Plaginlar Katalogi", desc: "Kengaytmalar va integratsiyalar", icon: PluginsIcon },
  { path: "/devices", label: "Qurilmalar", desc: "Ulangan kompyuterlar boshqaruvi", icon: LaptopIcon },
  { path: "/remote", label: "Masofaviy Boshqaruv", desc: "Ruxsatlar va xavfsizlik markazi", icon: RemoteControlIcon },
  { path: "/telegram", label: "Telegram Integratsiya", desc: "OTP ulanish va mobil agent", icon: TelegramIcon },
  { path: "/voice", label: "Ovozli Muloqot", desc: "To'liq ekranli jonli ovoz rejimi", icon: MicIcon },
];

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activePath,
  onNavigate,
  onOpenCommandPalette,
  userName = "Ustoz",
  avatarStyle = "cosmic",
}) => {
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const moreMenuRef = useRef<HTMLDivElement>(null);

  const activeExtraItem = EXTRA_NAV_ITEMS.find((item) => item.path === activePath);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (moreMenuRef.current && !moreMenuRef.current.contains(e.target as Node)) {
        setMoreMenuOpen(false);
      }
    };
    if (moreMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [moreMenuOpen]);

  return (
    <div
      className="misa-app-shell mikasa-app-shell"
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100vw",
        height: "100vh",
        backgroundColor: "var(--bg-darkest, #02060E)",
        color: "var(--text-primary)",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* 1. Deep Midnight Canvas & Ambient Violet Glows */}
      <div className="cinematic-bg misa-canvas-bg" />

      {/* 2. Subtle Architectural Micro-Grid Overlay */}
      <div className="cinematic-vignette misa-grid-overlay" />

      {/* 3. FLOATING ULTRA GLASS TOP NAVIGATION BAR (No Sidebar) */}
      <header
        data-tauri-drag-region
        style={{
          position: "relative",
          zIndex: 100,
          width: "100%",
          padding: "12px 16px 6px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          userSelect: "none",
        }}
      >
        <nav
          data-tauri-drag-region
          className="misa-ultra-glass mikasa-glass-topnav"
          aria-label="Asosiy navigatsiya"
          style={{
            width: "100%",
            maxWidth: "1440px",
            height: "54px",
            borderRadius: "9999px",
            padding: "0 8px 0 16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
            background: "rgba(24, 13, 36, var(--misa-glass-opacity, 0.62))",
            backdropFilter: "blur(24px) saturate(180%)",
            WebkitBackdropFilter: "blur(24px) saturate(180%)",
            border: "1px solid rgba(232, 179, 255, 0.14)",
            boxShadow:
              "0 20px 50px rgba(2, 6, 14, 0.82), 0 0 30px rgba(147, 3, 197, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.12)",
          }}
        >
          {/* ── LEFT: Misa v9.0 Brand Capsule ── */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "14px",
              flexShrink: 0,
              ...({ WebkitAppRegion: "no-drag" } as React.CSSProperties),
            }}
          >
            <MisaLogo onClick={() => onNavigate("/")} showVersion={true} />
            <div
              style={{
                width: "1px",
                height: "20px",
                background: "rgba(255, 255, 255, 0.1)",
              }}
            />
          </div>

          {/* ── CENTER: Detached Floating Navigation Pills ── */}
          <div
            className="misa-topnav-center mikasa-topnav-center"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "4px",
              borderRadius: "9999px",
              background: "rgba(2, 6, 14, 0.48)",
              border: "1px solid rgba(255, 255, 255, 0.06)",
              ...({ WebkitAppRegion: "no-drag" } as React.CSSProperties),
            }}
          >
            {PRIMARY_NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activePath === item.path;
              return (
                <button
                  key={item.path}
                  onClick={() => onNavigate(item.path)}
                  aria-current={isActive ? "page" : undefined}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "7px",
                    padding: "7px 16px",
                    borderRadius: "9999px",
                    fontSize: "12.5px",
                    fontWeight: isActive ? 600 : 500,
                    color: isActive ? "#FFFFFF" : "var(--text-secondary)",
                    background: isActive
                      ? "linear-gradient(135deg, rgba(147, 3, 197, 0.36) 0%, rgba(192, 76, 253, 0.22) 100%)"
                      : "transparent",
                    border: isActive
                      ? "1px solid rgba(192, 76, 253, 0.45)"
                      : "1px solid transparent",
                    boxShadow: isActive ? "0 0 18px rgba(147, 3, 197, 0.35)" : "none",
                    cursor: "pointer",
                    transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
                    whiteSpace: "nowrap",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = "#FFFFFF";
                      e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = "var(--text-secondary)";
                      e.currentTarget.style.background = "transparent";
                    }
                  }}
                >
                  <Icon size={14} color={isActive ? "#E8B3FF" : "currentColor"} />
                  <span className="misa-topnav-label">{item.label}</span>
                </button>
              );
            })}

            {/* More / System Centers Dropdown Pill */}
            <div ref={moreMenuRef} style={{ position: "relative" }}>
              <button
                type="button"
                onClick={() => setMoreMenuOpen((prev) => !prev)}
                aria-expanded={moreMenuOpen}
                title="Boshqa bo'limlar va vositalar"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "7px 14px",
                  borderRadius: "9999px",
                  fontSize: "12.5px",
                  fontWeight: activeExtraItem ? 600 : 500,
                  color: activeExtraItem || moreMenuOpen ? "#FFFFFF" : "var(--text-secondary)",
                  background: activeExtraItem
                    ? "linear-gradient(135deg, rgba(147, 3, 197, 0.36) 0%, rgba(192, 76, 253, 0.22) 100%)"
                    : moreMenuOpen
                    ? "rgba(255, 255, 255, 0.08)"
                    : "transparent",
                  border: activeExtraItem
                    ? "1px solid rgba(192, 76, 253, 0.45)"
                    : "1px solid transparent",
                  boxShadow: activeExtraItem ? "0 0 18px rgba(147, 3, 197, 0.35)" : "none",
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  whiteSpace: "nowrap",
                }}
              >
                {activeExtraItem ? (
                  <>
                    <activeExtraItem.icon size={14} color="#E8B3FF" />
                    <span className="misa-topnav-label">{activeExtraItem.label.split(" ")[0]}</span>
                  </>
                ) : (
                  <>
                    <CommandsIcon size={14} color="currentColor" />
                    <span className="misa-topnav-label">Markazlar</span>
                  </>
                )}
                <svg
                  width="11"
                  height="11"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  style={{
                    transform: moreMenuOpen ? "rotate(180deg)" : "rotate(0deg)",
                    transition: "transform 0.2s ease",
                    opacity: 0.75,
                  }}
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>

              {moreMenuOpen && (
                <div
                  className="misa-ultra-glass"
                  style={{
                    position: "absolute",
                    top: "calc(100% + 10px)",
                    right: 0,
                    width: "270px",
                    padding: "8px",
                    borderRadius: "20px",
                    background: "rgba(15, 11, 26, 0.94)",
                    backdropFilter: "blur(28px)",
                    WebkitBackdropFilter: "blur(28px)",
                    border: "1px solid rgba(232, 179, 255, 0.2)",
                    boxShadow: "0 24px 60px rgba(2, 6, 14, 0.92), 0 0 30px rgba(147, 3, 197, 0.2)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                    zIndex: 300,
                    animation: "misa-fade-in 0.16s ease-out",
                  }}
                >
                  <div
                    style={{
                      padding: "6px 10px 4px",
                      fontSize: "10px",
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      color: "var(--text-muted)",
                    }}
                  >
                    Misa Tizim Markazlari
                  </div>
                  {EXTRA_NAV_ITEMS.map((item) => {
                    const Icon = item.icon;
                    const isItemActive = activePath === item.path;
                    return (
                      <button
                        key={item.path}
                        type="button"
                        onClick={() => {
                          setMoreMenuOpen(false);
                          onNavigate(item.path);
                        }}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          width: "100%",
                          padding: "9px 11px",
                          borderRadius: "12px",
                          textAlign: "left",
                          background: isItemActive ? "rgba(147, 3, 197, 0.22)" : "transparent",
                          border: isItemActive
                            ? "1px solid rgba(192, 76, 253, 0.38)"
                            : "1px solid transparent",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                        onMouseEnter={(e) => {
                          if (!isItemActive) {
                            e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isItemActive) {
                            e.currentTarget.style.background = "transparent";
                          }
                        }}
                      >
                        <div
                          style={{
                            width: "30px",
                            height: "30px",
                            borderRadius: "9px",
                            background: isItemActive
                              ? "rgba(192, 76, 253, 0.25)"
                              : "rgba(255, 255, 255, 0.05)",
                            border: "1px solid rgba(255, 255, 255, 0.08)",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: isItemActive ? "#E8B3FF" : "var(--text-secondary)",
                            flexShrink: 0,
                          }}
                        >
                          <Icon size={15} color="currentColor" />
                        </div>
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div
                            style={{
                              fontSize: "12.5px",
                              fontWeight: 600,
                              color: isItemActive ? "#FFFFFF" : "var(--text-primary)",
                            }}
                          >
                            {item.label}
                          </div>
                          <div
                            style={{
                              fontSize: "10.5px",
                              color: "var(--text-muted)",
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {item.desc}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* ── RIGHT: Search Pill (Ctrl+K), Device Selector, Profile Pill & Window Controls ── */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              flexShrink: 0,
              ...({ WebkitAppRegion: "no-drag" } as React.CSSProperties),
            }}
          >
            {/* Command Palette Trigger Pill */}
            <button
              type="button"
              onClick={onOpenCommandPalette}
              title="Tezkor qidiruv va buyruqlar (Ctrl+K)"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "6px 12px",
                borderRadius: "9999px",
                background: "rgba(255, 255, 255, 0.035)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                color: "var(--text-secondary)",
                fontSize: "12px",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(147, 3, 197, 0.14)";
                e.currentTarget.style.borderColor = "rgba(192, 76, 253, 0.35)";
                e.currentTarget.style.color = "#FFFFFF";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.035)";
                e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
                e.currentTarget.style.color = "var(--text-secondary)";
              }}
            >
              <SearchIcon size={13} color="currentColor" />
              <span className="misa-topnav-label">Qidirish...</span>
              <kbd
                style={{
                  fontSize: "10px",
                  fontFamily: "var(--font-mono)",
                  padding: "1px 5px",
                  borderRadius: "4px",
                  background: "rgba(255, 255, 255, 0.08)",
                  color: "var(--text-muted)",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                }}
              >
                Ctrl+K
              </kbd>
            </button>

            <DeviceSelector onManageDevices={() => onNavigate("/devices")} />

            {/* User Profile & Settings Pill */}
            <button
              type="button"
              onClick={() => onNavigate("/account")}
              title="Profil va Sozlamalar"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "4px 6px 4px 12px",
                borderRadius: "9999px",
                background:
                  activePath === "/account"
                    ? "linear-gradient(135deg, rgba(147, 3, 197, 0.36) 0%, rgba(192, 76, 253, 0.2) 100%)"
                    : "rgba(255, 255, 255, 0.04)",
                border:
                  activePath === "/account"
                    ? "1px solid rgba(192, 76, 253, 0.45)"
                    : "1px solid rgba(255, 255, 255, 0.1)",
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                if (activePath !== "/account") {
                  e.currentTarget.style.borderColor = "rgba(192, 76, 253, 0.35)";
                  e.currentTarget.style.background = "rgba(147, 3, 197, 0.12)";
                }
              }}
              onMouseLeave={(e) => {
                if (activePath !== "/account") {
                  e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.1)";
                  e.currentTarget.style.background = "rgba(255, 255, 255, 0.04)";
                }
              }}
            >
              <span
                className="misa-topnav-label"
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#F5F0FF",
                  maxWidth: "110px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {userName}
              </span>
              <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
                <Avatar name={userName} size="sm" styleId={avatarStyle} />
                <span
                  style={{
                    position: "absolute",
                    bottom: "-1px",
                    right: "-1px",
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: "#4EDEA3",
                    border: "1.5px solid #02060E",
                    boxShadow: "0 0 6px rgba(78, 222, 163, 0.8)",
                  }}
                />
              </div>
              <SettingsIcon size={13} color={activePath === "/account" ? "#E8B3FF" : "var(--text-secondary)"} />
            </button>

            <div
              style={{
                width: "1px",
                height: "18px",
                background: "rgba(255, 255, 255, 0.08)",
                marginLeft: "2px",
              }}
            />

            <WindowControls />
          </div>
        </nav>
      </header>

      {/* 4. FULL-BLEED WORKSPACE STAGE */}
      <main
        style={{
          flex: 1,
          position: "relative",
          zIndex: 10,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {children}
      </main>
    </div>
  );
};
