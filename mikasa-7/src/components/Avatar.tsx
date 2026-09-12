import React from "react";

export interface AvatarProps {
  initials?: string;
  size?: number;
  className?: string;
  avatarStyle?: string;
}

const AVATAR_GRADIENTS: Record<string, string> = {
  emerald: "linear-gradient(135deg, #059669 0%, #10B981 100%)",
  blue: "linear-gradient(135deg, #0284C7 0%, #1D4ED8 100%)",
  purple: "linear-gradient(135deg, #7C3AED 0%, #9333EA 100%)",
  cyan: "linear-gradient(135deg, #0891B2 0%, #06B6D4 100%)",
  gold: "linear-gradient(135deg, #D97706 0%, #F59E0B 100%)",
  rose: "linear-gradient(135deg, #E11D48 0%, #F43F5E 100%)",
};

export const Avatar: React.FC<AvatarProps> = ({
  initials = "U",
  size = 32,
  className = "",
  avatarStyle = "emerald",
}) => {
  const gradient = AVATAR_GRADIENTS[avatarStyle] || AVATAR_GRADIENTS.emerald;

  return (
    <div
      className={`user-avatar ${className}`}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: gradient,
        color: "#FFFFFF",
        fontWeight: 600,
        fontSize: `${Math.round(size * 0.4)}px`,
        letterSpacing: "0.02em",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.3)",
        userSelect: "none",
        flexShrink: 0,
      }}
    >
      {initials}
    </div>
  );
};
