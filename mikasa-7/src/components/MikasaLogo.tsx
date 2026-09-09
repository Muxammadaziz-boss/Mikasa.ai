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
        gap: "8px",
        cursor: onClick ? "pointer" : "default",
        userSelect: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: "22px",
          height: "22px",
          borderRadius: "var(--radius-sm)",
          background: "var(--primary-soft)",
          border: "1px solid var(--glass-border)",
        }}
      >
        <SparklesIcon size={13} color="var(--primary-glow)" />
      </div>
      <span
        style={{
          fontSize: "12.5px",
          fontWeight: 700,
          letterSpacing: "0.12em",
          color: "var(--text-primary)",
          fontFamily: "var(--font-family)",
        }}
      >
        {compact ? "MIKASA" : "MIKASA AI"}
      </span>
    </div>
  );
};
