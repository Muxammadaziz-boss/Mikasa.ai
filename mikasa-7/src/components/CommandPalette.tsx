// ========== CommandPalette.tsx ==========
// Mikasa AI 7.1.0 — Phase 16: Global Command Palette (Ctrl+K)
// Qidiruv, Navigatsiya, Tezkor Amallar va Tizim Asboblarini to'g'ridan-to'g'ri bajarish

import React, { useState, useEffect, useRef, useMemo } from "react";
import {
  HomeIcon,
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
  PlayIcon,
  CheckIcon,
  TrashIcon,
  CalculatorIcon,
  FolderIcon,
  GlobeIcon,
  DollarIcon,
  VolumeIcon,
  TerminalIcon,
} from "./icons/Icons";
import {
  backendService,
  CommandItem,
} from "../services/backendService";

export interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (path: string, initialPrompt?: string) => void;
}

interface PaletteItem {
  id: string;
  title: string;
  subtitle: string;
  category: "Navigatsiya" | "Tezkor Amallar" | "Tizim Asboblari";
  icon: React.ReactNode;
  keywords: string[];
  isTool?: boolean;
  run: () => Promise<string | void> | void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [registryTools, setRegistryTools] = useState<CommandItem[]>([]);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<{ id: string; text: string } | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Registry buyruqlarini yuklash
  useEffect(() => {
    let mounted = true;
    const fetchTools = async () => {
      try {
        const resp = await backendService.getCommands();
        if (mounted && resp.ok && resp.commands) {
          setRegistryTools(resp.commands);
        }
      } catch {
        // ignore
      }
    };
    if (isOpen) {
      fetchTools();
    }
    return () => {
      mounted = false;
    };
  }, [isOpen]);

  // Yordamchi SVG ikonkalarini aniqlash
  const getToolIcon = (cmd: CommandItem): React.ReactNode => {
    const id = (cmd.tool_name || cmd.id || "").toLowerCase();
    const cat = (cmd.category || "").toLowerCase();

    if (id.includes("calc") || id.includes("hisob")) {
      return <CalculatorIcon size={18} color="#10B981" />;
    }
    if (id.includes("file") || id.includes("fayl") || id.includes("folder")) {
      return <FolderIcon size={18} color="#3B82F6" />;
    }
    if (id.includes("web") || id.includes("browser") || id.includes("sayt")) {
      return <GlobeIcon size={18} color="#06B6D4" />;
    }
    if (id.includes("currency") || id.includes("valyuta")) {
      return <DollarIcon size={18} color="#F59E0B" />;
    }
    if (id.includes("system") || id.includes("tizim") || id.includes("specs") || id.includes("cpu")) {
      return <CpuIcon size={18} color="#8B5CF6" />;
    }
    if (id.includes("audio") || id.includes("ovoz") || id.includes("volume")) {
      return <VolumeIcon size={18} color="#EC4899" />;
    }
    if (cat.includes("ilova") || id.includes("app")) {
      return <TerminalIcon size={18} color="#14B8A6" />;
    }
    return <CommandsIcon size={18} color="#F59E0B" />;
  };

