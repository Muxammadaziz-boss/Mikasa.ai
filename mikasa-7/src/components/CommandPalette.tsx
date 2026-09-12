import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  HomeIcon,
  ChatIcon,
  MicIcon,
  CommandsIcon,
  MemoryIcon,
  SchedulerIcon,
  PluginsIcon,
  UserIcon,
  SearchIcon,
  CpuIcon,
  RefreshIcon,
  SparklesIcon,
  CloseIcon,
} from "./icons/Icons";
import { backendService } from "../services/backendService";

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (path: string, initialPrompt?: string) => void;
}

interface PaletteAction {
  id: string;
  title: string;
  subtitle: string;
  category: "Navigatsiya" | "Harakatlar" | "Tizim";
  icon: React.ReactNode;
  keywords: string[];
  run: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const actions: PaletteAction[] = useMemo(
    () => [
      // Navigatsiya
      {
        id: "nav-home",
        title: "Bosh sahifa",
        subtitle: "Asosiy boshqaruv paneli va tezkor vositalar",
        category: "Navigatsiya",
        icon: <HomeIcon size={18} color="#10B981" />,
        keywords: ["home", "bosh", "asosiy", "dastur"],
        run: () => onNavigate("/"),
      },
      {
        id: "nav-chat",
        title: "AI Suhbat",
        subtitle: "Mikasa AI bilan yozishish va savol-javob",
        category: "Navigatsiya",
        icon: <ChatIcon size={18} color="#3B82F6" />,
        keywords: ["chat", "suhbat", "yozish", "savol", "ai"],
        run: () => onNavigate("/chat"),
      },
      {
        id: "nav-voice",
        title: "Ovozli muloqot",
        subtitle: "Real-vaqt ovozli yordamchi va jonli orb",
        category: "Navigatsiya",
        icon: <MicIcon size={18} color="#8B5CF6" />,
        keywords: ["voice", "ovoz", "gapirish", "mikrofon", "tingla"],
        run: () => onNavigate("/voice"),
      },
      {
        id: "nav-commands",
        title: "Tizim buyruqlari",
        subtitle: "Ilovalarni ochish, boshqaruv va Windows vositalari",
        category: "Navigatsiya",
        icon: <CommandsIcon size={18} color="#F59E0B" />,
        keywords: ["commands", "buyruqlar", "dasturlar", "ilova", "windows"],
        run: () => onNavigate("/commands"),
      },
      {
        id: "nav-memory",
        title: "Agent xotirasi",
        subtitle: "Suhbatlar tarixi, profil va bilimlar ombori",
        category: "Navigatsiya",
        icon: <MemoryIcon size={18} color="#EC4899" />,
        keywords: ["memory", "xotira", "bilim", "tarix", "profil"],
        run: () => onNavigate("/memory"),
      },
      {
        id: "nav-scheduler",
        title: "Rejalashtiruvchi",
        subtitle: "Eslatmalar, taymerlar va avtomatlashtirish",
        category: "Navigatsiya",
        icon: <SchedulerIcon size={18} color="#14B8A6" />,
        keywords: ["scheduler", "rejalashtiruvchi", "eslatma", "soat", "vazifa"],
        run: () => onNavigate("/scheduler"),
      },
      {
        id: "nav-plugins",
        title: "Plaginlar va modullar",
        subtitle: "Agent qobiliyatlari, tashqi vositalar va integratsiyalar",
        category: "Navigatsiya",
        icon: <PluginsIcon size={18} color="#6366F1" />,
        keywords: ["plugins", "plaginlar", "tools", "vositalar"],
        run: () => onNavigate("/plugins"),
      },
      {
        id: "nav-account",
        title: "Hisob va sozlamalar",
        subtitle: "Foydalanuvchi ismi, ovoz turi, mavzular va parametrlar",
        category: "Navigatsiya",
        icon: <UserIcon size={18} color="#06B6D4" />,
        keywords: ["account", "hisob", "sozlamalar", "profil", "ovoz"],
        run: () => onNavigate("/account"),
      },

      // Harakatlar
      {
        id: "act-new-chat",
        title: "Yangi AI suhbat boshlash",
        subtitle: "Toza muloqot oynasini ochish",
        category: "Harakatlar",
        icon: <SparklesIcon size={18} color="#10B981" />,
        keywords: ["yangi", "toza", "new", "reset"],
        run: () => {
          onNavigate("/chat");
        },
      },
      {
        id: "act-system-specs",
        title: "Kompyuter parametrlarini so'rash",
        subtitle: "CPU, RAM, Disk va apparat ma'lumotlarini tahlil qilish",
        category: "Harakatlar",
        icon: <CpuIcon size={18} color="#3B82F6" />,
        keywords: ["parametr", "pc", "kompyuter", "specs", "ram", "cpu"],
        run: () => {
          onNavigate("/chat", "Kompyuterim parametrlarini aytib ber");
        },
      },

      // Tizim
      {
        id: "sys-restart-backend",
        title: "Python Backend xizmatini qayta yuklash",
        subtitle: "API server va agent jarayonlarini toza restart qilish",
        category: "Tizim",
        icon: <RefreshIcon size={18} color="#F97316" />,
        keywords: ["restart", "backend", "qayta", "server", "python"],
        run: () => {
          backendService.restartBackend();
        },
      },
    ],
    [onNavigate]
  );

