import React from "react";

interface AvatarProps {
  initials?: string;
  size?: number;
  className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({
  initials = "U",
  size = 32,
  className = "",
}) => {
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
        background: "linear-gradient(135deg, #0284C7 0%, #1D4ED8 100%)",
        color: "#FFFFFF",
        fontWeight: 600,
        fontSize: `${Math.round(size * 0.4)}px`,
        letterSpacing: "0.02em",
        boxShadow: "0 2px 8px rgba(2, 132, 199, 0.3)",
        userSelect: "none",
        flexShrink: 0,
      }}
    >
      {initials}
    </div>
  );
};
