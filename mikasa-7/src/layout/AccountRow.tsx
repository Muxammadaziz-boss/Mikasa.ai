import React from "react";
import { Avatar } from "../components/Avatar";
import { ChevronRightIcon } from "../components/icons/Icons";

interface AccountRowProps {
  name?: string;
  initials?: string;
  active?: boolean;
  collapsed?: boolean;
  onClick?: () => void;
  className?: string;
}

export const AccountRow: React.FC<AccountRowProps> = ({
  name = "Muxammadaziz",
  initials = "MA",
  active = false,
  collapsed = false,
  onClick,
  className = "",
}) => {
  if (collapsed) {
    return (
      <button
        onClick={onClick}
        title={`${name} — Hisob`}
        aria-label={`${name} — Hisob`}
        className={`account-row-collapsed ${className}`}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: "48px",
          height: "48px",
          margin: "0 auto",
          borderRadius: "var(--radius-md)",
          backgroundColor: active ? "var(--surface-active)" : "rgba(13, 19, 31, 0.6)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          cursor: "pointer",
          transition: "all 0.15s ease",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.3)")}
        onMouseLeave={(e) => (e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)")}
      >
        <Avatar initials={initials} size={32} />
      </button>
    );
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
      className={`account-row ${className}`}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "10px 12px",
        borderRadius: "var(--radius-md)",
        backgroundColor: active ? "rgba(2, 132, 199, 0.15)" : "rgba(13, 19, 31, 0.65)",
        border: active ? "1px solid var(--border-active)" : "1px solid rgba(255, 255, 255, 0.07)",
        cursor: "pointer",
        transition: "all 0.15s ease",
        userSelect: "none",
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.backgroundColor = "rgba(20, 28, 45, 0.8)";
          e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.15)";
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.backgroundColor = "rgba(13, 19, 31, 0.65)";
          e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.07)";
        }
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px", overflow: "hidden" }}>
        <Avatar initials={initials} size={32} />
        <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
          <span
            style={{
              fontSize: "12.5px",
              fontWeight: 600,
              color: "var(--text-primary)",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {name}
          </span>
          <span
            style={{
              fontSize: "11px",
              color: "var(--text-muted)",
            }}
          >
            Hisob
          </span>
        </div>
      </div>

      <ChevronRightIcon size={14} color="var(--text-muted)" />
    </div>
  );
};
