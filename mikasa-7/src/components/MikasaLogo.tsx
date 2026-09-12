import React from "react";
import { SparklesIcon } from "./icons/Icons";

interface MikasaLogoProps {
  compact?: boolean;
  onClick?: () => void;
  className?: string;
}

export const MikasaLogo: React.FC<MikasaLogoProps> = ({
  compact = false,
  onClick,
  className = "",
}) => {
  return (
    <div
      onClick={onClick}
      className={`mikasa-logo ${className}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "10px",
        cursor: onClick ? "pointer" : "default",
        userSelect: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: "28px",
          height: "28px",
          borderRadius: "50%",
          background: "radial-gradient(circle at 35% 35%, #38BDF8 0%, #0284C7 60%, #071D3A 100%)",
          boxShadow: "0 0 12px rgba(56, 189, 248, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.6)",
          border: "1px solid rgba(56, 189, 248, 0.5)",
          flexShrink: 0,
        }}
      >
        <SparklesIcon size={14} color="#FFFFFF" />
      </div>

      {!compact && (
        <span
          style={{
            fontSize: "13px",
            fontWeight: 700,
            letterSpacing: "0.08em",
            color: "#FFFFFF",
            fontFamily: "var(--font-family)",
            whiteSpace: "nowrap",
          }}
        >
          MIKASA AI
        </span>
      )}
    </div>
  );
};
