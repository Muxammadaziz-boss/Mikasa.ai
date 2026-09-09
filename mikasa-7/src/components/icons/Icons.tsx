import React from "react";

export interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export const SparklesIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <path
      d="M10.5 3L12.5 9.5L19 11.5L12.5 13.5L10.5 20L8.5 13.5L2 11.5L8.5 9.5L10.5 3Z"
      fill={color}
    />
    <circle cx="18.5" cy="5.5" r="1.8" fill={color} />
  </svg>
);

export const HomeIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M3 9.5L12 3L21 9.5V20C21 20.6 20.6 21 20 21H15V14H9V21H4C3.4 21 3 20.6 3 20V9.5Z" />
  </svg>
);

export const MicIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="9" y="2.5" width="6" height="11" rx="3" />
    <path d="M5.5 10C5.5 13.6 8.4 16.5 12 16.5C15.6 16.5 18.5 13.6 18.5 10" />
    <line x1="12" y1="16.5" x2="12" y2="20.5" />
    <line x1="8" y1="20.5" x2="16" y2="20.5" />
  </svg>
);

export const ChatIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M3 5.5C3 4.4 3.9 3.5 5 3.5H19C20.1 3.5 21 4.4 21 5.5V15.5C21 16.6 20.1 17.5 19 17.5H7L3 21V5.5Z" />
  </svg>
);

export const CommandsIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
    <polygon points="13 2.5 6.5 12 12 12 11 21.5 17.5 11 12.5 11 13 2.5" fill={color} />
  </svg>
);

export const MemoryIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="5.5" y="5.5" width="13" height="13" rx="2" />
    <rect x="9" y="9" width="6" height="6" fill={color} />
    <line x1="9" y1="2.5" x2="9" y2="5.5" />
    <line x1="15" y1="2.5" x2="15" y2="5.5" />
    <line x1="9" y1="18.5" x2="9" y2="21.5" />
    <line x1="15" y1="18.5" x2="15" y2="21.5" />
    <line x1="2.5" y1="9" x2="5.5" y2="9" />
    <line x1="2.5" y1="15" x2="5.5" y2="15" />
    <line x1="18.5" y1="9" x2="21.5" y2="9" />
    <line x1="18.5" y1="15" x2="21.5" y2="15" />
  </svg>
);

export const SchedulerIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="1.2" fill={color} />
    <line x1="12" y1="12" x2="12" y2="7.5" />
    <line x1="12" y1="12" x2="16" y2="12" />
  </svg>
);

export const PluginsIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="6" y="6" width="12" height="12" rx="2" />
    <circle cx="12" cy="6" r="2" fill={color} />
    <circle cx="18" cy="12" r="2" fill={color} />
  </svg>
);

export const UserIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="12" cy="7" r="4" />
    <path d="M5.5 20C5.5 16.5 8.5 14 12 14C15.5 14 18.5 16.5 18.5 20" />
  </svg>
);

export const MinimizeIcon: React.FC<IconProps> = ({ size = 14, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" className={className}>
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

export const MaximizeIcon: React.FC<IconProps> = ({ size = 14, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="5.5" y="5.5" width="13" height="13" rx="1.5" />
  </svg>
);

export const RestoreIcon: React.FC<IconProps> = ({ size = 14, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M8.5 5.5H18.5V15.5" />
    <rect x="5.5" y="8.5" width="10" height="10" rx="1.5" />
  </svg>
);

export const CloseIcon: React.FC<IconProps> = ({ size = 14, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" className={className}>
    <line x1="6" y1="6" x2="18" y2="18" />
    <line x1="18" y1="6" x2="6" y2="18" />
  </svg>
);

export const ChevronRightIcon: React.FC<IconProps> = ({ size = 14, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

export const CircleDotIcon: React.FC<IconProps> = ({ size = 8, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 10 10" fill="none" className={className}>
    <circle cx="5" cy="5" r="4" fill={color} />
  </svg>
);

export const AttachIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
  </svg>
);

export const SendIcon: React.FC<IconProps> = ({ size = 16, color = "currentColor", className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);