  // Filter actions based on query
  const filteredActions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return actions;
    return actions.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.subtitle.toLowerCase().includes(q) ||
        a.keywords.some((k) => k.includes(q))
    );
  }, [actions, query]);

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Keyboard navigation inside palette
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev + 1 < filteredActions.length ? prev + 1 : 0
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev - 1 >= 0 ? prev - 1 : filteredActions.length - 1
        );
      } else if (e.key === "Enter") {
        e.preventDefault();
        const action = filteredActions[selectedIndex];
        if (action) {
          action.run();
          onClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filteredActions, selectedIndex, onClose]);

  // Scroll active item into view
  useEffect(() => {
    if (!listRef.current) return;
    const activeEl = listRef.current.querySelector<HTMLDivElement>(
      `[data-index="${selectedIndex}"]`
    );
    if (activeEl) {
      activeEl.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      className="palette-backdrop"
      onClick={onClose}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(6px)",
        WebkitBackdropFilter: "blur(6px)",
        zIndex: 1000,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        paddingTop: "12vh",
        animation: "fadeIn 0.15s ease-out",
      }}
    >
      <div
        className="palette-modal"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "90%",
          maxWidth: "600px",
          backgroundColor: "var(--bg-card, #13171F)",
          borderRadius: "14px",
          border: "1px solid var(--border-light, rgba(255, 255, 255, 0.12))",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          maxHeight: "70vh",
        }}
      >
        {/* Search header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "14px 18px",
            borderBottom: "1px solid var(--border, rgba(255, 255, 255, 0.08))",
            gap: "12px",
          }}
        >
          <SearchIcon size={20} color="var(--text-muted, #94A3B8)" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buyruq yoki sahifa qidirish (masalan: chat, ovoz, specs)..."
            style={{
              flex: 1,
              backgroundColor: "transparent",
              border: "none",
              outline: "none",
              color: "var(--text-main, #FFFFFF)",
              fontSize: "15px",
              fontWeight: 500,
            }}
          />
          {query ? (
            <button
              onClick={() => setQuery("")}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--text-muted, #94A3B8)",
                cursor: "pointer",
                padding: "4px",
                display: "flex",
                alignItems: "center",
              }}
            >
              <CloseIcon size={14} />
            </button>
          ) : (
            <kbd
              style={{
                fontSize: "11px",
                color: "var(--text-muted, #94A3B8)",
                backgroundColor: "rgba(255, 255, 255, 0.06)",
                padding: "3px 7px",
                borderRadius: "5px",
                border: "1px solid rgba(255, 255, 255, 0.1)",
              }}
            >
              ESC
            </kbd>
          )}
        </div>

        {/* Results List */}
        <div
          ref={listRef}
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "8px",
          }}
        >
          {filteredActions.length === 0 ? (
            <div
              style={{
                padding: "32px 16px",
                textAlign: "center",
                color: "var(--text-muted, #94A3B8)",
                fontSize: "14px",
              }}
            >
              Hech qanday mos keluvchi buyruq topilmadi.
            </div>
          ) : (
            filteredActions.map((action, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={action.id}
                  data-index={idx}
                  onClick={() => {
                    action.run();
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "10px 14px",
                    borderRadius: "8px",
                    cursor: "pointer",
                    gap: "14px",
                    backgroundColor: isSelected
                      ? "rgba(16, 185, 129, 0.12)"
                      : "transparent",
                    border: isSelected
                      ? "1px solid rgba(16, 185, 129, 0.25)"
                      : "1px solid transparent",
                    transition: "all 0.12s ease",
                  }}
                >
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      borderRadius: "8px",
                      backgroundColor: isSelected
                        ? "rgba(16, 185, 129, 0.2)"
                        : "rgba(255, 255, 255, 0.04)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                    }}
                  >
                    {action.icon}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        color: isSelected
                          ? "#FFFFFF"
                          : "var(--text-main, #E2E8F0)",
                        fontSize: "14px",
                        fontWeight: 600,
                      }}
                    >
                      {action.title}
                    </div>
                    <div
                      style={{
                        color: "var(--text-muted, #94A3B8)",
                        fontSize: "12px",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {action.subtitle}
                    </div>
                  </div>

                  <div
                    style={{
                      fontSize: "11px",
                      color: "var(--text-muted, #64748B)",
                      backgroundColor: "rgba(255, 255, 255, 0.03)",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      flexShrink: 0,
                    }}
                  >
                    {action.category}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "10px 18px",
            borderTop: "1px solid var(--border, rgba(255, 255, 255, 0.06))",
            backgroundColor: "rgba(0, 0, 0, 0.2)",
            fontSize: "12px",
            color: "var(--text-muted, #94A3B8)",
          }}
        >
          <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
            <span>
              <kbd style={kbdStyle}>↑</kbd> <kbd style={kbdStyle}>↓</kbd> Tanlash
            </span>
            <span>
              <kbd style={kbdStyle}>↵</kbd> Bajarish
            </span>
          </div>
          <div>Mikasa AI 7.x</div>
        </div>
      </div>
    </div>
  );
};

const kbdStyle: React.CSSProperties = {
  backgroundColor: "rgba(255, 255, 255, 0.08)",
  color: "#FFFFFF",
  borderRadius: "3px",
  padding: "2px 5px",
  fontSize: "10px",
  border: "1px solid rgba(255, 255, 255, 0.15)",
};
