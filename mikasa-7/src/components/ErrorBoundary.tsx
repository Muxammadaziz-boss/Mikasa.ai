// ========== ErrorBoundary.tsx ==========
// Mikasa AI 7.x — Global React Error Boundary [Phase 21]
// Catches unhandled React rendering errors with structured 3-part messages

import React, { Component, ErrorInfo } from "react";
import { RefreshIcon } from "./icons/Icons";

interface Props {
  children: React.ReactNode;
  fallbackNavigate?: () => void;
}

interface State {
  hasError: boolean;
  errorMessage: string;
  errorStack: string;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, errorMessage: "", errorStack: "" };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      errorMessage: error.message || "Noma'lum xatolik",
      errorStack: error.stack || "",
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[Mikasa ErrorBoundary]", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, errorMessage: "", errorStack: "" });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            minHeight: "400px",
            padding: "40px 20px",
            textAlign: "center",
            gap: "16px",
          }}
        >
          {/* Error icon */}
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: "rgba(239, 68, 68, 0.12)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>

          {/* What happened */}
          <h3
            style={{
              margin: 0,
              fontSize: "16px",
              fontWeight: 600,
              color: "#F1F5F9",
            }}
          >
            Sahifada kutilmagan xatolik yuz berdi
          </h3>

          {/* Why it happened */}
          <p
            style={{
              margin: 0,
              fontSize: "13px",
              color: "#94A3B8",
              maxWidth: "420px",
              lineHeight: 1.5,
            }}
          >
            {this.state.errorMessage || "Noma'lum ichki xatolik. Bu muammo tizim log-larida qayd etildi."}
          </p>

          {/* Action buttons */}
          <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
            <button
              onClick={this.handleRetry}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "9px 18px",
                borderRadius: "8px",
                border: "none",
                background: "#10B981",
                color: "#fff",
                fontSize: "13px",
                fontWeight: 500,
                cursor: "pointer",
                transition: "opacity 0.15s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
              aria-label="Qayta urinish"
            >
              <RefreshIcon size={14} />
              Qayta urinish
            </button>
            {this.props.fallbackNavigate && (
              <button
                onClick={this.props.fallbackNavigate}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "9px 18px",
                  borderRadius: "8px",
                  border: "1px solid rgba(148, 163, 184, 0.2)",
                  background: "transparent",
                  color: "#94A3B8",
                  fontSize: "13px",
                  fontWeight: 500,
                  cursor: "pointer",
                  transition: "opacity 0.15s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.7")}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
                aria-label="Bosh sahifaga qaytish"
              >
                Bosh sahifaga qaytish
              </button>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
