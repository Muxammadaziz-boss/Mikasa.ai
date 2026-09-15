import React from "react";

export type OrbState =
  | "idle"
  | "listening"
  | "thinking"
  | "planning"
  | "acting"
  | "verifying"
  | "replanning"
  | "speaking"
  | "completed"
  | "error"
  // Backwards compatibility aliases:
  | "loading"
  | "offline";

interface MikasaOrbProps {
  size?: number | string;
  state?: OrbState;
  audioLevel?: number; // 0.0 to 1.0 (for audio reactivity)
  className?: string;
  onClick?: () => void;
}

export const MikasaOrb: React.FC<MikasaOrbProps> = ({
  size = 190,
  state = "idle",
  audioLevel = 0,
  className = "",
  onClick,
}) => {
  // Normalize legacy states
  const normState: OrbState =
    state === "loading" ? "thinking" : state === "offline" ? "error" : state;

  const getStateColors = () => {
    switch (normState) {
      case "listening":
        return {
          glow: "rgba(56, 189, 248, 0.55)",
          innerGlow: "rgba(14, 165, 233, 0.7)",
          ring: "rgba(56, 189, 248, 0.4)",
          core: "radial-gradient(circle at 38% 32%, #F0F9FF 0%, #38BDF8 35%, #0284C7 70%, #0369A1 100%)",
          shadow: "0 0 35px rgba(56, 189, 248, 0.6)",
        };
      case "thinking":
        return {
          glow: "rgba(168, 85, 247, 0.5)",
          innerGlow: "rgba(139, 92, 246, 0.65)",
          ring: "rgba(192, 132, 252, 0.4)",
          core: "radial-gradient(circle at 38% 32%, #FAF5FF 0%, #C084FC 35%, #8B5CF6 70%, #581C87 100%)",
          shadow: "0 0 35px rgba(168, 85, 247, 0.55)",
        };
      case "planning":
        return {
          glow: "rgba(99, 102, 241, 0.5)",
          innerGlow: "rgba(79, 70, 229, 0.65)",
          ring: "rgba(129, 140, 248, 0.5)",
          core: "radial-gradient(circle at 38% 32%, #EEF2FF 0%, #818CF8 35%, #4F46E5 70%, #312E81 100%)",
          shadow: "0 0 35px rgba(99, 102, 241, 0.55)",
        };
      case "acting":
        return {
          glow: "rgba(14, 165, 233, 0.6)",
          innerGlow: "rgba(34, 211, 238, 0.7)",
          ring: "rgba(56, 189, 248, 0.55)",
          core: "radial-gradient(circle at 38% 32%, #ECFEFF 0%, #22D3EE 35%, #0284C7 70%, #0F172A 100%)",
          shadow: "0 0 42px rgba(34, 211, 238, 0.7)",
        };
      case "verifying":
        return {
          glow: "rgba(20, 184, 166, 0.55)",
          innerGlow: "rgba(13, 148, 136, 0.7)",
          ring: "rgba(45, 212, 191, 0.45)",
          core: "radial-gradient(circle at 38% 32%, #F0FDFA 0%, #2DD4BF 35%, #0D9488 70%, #134E4A 100%)",
          shadow: "0 0 35px rgba(20, 184, 166, 0.6)",
        };
      case "replanning":
        return {
          glow: "rgba(245, 158, 11, 0.55)",
          innerGlow: "rgba(217, 119, 6, 0.7)",
          ring: "rgba(251, 191, 36, 0.5)",
          core: "radial-gradient(circle at 38% 32%, #FFFBEB 0%, #FBBF24 35%, #D97706 70%, #78350F 100%)",
          shadow: "0 0 38px rgba(245, 158, 11, 0.65)",
        };
      case "speaking":
        return {
          glow: "rgba(6, 182, 212, 0.55)",
          innerGlow: "rgba(14, 165, 233, 0.7)",
          ring: "rgba(34, 211, 238, 0.45)",
          core: "radial-gradient(circle at 38% 32%, #CFFAFE 0%, #22D3EE 35%, #0891B2 70%, #164E63 100%)",
          shadow: "0 0 40px rgba(6, 182, 212, 0.65)",
        };
      case "completed":
        return {
          glow: "rgba(16, 185, 129, 0.5)",
          innerGlow: "rgba(5, 150, 105, 0.65)",
          ring: "rgba(52, 211, 153, 0.4)",
          core: "radial-gradient(circle at 38% 32%, #ECFDF5 0%, #34D19E 35%, #059669 70%, #064E3B 100%)",
          shadow: "0 0 32px rgba(16, 185, 129, 0.55)",
        };
      case "error":
        return {
          glow: "rgba(239, 68, 68, 0.45)",
          innerGlow: "rgba(220, 38, 38, 0.6)",
          ring: "rgba(248, 113, 113, 0.4)",
          core: "radial-gradient(circle at 38% 32%, #FEF2F2 0%, #F87171 35%, #DC2626 70%, #7F1D1D 100%)",
          shadow: "0 0 32px rgba(239, 68, 68, 0.55)",
        };
      case "idle":
      default:
        return {
          glow: "rgba(56, 189, 248, 0.35)",
          innerGlow: "rgba(139, 92, 246, 0.35)",
          ring: "rgba(125, 211, 252, 0.25)",
          core: "radial-gradient(circle at 38% 32%, #F0F9FF 0%, #38BDF8 35%, #0284C7 68%, #4C1D95 100%)",
          shadow: "0 0 28px rgba(56, 189, 248, 0.4)",
        };
    }
  };

  const colors = getStateColors();
  const audioScale = Math.min(1 + audioLevel * 0.25, 1.3);

  return (
    <div
      onClick={onClick}
      className={`mikasa-orb-wrapper ${className}`}
      role="status"
      aria-label={`Mikasa AI Holati: ${normState}`}
      style={{
        position: "relative",
        width: typeof size === "number" ? `${size}px` : size,
        height: typeof size === "number" ? `${size}px` : size,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: onClick ? "pointer" : "default",
        userSelect: "none",
        transition: "transform 0.2s ease-out",
        transform: `scale(${audioScale})`,
      }}
    >
      {/* Outer ambient glow halo */}
      <div
        style={{
          position: "absolute",
          width: "120%",
          height: "120%",
          borderRadius: "50%",
          background: colors.glow,
          filter: "blur(32px)",
          opacity: normState === "listening" || normState === "speaking" ? 0.95 : 0.78,
          animation:
            normState === "listening"
              ? "orb-pulse-fast 1.4s ease-in-out infinite"
              : normState === "acting"
              ? "orb-kinetic-acting 2s ease-in-out infinite"
              : "orb-breathing 4s ease-in-out infinite",
          pointerEvents: "none",
        }}
      />

      {/* Orbital / Activity Accent Rings */}
      {(normState === "planning" || normState === "thinking" || normState === "acting" || normState === "replanning") && (
        <div
          style={{
            position: "absolute",
            width: "92%",
            height: "92%",
            borderRadius: "50%",
            border: `1.5px dashed ${colors.ring}`,
            animation:
              normState === "replanning"
                ? "orb-replan-shift 3s ease-in-out infinite"
                : normState === "planning"
                ? "orb-orbital-ring 8s linear infinite"
                : "orb-particle-spin 6s linear infinite",
            pointerEvents: "none",
          }}
        />
      )}

      {/* Secondary accent halo */}
      <div
        style={{
          position: "absolute",
          width: "82%",
          height: "82%",
          borderRadius: "50%",
          background: colors.innerGlow,
          filter: "blur(16px)",
          opacity: 0.85,
          pointerEvents: "none",
        }}
      />

      {/* Core illuminated Sphere */}
      <div
        style={{
          position: "relative",
          width: "68%",
          height: "68%",
          borderRadius: "50%",
          background: colors.core,
          boxShadow: `inset -7px -7px 16px rgba(0, 0, 0, 0.55), inset 4px 4px 12px rgba(255, 255, 255, 0.7), ${colors.shadow}`,
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* State-specific overlays */}
        {normState === "verifying" && (
          <div
            style={{
              position: "absolute",
              width: "100%",
              height: "3px",
              background: "rgba(255, 255, 255, 0.85)",
              boxShadow: "0 0 10px #2DD4BF, 0 0 20px #2DD4BF",
              animation: "orb-scan-sweep 1.8s ease-in-out infinite",
            }}
          />
        )}

        {normState === "speaking" && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "3px",
              height: "28px",
              zIndex: 3,
            }}
          >
            {[0.8, 1.4, 1.8, 1.1, 0.6].map((rate, i) => (
              <span
                key={i}
                style={{
                  width: "3px",
                  height: "12px",
                  borderRadius: "2px",
                  background: "rgba(255, 255, 255, 0.9)",
                  boxShadow: "0 0 6px rgba(255, 255, 255, 0.8)",
                  animation: `wave-bounce ${0.6 / rate}s ease-in-out infinite alternate`,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
export default MikasaOrb;