  // Standart Harakatlar va Navigatsiya
  const baseActions: PaletteItem[] = useMemo(
    () => [
      // 1. Navigatsiya
      {
        id: "nav-new-chat",
        title: "Yangi AI Suhbat (New Chat)",
        subtitle: "Toza muloqot oynasini ochish va yangi mavzu boshlash",
        category: "Navigatsiya",
        icon: <SparklesIcon size={18} color="#10B981" />,
        keywords: ["new", "chat", "yangi", "suhbat", "muloqot", "toza"],
        run: () => {
          onNavigate("/chat");
          onClose();
        },
      },
      {
        id: "nav-voice",
        title: "Ovozli Muloqot (Voice Mode)",
        subtitle: "Mikasa bilan real-vaqt ovozli jonli suhbat orb oynasi",
        category: "Navigatsiya",
        icon: <MicIcon size={18} color="#8B5CF6" />,
        keywords: ["voice", "ovoz", "gapirish", "tinglash", "orb", "mikrofon"],
        run: () => {
          onNavigate("/voice");
          onClose();
        },
      },
      {
        id: "nav-commands",
        title: "Buyruqlar Markazi (Commands Center)",
        subtitle: "Barcha 128+ mahalliy buyruqlar va tizim asboblari katalogi",
        category: "Navigatsiya",
        icon: <CommandsIcon size={18} color="#F59E0B" />,
        keywords: ["commands", "buyruqlar", "dasturlar", "ilova", "tizim"],
        run: () => {
          onNavigate("/commands");
          onClose();
        },
      },
      {
        id: "nav-memory",
        title: "Agent Xotirasi (Memory & Knowledge)",
        subtitle: "Profil, saqlangan bilimlar va suhbatlar tarixi fazosi",
        category: "Navigatsiya",
        icon: <MemoryIcon size={18} color="#EC4899" />,
        keywords: ["memory", "xotira", "bilim", "tarix", "profil", "kontekst"],
        run: () => {
          onNavigate("/memory");
          onClose();
        },
      },
      {
        id: "nav-scheduler",
        title: "Rejalashtiruvchi (Scheduler & Reminders)",
        subtitle: "Vazifalar xronologiyasi, eslatmalar va avtomatlashtirish",
        category: "Navigatsiya",
        icon: <SchedulerIcon size={18} color="#14B8A6" />,
        keywords: ["scheduler", "rejalashtiruvchi", "eslatma", "soat", "taymer", "vazifa"],
        run: () => {
          onNavigate("/scheduler");
          onClose();
        },
      },
      {
        id: "nav-plugins",
        title: "Plaginlar Markazi (Plugin Center)",
        subtitle: "Kengaytmalar, tashqi vositalar va integratsiyalarni boshqarish",
        category: "Navigatsiya",
        icon: <PluginsIcon size={18} color="#6366F1" />,
        keywords: ["plugins", "plaginlar", "tools", "modullar", "integratsiya"],
        run: () => {
          onNavigate("/plugins");
          onClose();
        },
      },
      {
        id: "nav-account",
        title: "Hisob va Sozlamalar (Account & Settings)",
        subtitle: "Profil, ovoz tanlovi, Gemini AI modeli, tashqi ko'rinish va maxfiylik",
        category: "Navigatsiya",
        icon: <UserIcon size={18} color="#06B6D4" />,
        keywords: ["account", "hisob", "sozlamalar", "settings", "profil", "tema", "ovoz"],
        run: () => {
          onNavigate("/account");
          onClose();
        },
      },
      {
        id: "nav-home",
        title: "Bosh Sahifa (Home)",
        subtitle: "Asosiy vitrina paneli va tezkor ilovalar",
        category: "Navigatsiya",
        icon: <HomeIcon size={18} color="#10B981" />,
        keywords: ["home", "bosh", "asosiy", "dashboard"],
        run: () => {
          onNavigate("/");
          onClose();
        },
      },

      // 2. Tezkor Amallar
      {
        id: "act-pc-specs",
        title: "Kompyuter Parametrlarini Tahlil Qilish",
        subtitle: "CPU, RAM, Disk va operatsion tizim holatini bilish",
        category: "Tezkor Amallar",
        icon: <CpuIcon size={18} color="#3B82F6" />,
        keywords: ["specs", "parametr", "ram", "cpu", "kompyuter", "tizim"],
        run: () => {
          onNavigate("/chat", "Kompyuterim parametrlarini aytib ber");
          onClose();
        },
      },
      {
        id: "act-voice-test",
        title: "Mikasa Ovozini Sinash",
        subtitle: "Joriy tanlangan ovoz bilan salomlashuvni eshittirish",
        category: "Tezkor Amallar",
        icon: <PlayIcon size={18} color="#10B981" />,
        keywords: ["ovoz", "sinash", "test", "gapir", "audio"],
        run: async () => {
          await backendService.speakText("Assalomu alaykum! Mikasa AI buyruqlar paneli orqali tayyor.");
          return "Ovozli salomlashuv yangradi";
        },
      },
      {
        id: "act-clear-history",
        title: "Suhbatlar Tarixini Tozalash",
        subtitle: "Barcha xotiradagi suhbatlarni xavfsiz tozalash",
        category: "Tezkor Amallar",
        icon: <TrashIcon size={18} color="#EF4444" />,
        keywords: ["tozalash", "tarix", "clear", "delete", "suhbatlar"],
        run: async () => {
          await backendService.clearHistory();
          await backendService.clearChat();
          return "Suhbatlar tarixi tozalandi";
        },
      },
      {
        id: "act-restart-backend",
        title: "Backend Serverini Qayta Yuklash",
        subtitle: "Python API serverini va asboblar reestrini yangilash",
        category: "Tezkor Amallar",
        icon: <RefreshIcon size={18} color="#F97316" />,
        keywords: ["restart", "backend", "qayta", "server", "python", "yangilash"],
        run: () => {
          backendService.restartBackend();
          onClose();
        },
      },
    ],
    [onNavigate, onClose]
  );

