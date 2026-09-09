import React from "react";
import {
  HomeIcon,
  MicIcon,
  ChatIcon,
  CommandsIcon,
  MemoryIcon,
  SchedulerIcon,
  PluginsIcon,
} from "../components/icons/Icons";
import { AccountRow } from "./AccountRow";

export interface NavItemDef {
  id: string;
  path: string;
  label: string;
  icon: React.ComponentType<{ size?: number; color?: string }>;
}

export interface NavSectionDef {
  title: string;
  items: NavItemDef[];
}

export const NAV_SECTIONS: NavSectionDef[] = [
  {
    title: "MIKASA",
    items: [
      { id: "home", path: "/", label: "Bosh sahifa", icon: HomeIcon },
      { id: "voice", path: "/voice", label: "Ovozli muloqot", icon: MicIcon },
      { id: "chat", path: "/chat", label: "AI Suhbat", icon: ChatIcon },
      { id: "commands", path: "/commands", label: "Buyruqlar", icon: CommandsIcon },
      { id: "memory", path: "/memory", label: "Xotira", icon: MemoryIcon },
    ],
  },
  {
    title: "AGENT",
    items: [
      { id: "scheduler", path: "/scheduler", label: "Rejalashtiruvchi", icon: SchedulerIcon },
      { id: "plugins", path: "/plugins", label: "Plaginlar", icon: PluginsIcon },
    ],
  },
];

interface SidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPath, onNavigate }) => {
  return (
    <aside
      className="mikasa-sidebar"
      style={{
        width: "var(--sidebar-width)",
        height: "100%",
        backgroundColor: "var(--surface)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "12px 8px 8px 8px",
        userSelect: "none",
        flexShrink: 0,
      }}
    >
      {/* Top Nav Sections */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px", overflowY: "auto" }}>
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
            <span
              style={{
                fontSize: "var(--font-size-label)",
                fontWeight: 700,
                color: "var(--text-muted)",
                letterSpacing: "0.08em",
                padding: "2px 12px 4px 12px",
              }}
            >
              {section.title}
            </span>

            {section.items.map((item) => {
              const isActive = currentPath === item.path;
              const IconComp = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.path)}
                  style={{
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "9px 12px",
                    borderRadius: "var(--radius-md)",
                    backgroundColor: isActive ? "var(--surface-active)" : "transparent",
                    color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                    fontWeight: isActive ? 600 : 500,
                    fontSize: "var(--font-size-body)",
                    transition: "all 0.12s ease",
                    cursor: "pointer",
                    border: "none",
                    textAlign: "left",
                    width: "100%",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = "var(--surface-hover)";
                      e.currentTarget.style.color = "var(--text-primary)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.backgroundColor = "transparent";
                      e.currentTarget.style.color = "var(--text-secondary)";
                    }
                  }}
                >
                  {/* Left Active indicator bar */}
                  {isActive && (
                    <div
                      style={{
                        position: "absolute",
                        left: "3px",
                        top: "8px",
                        bottom: "8px",
                        width: "3px",
                        borderRadius: "2px",
                        backgroundColor: "var(--primary)",
                      }}
                    />
                  )}
                  <IconComp
                    size={16}
                    color={isActive ? "var(--primary-glow)" : "var(--text-muted)"}
                  />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Bottom User Account Area */}
      <div style={{ display: "flex", flexDirection: "column", gap: "6px", paddingTop: "8px" }}>
        <div style={{ height: "1px", backgroundColor: "var(--border-subtle)", margin: "0 4px" }} />
        <AccountRow
          active={currentPath === "/account"}
          onClick={() => onNavigate("/account")}
        />
      </div>
    </aside>
  );
};
