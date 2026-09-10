// ========== MemoryPage.tsx ==========
// Mikasa AI 7.1.0 — Agent Xotira va Bilimlar Bazasi Boshqaruvi
// agent_memory.py, agent_knowledge.json va agent_profile.json bilan bog'langan

import React, { useState, useEffect } from "react";
import {
  MemoryIcon,
  HomeIcon,
  SparklesIcon,
  TrashIcon,
} from "../components/icons/Icons";
import {
  backendService,
  KnowledgeItem,
  MemoryResponse,
} from "../services/backendService";

interface MemoryPageProps {
  onNavigateHome: () => void;
}

export const MemoryPage: React.FC<MemoryPageProps> = ({ onNavigateHome }) => {
  const [activeTab, setActiveTab] = useState<"knowledge" | "profile" | "history">("knowledge");
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [profile, setProfile] = useState<Record<string, any>>({});
  const [conversations, setConversations] = useState<
    Array<{ user: string; agent: string; time: string }>
  >([]);
  const [stats, setStats] = useState<{
    kontekst_hajmi?: number;
    suhbatlar_soni?: number;
    bilimlar_soni?: number;
  }>({});
  const [loading, setLoading] = useState<boolean>(true);

  // Yangi bilim shakli
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [searchFilter, setSearchFilter] = useState("");

  const fetchMemory = async () => {
    setLoading(true);
    const res: MemoryResponse = await backendService.getMemory();
    if (res.ok) {
      setKnowledge(res.knowledge || []);
      setProfile(res.profile || {});
      setConversations(res.conversations || []);
      setStats(res.stats || {});
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchMemory();
  }, []);

  const handleAddKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim() || isSaving) return;
    setIsSaving(true);
    const ok = await backendService.saveKnowledge(newKey.trim(), newValue.trim());
    if (ok) {
      setNewKey("");
      setNewValue("");
      await fetchMemory();
    }
    setIsSaving(false);
  };

  const handleDeleteKnowledge = async (key: string) => {
    const ok = await backendService.deleteKnowledge(key);
    if (ok) {
      setKnowledge((prev) => prev.filter((k) => k.key !== key));
    }
  };

  const filteredKnowledge = knowledge.filter(
    (k) =>
      k.key.toLowerCase().includes(searchFilter.toLowerCase()) ||
      k.value.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const filteredConversations = conversations.filter(
    (c) =>
      c.user.toLowerCase().includes(searchFilter.toLowerCase()) ||
      c.agent.toLowerCase().includes(searchFilter.toLowerCase())
  );

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
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <MemoryIcon size={20} color="var(--accent)" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>
                Xotira Markazi
              </h1>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 12,
                  background: "rgba(16, 185, 129, 0.15)",
                  color: "var(--accent)",
                  fontWeight: 500,
                  border: "1px solid rgba(16, 185, 129, 0.2)",
                }}
              >
                {knowledge.length} ta bilim
              </span>
            </div>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
              Mikasa o'rgangan bilimlar, shaxsiy kontekst va suhbatlar arxivi
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

      {/* Main Content Area */}
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
        {/* Stats Row */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 12,
          }}
        >
          <div
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 12,
              padding: "14px 18px",
            }}
          >
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Saqlangan Bilimlar</span>
            <div style={{ fontSize: 22, fontWeight: 700, color: "var(--accent)", marginTop: 4 }}>
              {knowledge.length}
            </div>
          </div>
          <div
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 12,
              padding: "14px 18px",
            }}
          >
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Suhbatlar Tarixi</span>
            <div style={{ fontSize: 22, fontWeight: 700, color: "var(--secondary)", marginTop: 4 }}>
              {conversations.length}
            </div>
          </div>
          <div
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 12,
              padding: "14px 18px",
            }}
          >
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Joriy Kontekst (RAM)</span>
            <div style={{ fontSize: 22, fontWeight: 700, color: "var(--primary-glow)", marginTop: 4 }}>
              {stats.kontekst_hajmi || 0} ta
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: "flex", gap: 8, borderBottom: "1px solid var(--border-subtle)", paddingBottom: 8 }}>
          <button
            onClick={() => setActiveTab("knowledge")}
            style={{
              background: activeTab === "knowledge" ? "rgba(16, 185, 129, 0.15)" : "transparent",
              color: activeTab === "knowledge" ? "var(--accent)" : "var(--text-secondary)",
              border: `1px solid ${activeTab === "knowledge" ? "rgba(16, 185, 129, 0.3)" : "transparent"}`,
              borderRadius: 8,
              padding: "8px 16px",
              fontSize: 13,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Bilimlar Bazasi ({knowledge.length})
          </button>
          <button
            onClick={() => setActiveTab("profile")}
            style={{
              background: activeTab === "profile" ? "rgba(16, 185, 129, 0.15)" : "transparent",
              color: activeTab === "profile" ? "var(--accent)" : "var(--text-secondary)",
              border: `1px solid ${activeTab === "profile" ? "rgba(16, 185, 129, 0.3)" : "transparent"}`,
              borderRadius: 8,
              padding: "8px 16px",
              fontSize: 13,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Foydalanuvchi Profili
          </button>
          <button
            onClick={() => setActiveTab("history")}
            style={{
              background: activeTab === "history" ? "rgba(16, 185, 129, 0.15)" : "transparent",
              color: activeTab === "history" ? "var(--accent)" : "var(--text-secondary)",
              border: `1px solid ${activeTab === "history" ? "rgba(16, 185, 129, 0.3)" : "transparent"}`,
              borderRadius: 8,
              padding: "8px 16px",
              fontSize: 13,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Suhbatlar Tarixi ({conversations.length})
          </button>
        </div>

        {/* Tab 1: Knowledge Base */}
        {activeTab === "knowledge" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Add Knowledge Form */}
            <form
              onSubmit={handleAddKnowledge}
              style={{
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 12,
                padding: "16px 20px",
                display: "flex",
                flexDirection: "column",
                gap: 12,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 500 }}>
                <SparklesIcon size={15} color="var(--accent)" />
                <span>Yangi bilim yoki eslatma fakt qo'shish</span>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <input
                  type="text"
                  placeholder="Kalit so'z (masalan: Kasbim, Tug'ilgan kunim, Sevimli taomim...)"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  style={{
                    flex: "1 1 240px",
                    background: "rgba(0, 0, 0, 0.25)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "9px 12px",
                    color: "var(--text-primary)",
                    fontSize: 13,
                    outline: "none",
                  }}
                />
                <input
                  type="text"
                  placeholder="Qiymat (masalan: Dasturchi, 15-aprel, Osh...)"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  style={{
                    flex: "2 1 320px",
                    background: "rgba(0, 0, 0, 0.25)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "9px 12px",
                    color: "var(--text-primary)",
                    fontSize: 13,
                    outline: "none",
                  }}
                />
                <button
                  type="submit"
                  disabled={!newKey.trim() || !newValue.trim() || isSaving}
                  style={{
                    background: "var(--accent)",
                    color: "#052e16",
                    border: "none",
                    borderRadius: 8,
                    padding: "0 18px",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {isSaving ? "Saqlanmoqda..." : "Saqlash"}
                </button>
              </div>
            </form>

            {/* Search Filter */}
            <input
              type="text"
              placeholder="Bilimlar orasidan qidirish..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              style={{
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 8,
                padding: "8px 14px",
                color: "var(--text-primary)",
                fontSize: 13,
                outline: "none",
              }}
            />

            {/* Knowledge List */}
            {loading ? (
              <div style={{ textAlign: "center", padding: "30px", color: "var(--text-secondary)" }}>
                Xotira yuklanmoqda...
              </div>
            ) : filteredKnowledge.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "36px",
                  color: "var(--text-muted)",
                  border: "1px dashed var(--border-subtle)",
                  borderRadius: 10,
                }}
              >
                Hozircha saqlangan bilimlar mavjud emas. Yuqoridagi shakl orqali birinchi bilimni qo'shing!
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {filteredKnowledge.map((item) => (
                  <div
                    key={item.key}
                    style={{
                      background: "rgba(255, 255, 255, 0.03)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: 10,
                      padding: "12px 16px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 16,
                    }}
                  >
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--accent)" }}>
                          {item.key}
                        </span>
                        {item.saved_at && (
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                            {new Date(item.saved_at).toLocaleDateString("uz-UZ")}
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: 13, color: "var(--text-primary)" }}>{item.value}</span>
                    </div>

                    <button
                      onClick={() => handleDeleteKnowledge(item.key)}
                      style={{
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgba(239, 68, 68, 0.2)",
                        color: "#f87171",
                        borderRadius: 6,
                        padding: "6px 10px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: 11,
                      }}
                      title="O'chirish"
                    >
                      <TrashIcon size={13} />
                      <span>O'chirish</span>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: User Profile */}
        {activeTab === "profile" && (
          <div
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 12,
              padding: "20px 24px",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
          >
            <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Foydalanuvchi Shaxsiy Profili</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
              <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 12, borderRadius: 8 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Foydalanuvchi ismi</span>
                <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>
                  {profile.ism || "Muxammadaziz"}
                </div>
              </div>
              <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 12, borderRadius: 8 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Ovoz turi</span>
                <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>
                  {profile.ovoz_turi === "erkak" ? "Sardar (Erkak)" : "Madina (Ayol)"}
                </div>
              </div>
              <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 12, borderRadius: 8 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Asosiy muloqot tili</span>
                <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>O'zbek tili (uz-UZ)</div>
              </div>
              <div style={{ background: "rgba(0, 0, 0, 0.2)", padding: 12, borderRadius: 8 }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Xotira holati</span>
                <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, color: "var(--accent)" }}>
                  Faol va sinxronlangan
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: History */}
        {activeTab === "history" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <input
                type="text"
                placeholder="Suhbatlardan qidirish..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                style={{
                  flex: 1,
                  background: "rgba(255, 255, 255, 0.04)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 8,
                  padding: "8px 14px",
                  color: "var(--text-primary)",
                  fontSize: 13,
                  outline: "none",
                }}
              />
            </div>

            {filteredConversations.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "36px",
                  color: "var(--text-muted)",
                  border: "1px dashed var(--border-subtle)",
                  borderRadius: 10,
                }}
              >
                Hozircha saqlangan suhbatlar mavjud emas
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {filteredConversations.map((c, i) => (
                  <div
                    key={i}
                    style={{
                      background: "rgba(255, 255, 255, 0.03)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: 10,
                      padding: "14px 16px",
                      display: "flex",
                      flexDirection: "column",
                      gap: 8,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: "var(--secondary)" }}>
                        Siz:
                      </span>
                      <span style={{ fontSize: 13 }}>{c.user}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: "var(--primary-glow)" }}>
                        Mikasa:
                      </span>
                      <span style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.4 }}>
                        {c.agent}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
export default MemoryPage;
