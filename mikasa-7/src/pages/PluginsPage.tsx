// ========== PluginsPage.tsx ==========
// Mikasa AI 7.1.0 — Plaginlar va Agent Vositalari Katalogi
// agent_tools.py (29 ta tool registry) va agent_plugins.py bilan real vaqtda bog'langan

import React, { useState, useEffect } from "react";
import {
  PluginsIcon,
  HomeIcon,
  SparklesIcon,
  CloseIcon,
} from "../components/icons/Icons";
import {
  backendService,
  PluginItem,
  PluginsResponse,
} from "../services/backendService";

interface PluginsPageProps {
  onNavigateHome: () => void;
}

export const PluginsPage: React.FC<PluginsPageProps> = ({ onNavigateHome }) => {
  const [plugins, setPlugins] = useState<PluginItem[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("Barchasi");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  // Tool sinov modal holati
  const [selectedTool, setSelectedTool] = useState<PluginItem | null>(null);
  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);

  useEffect(() => {
    let mounted = true;
    const fetchPlugins = async () => {
      setLoading(true);
      const res: PluginsResponse = await backendService.getPlugins();
      if (mounted) {
        setPlugins(res.tools || []);
        setCategories(res.categories || ["Barchasi"]);
        setLoading(false);
      }
    };
    fetchPlugins();
    return () => {
      mounted = false;
    };
  }, []);

  const openToolModal = (tool: PluginItem) => {
    setSelectedTool(tool);
    setParamValues({});
    setExecutionResult(null);
  };

  const closeToolModal = () => {
    setSelectedTool(null);
    setExecutionResult(null);
  };

  const handleRunTool = async () => {
    if (!selectedTool || isExecuting) return;
    setIsExecuting(true);
    setExecutionResult(null);

    const res = await backendService.executePlugin(selectedTool.name, paramValues);
    setExecutionResult(res);
    setIsExecuting(false);
  };

  const filteredPlugins = plugins.filter((p) => {
    const matchesCat =
      selectedCategory === "Barchasi" || p.category.toLowerCase() === selectedCategory.toLowerCase();
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q);
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
              background: "rgba(168, 85, 247, 0.15)",
              border: "1px solid rgba(168, 85, 247, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <PluginsIcon size={20} color="#a855f7" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>
                Plaginlar va AI Vositalar
              </h1>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 12,
                  background: "rgba(168, 85, 247, 0.15)",
                  color: "#a855f7",
                  fontWeight: 500,
                  border: "1px solid rgba(168, 85, 247, 0.2)",
                }}
              >
                {plugins.length} ta faol vosita
              </span>
            </div>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
              AI Agent qo'ng'iroq qilishi mumkin bo'lgan dasturiy instrumentlar va kengaytmalar
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
        {/* Search and Category Filters */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <input
            type="text"
            placeholder="Plagin yoki tool nomini qidirish..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 10,
              padding: "10px 16px",
              color: "var(--text-primary)",
              fontSize: 13,
              outline: "none",
            }}
          />

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  background:
                    selectedCategory === cat ? "#a855f7" : "rgba(255, 255, 255, 0.04)",
                  color: selectedCategory === cat ? "#ffffff" : "var(--text-secondary)",
                  border: `1px solid ${
                    selectedCategory === cat ? "#a855f7" : "var(--border-subtle)"
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

        {/* Plugin Cards Grid */}
        {loading ? (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-secondary)" }}>
            Plaginlar katalogi yuklanmoqda...
          </div>
        ) : filteredPlugins.length === 0 ? (
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
            "{searchQuery}" bo'yicha plagin topilmadi
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: 14,
            }}
          >
            {filteredPlugins.map((tool) => (
              <div
                key={tool.name}
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 12,
                  padding: "16px 18px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: 12,
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "rgba(168, 85, 247, 0.4)";
                  e.currentTarget.style.background = "rgba(168, 85, 247, 0.04)";
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
                      {tool.name}
                    </span>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "2px 6px",
                        borderRadius: 6,
                        background: "rgba(168, 85, 247, 0.12)",
                        color: "#c084fc",
                        fontWeight: 500,
                      }}
                    >
                      {tool.category}
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
                    {tool.description}
                  </p>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    borderTop: "1px solid rgba(255, 255, 255, 0.04)",
                    paddingTop: 10,
                  }}
                >
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    Parametrlar: {Object.keys(tool.parameters || {}).length} ta
                  </span>

                  <button
                    onClick={() => openToolModal(tool)}
                    style={{
                      background: "rgba(168, 85, 247, 0.12)",
                      border: "1px solid rgba(168, 85, 247, 0.3)",
                      color: "#c084fc",
                      borderRadius: 8,
                      padding: "6px 12px",
                      fontSize: 12,
                      fontWeight: 500,
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#a855f7";
                      e.currentTarget.style.color = "#ffffff";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "rgba(168, 85, 247, 0.12)";
                      e.currentTarget.style.color = "#c084fc";
                    }}
                  >
                    Sinab ko'rish
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tool Tester Modal */}
      {selectedTool && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: 20,
          }}
          onClick={closeToolModal}
        >
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 16,
              maxWidth: 540,
              width: "100%",
              padding: 24,
              display: "flex",
              flexDirection: "column",
              gap: 16,
              boxShadow: "0 20px 50px rgba(0, 0, 0, 0.5)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <SparklesIcon size={18} color="#a855f7" />
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{selectedTool.name}</h3>
              </div>
              <button
                onClick={closeToolModal}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  padding: "4px",
                }}
              >
                <CloseIcon size={16} color="currentColor" />
              </button>
            </div>

            <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)" }}>
              {selectedTool.description}
            </p>

            {/* Parameters input */}
            {Object.keys(selectedTool.parameters || {}).length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <span style={{ fontSize: 12, fontWeight: 500, color: "var(--text-secondary)" }}>
                  Kirish parametrlari:
                </span>
                {Object.entries(selectedTool.parameters).map(([paramName, paramMeta]: [string, any]) => (
                  <div key={paramName} style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <label style={{ fontSize: 12, color: "var(--text-primary)", fontWeight: 500 }}>
                      {paramName}{" "}
                      <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>
                        ({paramMeta.type || "string"} - {paramMeta.description || ""})
                      </span>
                    </label>
                    <input
                      type="text"
                      placeholder={`Kiriting... masalan: ${paramName}`}
                      value={paramValues[paramName] || ""}
                      onChange={(e) =>
                        setParamValues({ ...paramValues, [paramName]: e.target.value })
                      }
                      style={{
                        background: "rgba(0, 0, 0, 0.25)",
                        border: "1px solid var(--border-subtle)",
                        borderRadius: 8,
                        padding: "8px 12px",
                        color: "var(--text-primary)",
                        fontSize: 13,
                        outline: "none",
                      }}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div
                style={{
                  fontSize: 12,
                  color: "var(--text-muted)",
                  padding: "8px 12px",
                  background: "rgba(255, 255, 255, 0.02)",
                  borderRadius: 6,
                }}
              >
                Ushbu tool parametr talab qilmaydi. To'g'ridan-to'g'ri ishga tushirish mumkin.
              </div>
            )}

            {/* Execution Result */}
            {executionResult && (
              <div
                style={{
                  background: "rgba(0, 0, 0, 0.4)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 8,
                  padding: 12,
                  maxHeight: 180,
                  overflowY: "auto",
                  fontSize: 12,
                  fontFamily: "monospace",
                  color: "#34d399",
                }}
              >
                <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                  {JSON.stringify(executionResult, null, 2)}
                </pre>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 6 }}>
              <button
                onClick={closeToolModal}
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 8,
                  padding: "8px 16px",
                  color: "var(--text-secondary)",
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                Yopish
              </button>
              <button
                onClick={handleRunTool}
                disabled={isExecuting}
                style={{
                  background: "#a855f7",
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 20px",
                  color: "#ffffff",
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: isExecuting ? "default" : "pointer",
                }}
              >
                {isExecuting ? "Bajarilmoqda..." : "Bajarish"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default PluginsPage;
