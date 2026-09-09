import React from "react";

export type OrbState = "idle" | "listening" | "thinking" | "speaking" | "loading" | "error" | "offline";

interface MikasaOrbProps {
  size?: number;
  state?: OrbState;
  className?: string;
  onClick?: () => void;
}

export const MikasaOrb: React.FC<MikasaOrbProps> = ({
  size = 150,
  state = "idle",
  className = "",
  onClick,
}) => {
  // Determine color themes per state
  const getStateColors = () => {
    switch (state) {
      case "listening":
        return {
          glow: "rgba(56, 189, 248, 0.45)",
          innerGlow: "rgba(14, 165, 233, 0.6)",
          core: "radial-gradient(circle at 40% 35%, #E0F2FE 0%, #38BDF8 35%, #0284C7 70%, #0369A1 100%)",
        };
      case "thinking":
        return {
          glow: "rgba(139, 92, 246, 0.4)",
          innerGlow: "rgba(99, 102, 241, 0.55)",
          core: "radial-gradient(circle at 40% 35%, #EDE9FE 0%, #A78BFA 35%, #7C3AED 70%, #4C1D95 100%)",
        };
      case "speaking":
        return {
          glow: "rgba(6, 182, 212, 0.45)",
          innerGlow: "rgba(14, 165, 233, 0.6)",
          core: "radial-gradient(circle at 40% 35%, #CFFAFE 0%, #22D3EE 35%, #0891B2 70%, #164E63 100%)",
        };
      case "loading":
        return {
          glow: "rgba(56, 189, 248, 0.35)",
          innerGlow: "rgba(124, 77, 255, 0.4)",
          core: "radial-gradient(circle at 40% 35%, #F0F9FF 0%, #38BDF8 40%, #1D4ED8 75%, #4338CA 100%)",
        };
      case "error":
        return {
          glow: "rgba(239, 68, 68, 0.35)",
          innerGlow: "rgba(220, 38, 38, 0.5)",
          core: "radial-gradient(circle at 40% 35%, #FEE2E2 0%, #F87171 40%, #DC2626 75%, #7F1D1D 100%)",
        };
      case "offline":
        return {
          glow: "rgba(100, 116, 139, 0.15)",
          innerGlow: "rgba(71, 85, 105, 0.25)",
          core: "radial-gradient(circle at 40% 35%, #CBD5E1 0%, #64748B 40%, #334155 75%, #1E293B 100%)",
        };
      case "idle":
      default:
        return {
          glow: "rgba(56, 189, 248, 0.3)",
          innerGlow: "rgba(139, 92, 246, 0.25)",
          core: "radial-gradient(circle at 40% 35%, #F0F9FF 0%, #38BDF8 35%, #0284C7 65%, #6D28D9 100%)",
        };
    }
  };

  const colors = getStateColors();

  return (
    <div
      onClick={onClick}
      className={`mikasa-orb ${className}`}
      style={{
        position: "relative",
        width: `${size}px`,
        height: `${size}px`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: onClick ? "pointer" : "default",
        userSelect: "none",
      }}
    >
      {/* Outer subtle breathing glow */}
      <div
        style={{
          position: "absolute",
          width: "100%",
          height: "100%",
          borderRadius: "50%",
          background: colors.glow,
          filter: "blur(28px)",
          opacity: 0.85,
          animation: "orb-breathing 4s ease-in-out infinite",
          pointerEvents: "none",
        }}
      />

      {/* Secondary accent ring / halo */}
      <div
        style={{
          position: "absolute",
          width: "82%",
          height: "82%",
          borderRadius: "50%",
          background: colors.innerGlow,
          filter: "blur(14px)",
          opacity: 0.9,
          pointerEvents: "none",
        }}
      />

      {/* Core 3D illuminated sphere */}
      <div
        style={{
          position: "relative",
          width: "68%",
          height: "68%",
          borderRadius: "50%",
          background: colors.core,
          boxShadow: "inset -6px -6px 14px rgba(0, 0, 0, 0.5), inset 4px 4px 10px rgba(255, 255, 255, 0.7), 0 0 20px rgba(56, 189, 248, 0.4)",
          transform: "translateZ(0)",
        }}
      />

      <style>{`
        @keyframes orb-breathing {
          0%, 100% {
            transform: scale(0.96);
            opacity: 0.65;
          }
          50% {
            transform: scale(1.06);
            opacity: 0.95;
          }
        }
      `}</style>
    </div>
  );
};
