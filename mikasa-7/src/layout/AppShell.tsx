import React from "react";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";

interface AppShellProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentPath,
  onNavigate,
  children,
}) => {
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
      }}
    >
      {/* 1. Global Custom Desktop TopBar */}
      <TopBar onLogoClick={() => onNavigate("/")} />

      {/* 2. Main Workspace Layout */}
      <div
        style={{
          display: "flex",
          flex: 1,
          height: "calc(100vh - var(--topbar-height))",
          overflow: "hidden",
        }}
      >
        {/* Left Navigation Sidebar */}
        <Sidebar currentPath={currentPath} onNavigate={onNavigate} />

        {/* Center Main Content Area */}
        <main
          style={{
            flex: 1,
            height: "100%",
            backgroundColor: "var(--bg-dark)",
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
