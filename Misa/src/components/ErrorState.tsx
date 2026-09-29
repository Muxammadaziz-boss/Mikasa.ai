// ========== ErrorState.tsx ==========
// Mikasa AI 7.x — Reusable Inline Error State [Phase 21]
// 3-part structured error: What happened, Why, Action button

import React from "react";
import { RefreshIcon } from "./icons/Icons";

interface ErrorStateProps {
  /** Nima sodir bo'ldi — qisqa sarlavha */
  title: string;
  /** Nima uchun sodir bo'ldi — tushuntirish */
  description?: string;
  /** Tugma matni */
  actionLabel?: string;
  /** Tugma bosilganda */
  onAction?: () => void;
  /** Ikkinchi tugma matni (ixtiyoriy) */
  secondaryLabel?: string;
  /** Ikkinchi tugma bosilganda */
  onSecondary?: () => void;
  /** Kichik inline holat yoki to'liq sahifa */
  compact?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  description,
  actionLabel = "Qayta urinish",
  onAction,
  secondaryLabel,
  onSecondary,
  compact = false,
}) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: compact ? "24px 16px" : "48px 24px",
        gap: compact ? "10px" : "14px",
        textAlign: "center",
        width: "100%",
        ...(compact ? {} : { minHeight: "260px" }),
      }}
      role="alert"
    >
      {/* Error icon circle */}
      <div
        style={{
          width: compact ? 40 : 52,
          height: compact ? 40 : 52,
          borderRadius: "50%",
          background: "rgba(239, 68, 68, 0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <svg
          width={compact ? 20 : 24}
          height={compact ? 20 : 24}
          viewBox="0 0 24 24"
          fill="none"
          stroke="#EF4444"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>

      {/* What happened */}
      <span
        style={{
          fontSize: compact ? "13px" : "15px",
          fontWeight: 600,
          color: "#F1F5F9",
          maxWidth: "380px",
        }}
      >
        {title}
      </span>

      {/* Why it happened */}
      {description && (
        <span
          style={{
            fontSize: compact ? "12px" : "13px",
            color: "#94A3B8",
            maxWidth: "380px",
            lineHeight: 1.5,
          }}
        >
          {description}
        </span>
      )}

      {/* Action buttons */}
      {(onAction || onSecondary) && (
        <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
          {onAction && (
            <button
              onClick={onAction}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                padding: compact ? "7px 14px" : "9px 18px",
                borderRadius: "8px",
                border: "none",
                background: "#10B981",
                color: "#fff",
                fontSize: compact ? "12px" : "13px",
                fontWeight: 500,
                cursor: "pointer",
                transition: "opacity 0.15s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
              aria-label={actionLabel}
            >
              <RefreshIcon size={compact ? 12 : 14} />
              {actionLabel}
            </button>
          )}
          {onSecondary && secondaryLabel && (
            <button
              onClick={onSecondary}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                padding: compact ? "7px 14px" : "9px 18px",
                borderRadius: "8px",
                border: "1px solid rgba(148, 163, 184, 0.2)",
                background: "transparent",
                color: "#94A3B8",
                fontSize: compact ? "12px" : "13px",
                fontWeight: 500,
                cursor: "pointer",
                transition: "opacity 0.15s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.7")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
              aria-label={secondaryLabel}
            >
              {secondaryLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
