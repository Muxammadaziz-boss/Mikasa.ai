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
          ring2: "rgba(168, 85, 247, 0.3)",
          ring3: "rgba(236, 72, 153, 0.25)",
          core: "radial-gradient(circle at 38% 32%, #F0F9FF 0%, #38BDF8 35%, #0284C7 70%, #0369A1 100%)",
          shadow: "0 0 45px rgba(56, 189, 248, 0.7)",
          particleColor: "#38BDF8",
        };
      case "thinking":
        return {
          glow: "rgba(168, 85, 247, 0.5)",
          innerGlow: "rgba(139, 92, 246, 0.65)",
          ring: "rgba(192, 132, 252, 0.4)",
          ring2: "rgba(99, 102, 241, 0.3)",
          ring3: "rgba(56, 189, 248, 0.2)",
          core: "radial-gradient(circle at 38% 32%, #FAF5FF 0%, #C084FC 35%, #8B5CF6 70%, #581C87 100%)",
          shadow: "0 0 40px rgba(168, 85, 247, 0.6)",
          particleColor: "#C084FC",
        };
      case "planning":
        return {
          glow: "rgba(99, 102, 241, 0.5)",
          innerGlow: "rgba(79, 70, 229, 0.65)",
          ring: "rgba(129, 140, 248, 0.5)",
          ring2: "rgba(168, 85, 247, 0.35)",
          ring3: "rgba(56, 189, 248, 0.25)",
          core: "radial-gradient(circle at 38% 32%, #EEF2FF 0%, #818CF8 35%, #4F46E5 70%, #312E81 100%)",
          shadow: "0 0 40px rgba(99, 102, 241, 0.6)",
          particleColor: "#818CF8",
        };
      case "acting":
        return {
          glow: "rgba(14, 165, 233, 0.6)",
          innerGlow: "rgba(34, 211, 238, 0.7)",
          ring: "rgba(56, 189, 248, 0.55)",
          ring2: "rgba(6, 182, 212, 0.4)",
          ring3: "rgba(99, 102, 241, 0.3)",
          core: "radial-gradient(circle at 38% 32%, #ECFEFF 0%, #22D3EE 35%, #0284C7 70%, #0F172A 100%)",
          shadow: "0 0 50px rgba(34, 211, 238, 0.75)",
          particleColor: "#22D3EE",
        };
      case "verifying":
        return {
          glow: "rgba(20, 184, 166, 0.55)",
          innerGlow: "rgba(13, 148, 136, 0.7)",
          ring: "rgba(45, 212, 191, 0.45)",
          ring2: "rgba(16, 185, 129, 0.35)",
          ring3: "rgba(56, 189, 248, 0.2)",
          core: "radial-gradient(circle at 38% 32%, #F0FDFA 0%, #2DD4BF 35%, #0D9488 70%, #134E4A 100%)",
          shadow: "0 0 38px rgba(20, 184, 166, 0.65)",
          particleColor: "#2DD4BF",
        };
      case "replanning":
        return {
          glow: "rgba(245, 158, 11, 0.55)",
          innerGlow: "rgba(217, 119, 6, 0.7)",
          ring: "rgba(251, 191, 36, 0.5)",
          ring2: "rgba(236, 72, 153, 0.35)",
          ring3: "rgba(168, 85, 247, 0.3)",
          core: "radial-gradient(circle at 38% 32%, #FFFBEB 0%, #FBBF24 35%, #D97706 70%, #78350F 100%)",
          shadow: "0 0 42px rgba(245, 158, 11, 0.7)",
          particleColor: "#FBBF24",
        };
      case "speaking":
        return {
          glow: "rgba(6, 182, 212, 0.55)",
          innerGlow: "rgba(14, 165, 233, 0.7)",
          ring: "rgba(34, 211, 238, 0.45)",
          ring2: "rgba(56, 189, 248, 0.35)",
          ring3: "rgba(139, 92, 246, 0.25)",
          core: "radial-gradient(circle at 38% 32%, #CFFAFE 0%, #22D3EE 35%, #0891B2 70%, #164E63 100%)",
          shadow: "0 0 45px rgba(6, 182, 212, 0.7)",
          particleColor: "#22D3EE",
        };
      case "completed":
        return {
          glow: "rgba(16, 185, 129, 0.5)",
          innerGlow: "rgba(5, 150, 105, 0.65)",
          ring: "rgba(52, 211, 153, 0.4)",
          ring2: "rgba(16, 185, 129, 0.3)",
          ring3: "rgba(6, 182, 212, 0.2)",
          core: "radial-gradient(circle at 38% 32%, #ECFDF5 0%, #34D19E 35%, #059669 70%, #064E3B 100%)",
          shadow: "0 0 35px rgba(16, 185, 129, 0.6)",
          particleColor: "#34D399",
        };
      case "error":
        return {
          glow: "rgba(239, 68, 68, 0.45)",
          innerGlow: "rgba(220, 38, 38, 0.6)",
          ring: "rgba(248, 113, 113, 0.4)",
          ring2: "rgba(239, 68, 68, 0.3)",
          ring3: "rgba(245, 158, 11, 0.2)",
          core: "radial-gradient(circle at 38% 32%, #FEF2F2 0%, #F87171 35%, #DC2626 70%, #7F1D1D 100%)",
          shadow: "0 0 35px rgba(239, 68, 68, 0.6)",
          particleColor: "#F87171",
        };
      case "idle":
      default:
        return {
          glow: "rgba(168, 85, 247, 0.35)",
          innerGlow: "rgba(56, 189, 248, 0.35)",
          ring: "rgba(129, 140, 248, 0.3)",
          ring2: "rgba(192, 132, 252, 0.25)",
          ring3: "rgba(56, 189, 248, 0.2)",
          core: "radial-gradient(circle at 45% 38%, #312E81 0%, #4C1D95 35%, #1E40AF 70%, #0F172A 100%)",
          shadow: "0 0 45px rgba(168, 85, 247, 0.5), inset 0 0 24px rgba(56, 189, 248, 0.45)",
          particleColor: "#C084FC",
        };
    }
  };

  const colors = getStateColors();
  const audioScale = Math.min(1 + audioLevel * 0.22, 1.28);

  // Ring animation speeds per state
  const getRingAnimation = (ringIdx: number) => {
    const base = [
      { idle: "orb-ring-slow 18s linear infinite", listening: "orb-ring-fast 4s linear infinite", thinking: "orb-ring-slow 12s linear infinite", planning: "orb-ring-structured 10s linear infinite", acting: "orb-ring-fast 3s linear infinite", speaking: "orb-ring-flow 6s ease-in-out infinite", verifying: "orb-ring-slow 8s linear infinite", replanning: "orb-replan-shift 3s ease-in-out infinite", completed: "orb-ring-slow 20s linear infinite", error: "orb-ring-pulse 2s ease-in-out infinite" },
      { idle: "orb-ring-slow 25s linear infinite reverse", listening: "orb-ring-fast 5s linear infinite reverse", thinking: "orb-ring-slow 16s linear infinite reverse", planning: "orb-ring-structured 14s linear infinite reverse", acting: "orb-ring-fast 4s linear infinite reverse", speaking: "orb-ring-flow 8s ease-in-out infinite reverse", verifying: "orb-ring-slow 10s linear infinite reverse", replanning: "orb-replan-shift 4s ease-in-out infinite reverse", completed: "orb-ring-slow 28s linear infinite reverse", error: "orb-ring-pulse 2.5s ease-in-out infinite" },
      { idle: "orb-ring-slow 30s linear infinite", listening: "orb-ring-fast 6s linear infinite", thinking: "orb-ring-slow 20s linear infinite", planning: "orb-ring-structured 18s linear infinite", acting: "orb-ring-fast 5s linear infinite", speaking: "orb-ring-flow 10s ease-in-out infinite", verifying: "orb-ring-slow 14s linear infinite", replanning: "orb-replan-shift 5s ease-in-out infinite", completed: "orb-ring-slow 35s linear infinite", error: "orb-ring-pulse 3s ease-in-out infinite" },
    ];
    const key = normState as keyof typeof base[0];
    return base[ringIdx]?.[key] || base[ringIdx]?.idle || "none";
  };

  // Particle positions (8 particles)
  const particles = [
    { angle: 0, dist: 42, delay: 0 },
    { angle: 45, dist: 44, delay: 0.3 },
    { angle: 90, dist: 40, delay: 0.6 },
    { angle: 135, dist: 46, delay: 0.9 },
    { angle: 180, dist: 41, delay: 1.2 },
    { angle: 225, dist: 45, delay: 1.5 },
    { angle: 270, dist: 43, delay: 1.8 },
    { angle: 315, dist: 44, delay: 2.1 },
  ];

  const showMicIcon = normState === "idle" || normState === "listening";
  const isActive = normState !== "idle" && normState !== "completed";

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
        transition: "transform 0.25s ease-out",
        transform: `scale(${audioScale})`,
      }}
    >
      {/* ── Layer 1: Outer ambient glow halo ── */}
      <div
        style={{
          position: "absolute",
          width: "130%",
          height: "130%",
          borderRadius: "50%",
          background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
          filter: "blur(28px)",
          opacity: normState === "listening" || normState === "speaking" ? 0.95 : 0.7,
          animation:
            normState === "listening"
              ? "orb-pulse-fast 1.2s ease-in-out infinite"
              : normState === "acting"
              ? "orb-kinetic-acting 2s ease-in-out infinite"
              : "orb-breathing 4s ease-in-out infinite",
          pointerEvents: "none",
        }}
      />

      {/* ── Layer 2: Orbital Ring 1 (outermost) ── */}
      <div
        style={{
          position: "absolute",
          width: "96%",
          height: "96%",
          borderRadius: "50%",
          border: `1px solid ${colors.ring}`,
          animation: getRingAnimation(0),
          pointerEvents: "none",
          opacity: isActive ? 0.9 : 0.4,
          transition: "opacity 0.5s ease",
        }}
      />

      {/* ── Layer 3: Orbital Ring 2 (tilted) ── */}
      <div
        style={{
          position: "absolute",
          width: "88%",
          height: "88%",
          borderRadius: "50%",
          border: `1px dashed ${colors.ring2}`,
          transform: "rotateX(60deg) rotateZ(30deg)",
          animation: getRingAnimation(1),
          pointerEvents: "none",
          opacity: isActive ? 0.8 : 0.3,
          transition: "opacity 0.5s ease",
        }}
      />

      {/* ── Layer 4: Orbital Ring 3 (perpendicular) ── */}
      <div
        style={{
          position: "absolute",
          width: "82%",
          height: "82%",
          borderRadius: "50%",
          border: `1px dotted ${colors.ring3}`,
          transform: "rotateX(75deg) rotateZ(-45deg)",
          animation: getRingAnimation(2),
          pointerEvents: "none",
          opacity: isActive ? 0.7 : 0.2,
          transition: "opacity 0.5s ease",
        }}
      />

      {/* ── Layer 5: Floating Particles ── */}
      {particles.map((p, i) => {
        const rad = (p.angle * Math.PI) / 180;
        const x = Math.cos(rad) * p.dist;
        const y = Math.sin(rad) * p.dist;
        const particleSize = normState === "listening" ? 3 + audioLevel * 3 : 2;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              width: `${particleSize}px`,
              height: `${particleSize}px`,
              borderRadius: "50%",
              backgroundColor: colors.particleColor,
              boxShadow: `0 0 6px ${colors.particleColor}`,
              left: `calc(50% + ${x}px - ${particleSize / 2}px)`,
              top: `calc(50% + ${y}px - ${particleSize / 2}px)`,
              opacity: isActive ? 0.8 : 0.35,
              animation: `orb-particle-float 3s ease-in-out ${p.delay}s infinite`,
              pointerEvents: "none",
              transition: "width 0.2s, height 0.2s, opacity 0.5s",
            }}
          />
        );
      })}

      {/* ── Layer 6: Inner glow halo ── */}
      <div
        style={{
          position: "absolute",
          width: "76%",
          height: "76%",
          borderRadius: "50%",
          background: `radial-gradient(circle, ${colors.innerGlow} 0%, transparent 70%)`,
          filter: "blur(14px)",
          opacity: 0.85,
          pointerEvents: "none",
        }}
      />

      {/* ── Layer 7: Glass sphere shell ── */}
      <div
        style={{
          position: "absolute",
          width: "70%",
          height: "70%",
          borderRadius: "50%",
          background: "linear-gradient(135deg, rgba(255,255,255,0.08) 0%, transparent 50%, rgba(255,255,255,0.03) 100%)",
          border: "1px solid rgba(255,255,255,0.12)",
          pointerEvents: "none",
        }}
      />

      {/* ── Layer 8: Core illuminated Sphere ── */}
      <div
        style={{
          position: "relative",
          width: "64%",
          height: "64%",
          borderRadius: "50%",
          background: colors.core,
          boxShadow: `inset -7px -7px 18px rgba(0, 0, 0, 0.55), inset 4px 4px 14px rgba(255, 255, 255, 0.65), ${colors.shadow}`,
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 2,
        }}
      >
        {/* Verifying scan sweep */}
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

        {/* Speaking waveform bars */}
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

        {/* Microphone Icon (idle/listening) */}
        {showMicIcon && (
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke={normState === "listening" ? "#FFFFFF" : "rgba(255,255,255,0.7)"}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              zIndex: 3,
              filter: normState === "listening" ? "drop-shadow(0 0 8px rgba(255,255,255,0.6))" : "none",
              animation: normState === "listening" ? "orb-mic-pulse 1.5s ease-in-out infinite" : "none",
            }}
          >
            <rect x="9" y="1" width="6" height="11" rx="3" />
            <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        )}

        {/* Thinking / Planning icon */}
        {(normState === "thinking" || normState === "planning") && (
          <div
            style={{
              width: "20px",
              height: "20px",
              border: "2px solid rgba(255,255,255,0.8)",
              borderTopColor: "transparent",
              borderRadius: "50%",
              animation: "orb-particle-spin 1s linear infinite",
              zIndex: 3,
            }}
          />
        )}

        {/* Error icon */}
        {normState === "error" && (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ zIndex: 3 }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        )}

        {/* Completed checkmark */}
        {normState === "completed" && (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ zIndex: 3 }}>
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )}
      </div>
    </div>
  );
};
export default MikasaOrb;
