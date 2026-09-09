import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { WindowControls } from "../components/WindowControls";

interface AppShellProps {
  currentPath: string;
  onNavigate: (path: string, initialPrompt?: string) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentPath,
  onNavigate,
  children,
}) => {
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window !== "undefined" && window.location.search.includes("collapsed=true")) {
      return true;
    }
    return false;
  });


  return (
    <div
      className="mikasa-app-shell"
      style={{
        display: "flex",
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

      {/* 1. Left Translucent Glass Sidebar */}
      <Sidebar
        currentPath={currentPath}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
        onNavigate={onNavigate}
      />

      {/* 2. Main Workspace Layout */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          flex: 1,
          height: "100%",
          overflow: "hidden",
          position: "relative",
          zIndex: 5,
        }}
      >
        {/* Minimalist Top Drag Strip with Window Controls */}
        <header
          data-tauri-drag-region
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            height: "36px",
            width: "100%",
            flexShrink: 0,
            userSelect: "none",
            zIndex: 30,
            background: "transparent",
          }}
        >
          <WindowControls />
        </header>

        {/* Dynamic Route Content */}
        <main
          style={{
            display: "flex",
            flex: 1,
            height: "calc(100% - 36px)",
            overflow: "hidden",
            position: "relative",
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
};