  // Registry asboblarini dinamik amallar sifatida qo'shish
  const allActions: PaletteItem[] = useMemo(() => {
    const toolActions: PaletteItem[] = registryTools.map((cmd) => ({
      id: `tool-${cmd.id}`,
      title: cmd.name,
      subtitle: cmd.desc || `Tizim buyrug'i: ${cmd.query || cmd.id}`,
      category: "Tizim Asboblari",
      icon: getToolIcon(cmd),
      keywords: [
        cmd.name.toLowerCase(),
        cmd.query.toLowerCase(),
        cmd.id.toLowerCase(),
        cmd.category.toLowerCase(),
        ...(cmd.tool_name ? [cmd.tool_name.toLowerCase()] : []),
      ],
      isTool: true,
      run: async () => {
        setExecutingId(cmd.id);
        try {
          const res = await backendService.executeCommand(cmd.id, cmd.parameters);
          setExecutingId(null);
          if (res.ok) {
            return res.result || "Buyruq muvaffaqiyatli bajarildi";
          } else {
            return "Xatolik: " + (res.result || "Noma'lum xatolik");
          }
        } catch (err: any) {
          setExecutingId(null);
          return "Xatolik yuz berdi: " + String(err);
        }
      },
    }));

    return [...baseActions, ...toolActions];
  }, [baseActions, registryTools]);

