import React, { useState, useEffect } from "react";
import { MinimizeIcon, MaximizeIcon, RestoreIcon, CloseIcon } from "./icons/Icons";

interface WindowControlsProps {
  className?: string;
}

export const WindowControls: React.FC<WindowControlsProps> = ({ className = "" }) => {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
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
        // Browser fallback
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
      console.log("[WindowControls] Minimize");
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
    }
  };

  const handleClose = async () => {
    try {
      const { getCurrentWindow } = await import("@tauri-apps/api/window");
      await getCurrentWindow().close();
    } catch {
      console.log("[WindowControls] Close");
    }
  };

  return (
    <div
      className={`window-controls ${className}`}
      style={{
        display: "flex",
        alignItems: "center",
        height: "36px",
        paddingRight: "8px",
        gap: "2px",
        ...({ WebkitAppRegion: "no-drag" } as React.CSSProperties),
      }}
    >
      <button
        onClick={handleMinimize}
        title="Kichraytirish"
        aria-label="Kichraytirish"
        style={buttonStyle}
        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)")}
        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
      >
        <MinimizeIcon size={12} color="rgba(255, 255, 255, 0.75)" />
      </button>

      <button
        onClick={handleMaximize}
        title={isMaximized ? "Oldingi o‘lchamga qaytarish" : "Kattalashtirish"}
        aria-label={isMaximized ? "Oldingi o‘lchamga qaytarish" : "Kattalashtirish"}
        style={buttonStyle}
        onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.08)")}
        onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
      >
        {isMaximized ? (
          <RestoreIcon size={12} color="rgba(255, 255, 255, 0.75)" />
        ) : (
          <MaximizeIcon size={12} color="rgba(255, 255, 255, 0.75)" />
        )}
      </button>

      <button
        onClick={handleClose}
        title="Yopish"
        aria-label="Yopish"
        style={buttonStyle}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = "#EF4444";
          const svg = e.currentTarget.querySelector("svg");
          if (svg) svg.style.stroke = "#FFFFFF";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = "transparent";
          const svg = e.currentTarget.querySelector("svg");
          if (svg) svg.style.stroke = "rgba(255, 255, 255, 0.75)";
        }}
      >
        <CloseIcon size={12} color="rgba(255, 255, 255, 0.75)" />
      </button>
    </div>
  );
};

const buttonStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: "36px",
  height: "28px",
  borderRadius: "6px",
  transition: "all 0.15s ease",
  cursor: "pointer",
};
