import React from "react";
import { Avatar } from "../components/Avatar";
import { ChevronRightIcon } from "../components/icons/Icons";

interface AccountRowProps {
  name?: string;
  initials?: string;
  active?: boolean;
  onClick?: () => void;
  className?: string;
}

export const AccountRow: React.FC<AccountRowProps> = ({
  name = "Muxammadaziz",
  initials = "MA",
  active = false,
  onClick,
  className = "",
}) => {
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
        padding: "8px 10px",
        borderRadius: "var(--radius-md)",
        backgroundColor: active ? "var(--surface-active)" : "transparent",
        border: active ? "1px solid var(--border-hover)" : "1px solid transparent",
        cursor: "pointer",
        transition: "all 0.15s ease",
        userSelect: "none",
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.backgroundColor = "var(--surface-hover)";
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.backgroundColor = "transparent";
        }
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px", overflow: "hidden" }}>
        <Avatar initials={initials} size={30} />
        <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
          <span
            style={{
              fontSize: "12px",
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
              fontSize: "10.5px",
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
