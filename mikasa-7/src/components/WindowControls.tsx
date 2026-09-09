import React, { useState, useEffect } from "react";
import { MinimizeIcon, MaximizeIcon, RestoreIcon, CloseIcon } from "./icons/Icons";

interface WindowControlsProps {
  className?: string;
}

export const WindowControls: React.FC<WindowControlsProps> = ({ className = "" }) => {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    // Check Tauri environment safely
    let unlisten: (() => void) | undefined;
    const initTauri = async () => {
      try {
        const { getCurrentWindow } = await import("@tauri-apps/api/window");
        const appWindow = getCurrentWindow();
        const maxState = await appWindow.isMaximized();
        setIsMaximized(maxState);

        unlisten = await appWindow.onResized(async () => {
          const state = await appWindow.isMaximized();
          setIsMaximized(state);
        });
      } catch {
        // Browser dev fallback
      }
    };
    initTauri();

    return () => {
      if (unlisten) unlisten();
    };
  }, []);

  const handleMinimize = async () => {
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await getCurrentWindow().minimize();
    } catch {
      console.log("[WindowControls] Minimize clicked (browser mode)");
    }
  };

  const handleMaximize = async () => {
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await getCurrentWindow().toggleMaximize();
      const state = await getCurrentWindow().isMaximized();
      setIsMaximized(state);
    } catch {
      setIsMaximized(!isMaximized);
      console.log("[WindowControls] Maximize toggled (browser mode)");
    }
  };

  const handleClose = async () => {
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await getCurrentWindow().close();
    } catch {
      console.log("[WindowControls] Close clicked (browser mode)");
    }
  };

  return (
    <div
      className={`window-controls ${className}`}
      style={{
        display: "flex",
        alignItems: "center",
        height: "100%",
        ...({ WebkitAppRegion: "no-drag" } as React.CSSProperties),
      }}
    >
      <button
        onClick={handleMinimize}
        title="Kichraytirish"
        style={buttonStyle}
        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--surface-hover)")}
        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
      >
        <MinimizeIcon size={14} color="var(--text-secondary)" />
      </button>

      <button
        onClick={handleMaximize}
        title={isMaximized ? "Oldingi o‘lchamga qaytarish" : "Kattalashtirish"}
        style={buttonStyle}
        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--surface-hover)")}
        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
      >
        {isMaximized ? (
          <RestoreIcon size={14} color="var(--text-secondary)" />
        ) : (
          <MaximizeIcon size={14} color="var(--text-secondary)" />
        )}
      </button>

      <button
        onClick={handleClose}
        title="Yopish"
        style={buttonStyle}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = "#DC2626";
          const svg = e.currentTarget.querySelector("svg");
          if (svg) svg.style.stroke = "#FFFFFF";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = "transparent";
          const svg = e.currentTarget.querySelector("svg");
          if (svg) svg.style.stroke = "var(--text-secondary)";
        }}
      >
        <CloseIcon size={14} color="var(--text-secondary)" />
      </button>
    </div>
  );
};

const buttonStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: "44px",
  height: "100%",
  transition: "background-color 0.15s ease",
  cursor: "pointer",
};