  // Qidiruv bo'yicha filtrlash
  const filteredActions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allActions;
    return allActions.filter(
      (a) =>
        a.title.toLowerCase().includes(q) ||
        a.subtitle.toLowerCase().includes(q) ||
        a.keywords.some((k) => k.includes(q))
    );
  }, [allActions, query]);

  // Reset holati
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setExecutionResult(null);
      setTimeout(() => inputRef.current?.focus(), 40);
    }
  }, [isOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Klaviaturada navigatsiya
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = async (e: KeyboardEvent) => {
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
          const res = await action.run();
          if (typeof res === "string") {
            setExecutionResult({ id: action.id, text: res });
            setTimeout(() => {
              setExecutionResult(null);
              onClose();
            }, 1800);
          }
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filteredActions, selectedIndex, onClose]);

  // Tanlangan elementni ko'rinadigan joyga scroll qilish
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
        backgroundColor: "rgba(0, 0, 0, 0.7)",
        backdropFilter: "blur(10px)",
        WebkitBackdropFilter: "blur(10px)",
        zIndex: 1000,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        paddingTop: "10vh",
        animation: "fadeIn 0.15s ease-out",
      }}
    >
      <div
        className="palette-modal"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "92%",
          maxWidth: "640px",
          backgroundColor: "#0E1422",
          borderRadius: "14px",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          boxShadow: "0 24px 48px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          maxHeight: "72vh",
        }}
      >
        {/* Search Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            padding: "14px 18px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            gap: "12px",
            background: "rgba(255, 255, 255, 0.02)",
          }}
        >
          <SearchIcon size={20} color="var(--primary-glow, #10B981)" />
          <input
            ref={inputRef}
            type="text"
            role="combobox"
            aria-label="Buyruqlar va asboblar qidiruvi"
            aria-autocomplete="list"
            aria-expanded={filteredActions.length > 0}
            aria-controls="palette-results-list"
            aria-activedescendant={
              filteredActions[selectedIndex] ? `palette-item-${filteredActions[selectedIndex].id}` : undefined
            }
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search Mikasa... (Ctrl+K)"
            style={{
              flex: 1,
              backgroundColor: "transparent",
              border: "none",
              outline: "none",
              color: "#FFFFFF",
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

        {/* Execution Result Banner */}
        {executionResult && (
          <div
            style={{
              padding: "10px 18px",
              background: "rgba(16, 185, 129, 0.15)",
              borderBottom: "1px solid rgba(16, 185, 129, 0.3)",
              color: "#34D399",
              fontSize: "13px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <CheckIcon size={15} color="#34D399" />
            <span>{executionResult.text}</span>
          </div>
        )}

        {/* Results List */}
        <div
          ref={listRef}
          id="palette-results-list"
          role="listbox"
          aria-label="Qidiruv natijalari"
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "8px",
          }}
        >
          {filteredActions.length === 0 ? (
            <div
              style={{
                padding: "40px 16px",
                textAlign: "center",
                color: "var(--text-muted, #94A3B8)",
                fontSize: "14px",
              }}
            >
              Hech qanday mos keluvchi buyruq yoki sahifa topilmadi.
            </div>
          ) : (
            filteredActions.map((action, idx) => {
              const isSelected = idx === selectedIndex;
              const isExecuting = executingId === action.id.replace("tool-", "");

              return (
                <div
                  key={action.id}
                  id={`palette-item-${action.id}`}
                  role="option"
                  aria-selected={isSelected}
                  data-index={idx}
                  onClick={async () => {
                    const res = await action.run();
                    if (typeof res === "string") {
                      setExecutionResult({ id: action.id, text: res });
                      setTimeout(() => {
                        setExecutionResult(null);
                        onClose();
                      }, 1800);
                    }
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
                        color: isSelected ? "#FFFFFF" : "#E2E8F0",
                        fontSize: "14px",
                        fontWeight: 600,
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                      }}
                    >
                      <span>{action.title}</span>
                      {action.isTool && (
                        <span
                          style={{
                            fontSize: "10px",
                            padding: "1px 6px",
                            borderRadius: "4px",
                            background: "rgba(245, 158, 11, 0.15)",
                            color: "#F59E0B",
                            fontWeight: 500,
                          }}
                        >
                          Asbob
                        </span>
                      )}
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
                      color: isSelected ? "#34D399" : "var(--text-muted, #64748B)",
                      backgroundColor: isSelected
                        ? "rgba(16, 185, 129, 0.15)"
                        : "rgba(255, 255, 255, 0.03)",
                      padding: "3px 8px",
                      borderRadius: "5px",
                      flexShrink: 0,
                      fontWeight: 500,
                    }}
                  >
                    {isExecuting ? "Bajarilmoqda..." : action.category}
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
            borderTop: "1px solid rgba(255, 255, 255, 0.06)",
            backgroundColor: "rgba(0, 0, 0, 0.25)",
            fontSize: "12px",
            color: "var(--text-muted, #94A3B8)",
          }}
        >
          <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
            <span>
              <kbd style={kbdStyle}>↑</kbd> <kbd style={kbdStyle}>↓</kbd> Tanlash
            </span>
            <span>
              <kbd style={kbdStyle}>↵</kbd> Bajarish / Ochish
            </span>
            <span>
              <kbd style={kbdStyle}>Esc</kbd> Yopish
            </span>
          </div>
          <div style={{ fontSize: "11.5px", color: "var(--primary-glow, #10B981)", fontWeight: 500 }}>
            Mikasa AI · Ctrl+K
          </div>
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

export default CommandPalette;
