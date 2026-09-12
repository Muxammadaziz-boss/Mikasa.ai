// ========== CommandsPage.tsx ==========
// Mikasa AI 7.1.0 — Tizim va Avtomatlashtirish Buyruqlari Markazi
// Mahalliy buyruqlar taqsimlagichi (CommandDispatcher) va main.py bilan real vaqtda bog'langan

import React, { useState, useEffect } from "react";
import {
  CommandsIcon,
  HomeIcon,
  SparklesIcon,
  ArrowUpIcon,
  CloseIcon,
} from "../components/icons/Icons";
import {
  backendService,
  CommandItem,
  CommandsResponse,
} from "../services/backendService";

interface CommandsPageProps {
  onNavigateHome: () => void;
}

export const CommandsPage: React.FC<CommandsPageProps> = ({ onNavigateHome }) => {
  const [commands, setCommands] = useState<CommandItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("Barchasi");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [customCommand, setCustomCommand] = useState<string>("");
  const [isExecuting, setIsExecuting] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<{
    command: string;
    message: string;
    success: boolean;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Buyruqlarni backenddan yuklash
  useEffect(() => {
    let mounted = true;
    const fetchCommands = async () => {
      setLoading(true);
      const res: CommandsResponse = await backendService.getCommands();
      if (mounted) {
        setCommands(res.commands || []);
        setCategories(res.categories || ["Barchasi"]);
        setLoading(false);
      }
    };
    fetchCommands();
    return () => {
      mounted = false;
    };
  }, []);

  // Buyruqni bajarish
  const handleExecute = async (cmdQuery: string) => {
    if (!cmdQuery.trim() || isExecuting) return;
    setIsExecuting(cmdQuery);
    setExecutionResult(null);

    const res = await backendService.executeCommand(cmdQuery);
    setExecutionResult({
      command: cmdQuery,
      message: res.result || (res.ok ? "Buyruq muvaffaqiyatli bajarildi" : "Xatolik yuz berdi"),
      success: res.ok,
    });
    setIsExecuting(null);
  };

  // Filtrlangan buyruqlar
  const filteredCommands = commands.filter((cmd) => {
    const matchesCat =
      selectedCategory === "Barchasi" || cmd.category.toLowerCase() === selectedCategory.toLowerCase();
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      cmd.name.toLowerCase().includes(query) ||
      cmd.query.toLowerCase().includes(query) ||
      cmd.desc.toLowerCase().includes(query);
    return matchesCat && matchesSearch;
  });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        background: "var(--bg-gradient)",
        color: "var(--text-primary)",
        overflowY: "auto",
        position: "relative",
      }}
    >
      {/* Header Bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 28px",
          borderBottom: "1px solid var(--border-subtle)",
          background: "rgba(10, 15, 29, 0.75)",
          backdropFilter: "blur(20px)",
          position: "sticky",
          top: 0,
          zIndex: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: "50%",
              background: "rgba(59, 130, 246, 0.15)",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CommandsIcon size={20} color="var(--secondary)" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>
                Buyruqlar Markazi
              </h1>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 12,
                  background: "rgba(59, 130, 246, 0.15)",
                  color: "var(--secondary)",
                  fontWeight: 500,
                  border: "1px solid rgba(59, 130, 246, 0.2)",
                }}
              >
                {commands.length} ta buyruq
              </span>
            </div>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
              Tizim boshqaruvi, dasturlar va multimedia amallarini tezkor ishga tushirish
            </p>
          </div>
        </div>

        <button
          onClick={onNavigateHome}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid var(--border-subtle)",
            color: "var(--text-secondary)",
            padding: "8px 14px",
            borderRadius: 8,
            fontSize: 12,
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "var(--text-primary)";
            e.currentTarget.style.borderColor = "var(--border-strong)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "var(--text-secondary)";
            e.currentTarget.style.borderColor = "var(--border-subtle)";
          }}
        >
          <HomeIcon size={14} />
          <span>Bosh sahifa</span>
        </button>
      </div>

      {/* Main Container */}
      <div
        style={{
          maxWidth: 1100,
          width: "100%",
          margin: "0 auto",
          padding: "24px 28px 48px",
          display: "flex",
          flexDirection: "column",
          gap: 22,
        }}
      >
        {/* Custom Command Bar */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid var(--border-subtle)",
            borderRadius: 14,
            padding: "16px 20px",
            backdropFilter: "blur(12px)",
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 500 }}>
            <SparklesIcon size={15} color="var(--primary-glow)" />
            <span>Ixtiyoriy buyruqni sinab ko'rish</span>
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            <input
              type="text"
              placeholder="Masalan: youtube och, soat necha, ovoz 50, telegram..."
              value={customCommand}
              onChange={(e) => setCustomCommand(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && customCommand.trim()) {
                  handleExecute(customCommand);
                }
              }}
              style={{
                flex: 1,
                background: "rgba(0, 0, 0, 0.25)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 10,
                padding: "10px 14px",
                color: "var(--text-primary)",
                fontSize: 13,
                outline: "none",
              }}
              onFocus={(e) => (e.target.style.borderColor = "var(--secondary)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--border-subtle)")}
            />
            <button
              onClick={() => handleExecute(customCommand)}
              disabled={!customCommand.trim() || isExecuting !== null}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                background: customCommand.trim() ? "var(--secondary)" : "rgba(255, 255, 255, 0.08)",
                color: customCommand.trim() ? "#ffffff" : "var(--text-muted)",
                border: "none",
                borderRadius: 10,
                padding: "0 18px",
                fontSize: 13,
                fontWeight: 500,
                cursor: customCommand.trim() ? "pointer" : "default",
                transition: "all 0.2s ease",
              }}
            >
              <ArrowUpIcon size={14} />
              <span>{isExecuting === customCommand ? "Bajarilmoqda..." : "Ishga tushirish"}</span>
            </button>
          </div>

          {/* Execution Result Toast */}
          {executionResult && (
            <div
              style={{
                marginTop: 6,
                padding: "10px 14px",
                borderRadius: 8,
                fontSize: 12,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                background: executionResult.success
                  ? "rgba(16, 185, 129, 0.12)"
                  : "rgba(239, 68, 68, 0.12)",
                border: `1px solid ${
                  executionResult.success ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"
                }`,
                color: executionResult.success ? "#34d399" : "#f87171",
              }}
            >
              <span>
                <strong>{executionResult.command}:</strong> {executionResult.message}
              </span>
              <button
                onClick={() => setExecutionResult(null)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "inherit",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  padding: "2px",
                }}
              >
                <CloseIcon size={14} color="currentColor" />
              </button>
            </div>
          )}
        </div>

        {/* Search and Category Filters */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <input
              type="text"
              placeholder="Buyruqlar orasidan qidirish..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                flex: 1,
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 10,
                padding: "10px 16px",
                color: "var(--text-primary)",
                fontSize: 13,
                outline: "none",
              }}
            />
          </div>

          {/* Category Chips */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  background:
                    selectedCategory === cat ? "var(--secondary)" : "rgba(255, 255, 255, 0.04)",
                  color: selectedCategory === cat ? "#ffffff" : "var(--text-secondary)",
                  border: `1px solid ${
                    selectedCategory === cat ? "var(--secondary)" : "var(--border-subtle)"
                  }`,
                  borderRadius: 20,
                  padding: "6px 14px",
                  fontSize: 12,
                  fontWeight: selectedCategory === cat ? 500 : 400,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Command Cards Grid */}
        {loading ? (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-secondary)" }}>
            Buyruqlar yuklanmoqda...
          </div>
        ) : filteredCommands.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "48px 0",
              color: "var(--text-muted)",
              background: "rgba(255, 255, 255, 0.02)",
              borderRadius: 12,
              border: "1px dashed var(--border-subtle)",
            }}
          >
            "{searchQuery}" bo'yicha buyruq topilmadi
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(310px, 1fr))",
              gap: 14,
            }}
          >
            {filteredCommands.map((cmd) => (
              <div
                key={cmd.id}
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 12,
                  padding: "16px 18px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: 12,
                  transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "rgba(59, 130, 246, 0.4)";
                  e.currentTarget.style.background = "rgba(59, 130, 246, 0.04)";
                  e.currentTarget.style.transform = "translateY(-1px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border-subtle)";
                  e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 6,
                    }}
                  >
                    <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                      {cmd.name}
                    </span>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "2px 6px",
                        borderRadius: 6,
                        background: "rgba(255, 255, 255, 0.06)",
                        color: "var(--text-muted)",
                        fontWeight: 500,
                      }}
                    >
                      {cmd.category}
                    </span>
                  </div>
                  <p
                    style={{
                      margin: 0,
                      fontSize: 12,
                      color: "var(--text-secondary)",
                      lineHeight: 1.4,
                      marginBottom: 8,
                    }}
                  >
                    {cmd.desc}
                  </p>
                  <code
                    style={{
                      fontSize: 11,
                      color: "var(--secondary)",
                      background: "rgba(59, 130, 246, 0.08)",
                      padding: "2px 6px",
                      borderRadius: 4,
                    }}
                  >
                    "{cmd.query}"
                  </code>
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent: "flex-end",
                    borderTop: "1px solid rgba(255, 255, 255, 0.04)",
                    paddingTop: 10,
                  }}
                >
                  <button
                    onClick={() => handleExecute(cmd.query)}
                    disabled={isExecuting !== null}
                    style={{
                      background:
                        isExecuting === cmd.query
                          ? "rgba(59, 130, 246, 0.2)"
                          : "rgba(59, 130, 246, 0.12)",
                      border: "1px solid rgba(59, 130, 246, 0.3)",
                      color: "var(--secondary)",
                      borderRadius: 8,
                      padding: "6px 12px",
                      fontSize: 12,
                      fontWeight: 500,
                      cursor: isExecuting !== null ? "default" : "pointer",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      if (!isExecuting) {
                        e.currentTarget.style.background = "var(--secondary)";
                        e.currentTarget.style.color = "#ffffff";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isExecuting) {
                        e.currentTarget.style.background = "rgba(59, 130, 246, 0.12)";
                        e.currentTarget.style.color = "var(--secondary)";
                      }
                    }}
                  >
                    {isExecuting === cmd.query ? "Bajarilmoqda..." : "Bajarish"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
export default CommandsPage;
