import React from "react";
import { CircleDotIcon } from "./icons/Icons";

interface StatusIndicatorProps {
  online?: boolean;
  label?: string;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  online = true,
  label,
  className = "",
}) => {
  const displayLabel = label ?? (online ? "Online" : "Offline");
  const color = online ? "var(--success)" : "var(--error)";

  return (
    <div
      role="status"
      className={`status-indicator ${className}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "3px 10px",
        borderRadius: "var(--radius-pill)",
        background: "var(--surface)",
        border: "1px solid var(--border-subtle)",
        fontSize: "var(--font-size-caption)",
        color: "var(--text-muted)",
        userSelect: "none",
      }}
    >
      <CircleDotIcon size={7} color={color} />
      <span>{displayLabel}</span>
    </div>
  );
};
