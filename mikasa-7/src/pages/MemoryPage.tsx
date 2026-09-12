// ========== MemoryPage.tsx ==========
// Mikasa AI 7.1.0 — Intelligent Knowledge Space & Memory Center
// Sections: Profile, Knowledge, Conversation Context (RAM), Saved Information (History)
// Actions: Search, Add, Edit, Delete, Inspect, Clear

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  MemoryIcon,
  HomeIcon,
  SparklesIcon,
  TrashIcon,
  SearchIcon,
  CloseIcon,
  CheckIcon,
  CopyIcon,
  UserIcon,
  ChatIcon,
  RefreshIcon,
  CodeIcon,
} from "../components/icons/Icons";
import {
  backendService,
  KnowledgeItem,
  ContextTurn,
  MemoryResponse,
} from "../services/backendService";

interface MemoryPageProps {
  onNavigateHome: () => void;
}

export const MemoryPage: React.FC<MemoryPageProps> = ({ onNavigateHome }) => {
  // Navigation Tabs
  const [activeTab, setActiveTab] = useState<"knowledge" | "profile" | "context" | "history">("knowledge");

  // State Data
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [profile, setProfile] = useState<Record<string, any>>({});
  const [conversations, setConversations] = useState<Array<{ user: string; agent: string; time: string }>>([]);
  const [contextTurns, setContextTurns] = useState<ContextTurn[]>([]);
  const [stats, setStats] = useState<{
    kontekst_hajmi?: number;
    suhbatlar_soni?: number;
    bilimlar_soni?: number;
    profil_toliq?: boolean;
  }>({});
  const [loading, setLoading] = useState<boolean>(true);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");

  // Add & Edit Knowledge State
  const [newKey, setNewKey] = useState<string>("");
  const [newValue, setNewValue] = useState<string>("");
  const [isSavingKnowledge, setIsSavingKnowledge] = useState<boolean>(false);
  const [editingItem, setEditingItem] = useState<{ key: string; value: string; originalKey: string } | null>(null);

  // Profile Edit State
  const [editProfile, setEditProfile] = useState<Record<string, any>>({});
  const [isSavingProfile, setIsSavingProfile] = useState<boolean>(false);
  const [newProfileFieldKey, setNewProfileFieldKey] = useState<string>("");
  const [newProfileFieldValue, setNewProfileFieldValue] = useState<string>("");

  // Inspect Modal State
  const [inspectItem, setInspectItem] = useState<{
    title: string;
    subtitle?: string;
    content: string;
    meta?: Record<string, any>;
  } | null>(null);

  // Clear Confirmation Modal State
  const [confirmClear, setConfirmClear] = useState<"knowledge" | "context" | "history" | null>(null);
  const [isClearing, setIsClearing] = useState<boolean>(false);
  const [copiedNotification, setCopiedNotification] = useState<boolean>(false);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 150);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch memory data from backend
  const fetchMemory = useCallback(async () => {
    setLoading(true);
    const res: MemoryResponse = await backendService.getMemory();
    if (res.ok) {
      setKnowledge(res.knowledge || []);
      setProfile(res.profile || {});
      setEditProfile(res.profile || {});
      setConversations(res.conversations || []);
      setContextTurns(res.context || []);
      setStats(res.stats || {});
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchMemory();
  }, [fetchMemory]);

  // ========== KNOWLEDGE ACTIONS ==========
  const handleSaveKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim() || isSavingKnowledge) return;
    setIsSavingKnowledge(true);
    const ok = await backendService.saveKnowledge(newKey.trim(), newValue.trim());
    if (ok) {
      setNewKey("");
      setNewValue("");
      await fetchMemory();
    }
    setIsSavingKnowledge(false);
  };

  const handleUpdateKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingItem || !editingItem.key.trim() || !editingItem.value.trim()) return;

    // Agar kalit nomi o'zgargan bo'lsa, eskisini o'chirib yangisini saqlaymiz
    if (editingItem.key.trim() !== editingItem.originalKey) {
      await backendService.deleteKnowledge(editingItem.originalKey);
    }
    await backendService.saveKnowledge(editingItem.key.trim(), editingItem.value.trim());
    setEditingItem(null);
    await fetchMemory();
  };

  const handleDeleteKnowledge = async (key: string) => {
    const ok = await backendService.deleteKnowledge(key);
    if (ok) {
      setKnowledge((prev) => prev.filter((k) => k.key !== key));
    }
  };

  // ========== PROFILE ACTIONS ==========
  const handleSaveProfile = async () => {
    setIsSavingProfile(true);
    const ok = await backendService.saveProfile(editProfile);
    if (ok) {
      setProfile({ ...editProfile });
    }
    setIsSavingProfile(false);
  };

  const handleAddProfileField = () => {
    if (!newProfileFieldKey.trim() || !newProfileFieldValue.trim()) return;
    setEditProfile((prev) => ({
      ...prev,
      [newProfileFieldKey.trim()]: newProfileFieldValue.trim(),
    }));
    setNewProfileFieldKey("");
    setNewProfileFieldValue("");
  };

  const handleDeleteProfileField = (key: string) => {
    setEditProfile((prev) => {
      const updated = { ...prev };
      delete updated[key];
      return updated;
    });
  };

  // ========== CLEAR ACTIONS ==========
  const handleExecuteClear = async () => {
    if (!confirmClear || isClearing) return;
    setIsClearing(true);

    if (confirmClear === "knowledge") {
      await backendService.clearKnowledge();
      setKnowledge([]);
    } else if (confirmClear === "context") {
      await backendService.clearContext();
      setContextTurns([]);
    } else if (confirmClear === "history") {
      await backendService.clearHistory();
      setConversations([]);
    }

    await fetchMemory();
    setIsClearing(false);
    setConfirmClear(null);
  };

  // Copy to clipboard helper
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedNotification(true);
    setTimeout(() => setCopiedNotification(false), 2000);
  };

  // ========== FILTERED LISTS ==========
  const filteredKnowledge = useMemo(() => {
    const q = debouncedSearch.toLowerCase().trim();
    if (!q) return knowledge;
    return knowledge.filter((k) => k.key.toLowerCase().includes(q) || k.value.toLowerCase().includes(q));
  }, [knowledge, debouncedSearch]);

  const filteredConversations = useMemo(() => {
    const q = debouncedSearch.toLowerCase().trim();
    if (!q) return conversations;
    return conversations.filter((c) => c.user.toLowerCase().includes(q) || c.agent.toLowerCase().includes(q));
  }, [conversations, debouncedSearch]);

  const filteredContext = useMemo(() => {
    const q = debouncedSearch.toLowerCase().trim();
    if (!q) return contextTurns;
    return contextTurns.filter((t) => t.content.toLowerCase().includes(q) || t.role.toLowerCase().includes(q));
  }, [contextTurns, debouncedSearch]);

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
          background: "rgba(10, 15, 29, 0.85)",
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
              Foydalanuvchi profili, bilimlar bazasi, joriy kontekst va suhbatlar arxivi
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button
            onClick={fetchMemory}
            title="Yangilash"
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 8,
              padding: "8px 10px",
              color: "var(--text-secondary)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
            }}
          >
            <RefreshIcon size={14} />
          </button>
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
      </div>

      {/* Main Content Area */}
      <div
        style={{
          maxWidth: 1140,
          width: "100%",
          margin: "0 auto",
          padding: "24px 28px 48px",
          display: "flex",
          flexDirection: "column",
          gap: 22,
        }}
      >
        {/* 4 Stats Cards */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 12,
          }}
        >
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 12,
              padding: "16px 20px",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onClick={() => setActiveTab("knowledge")}
          >
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Bilimlar Bazasi</span>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)", marginTop: 4 }}>
              {knowledge.length}
            </div>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Saqlangan faktlar va ma'lumotlar</span>
          </div>

          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 12,
              padding: "16px 20px",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onClick={() => setActiveTab("profile")}
          >
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Foydalanuvchi Profili</span>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--secondary)", marginTop: 4 }}>
              {profile.ism || "Faol"}
            </div>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              {Object.keys(profile).length} ta maydon
            </span>
          </div>

          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 12,
              padding: "16px 20px",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onClick={() => setActiveTab("context")}
          >
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Joriy Kontekst (RAM)</span>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--primary-glow)", marginTop: 4 }}>
              {contextTurns.length || stats.kontekst_hajmi || 0} ta
            </div>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Faol suhbat xotirasi</span>
          </div>

          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 12,
              padding: "16px 20px",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
            onClick={() => setActiveTab("history")}
          >
            <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>Suhbatlar Arxivi</span>
            <div style={{ fontSize: 24, fontWeight: 700, color: "#f59e0b", marginTop: 4 }}>
              {conversations.length}
            </div>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Tarixga saqlangan dialoglar</span>
          </div>
        </div>

        {/* Tab Navigation Row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderBottom: "1px solid var(--border-subtle)",
            paddingBottom: 8,
            gap: 12,
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", gap: 8 }}>
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
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <SparklesIcon size={14} />
              <span>Bilimlar ({knowledge.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("profile")}
              style={{
                background: activeTab === "profile" ? "rgba(59, 130, 246, 0.15)" : "transparent",
                color: activeTab === "profile" ? "var(--secondary)" : "var(--text-secondary)",
                border: `1px solid ${activeTab === "profile" ? "rgba(59, 130, 246, 0.3)" : "transparent"}`,
                borderRadius: 8,
                padding: "8px 16px",
                fontSize: 13,
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <UserIcon size={14} />
              <span>Profil</span>
            </button>

            <button
              onClick={() => setActiveTab("context")}
              style={{
                background: activeTab === "context" ? "rgba(147, 51, 234, 0.15)" : "transparent",
                color: activeTab === "context" ? "var(--primary-glow)" : "var(--text-secondary)",
                border: `1px solid ${activeTab === "context" ? "rgba(147, 51, 234, 0.3)" : "transparent"}`,
                borderRadius: 8,
                padding: "8px 16px",
                fontSize: 13,
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <CodeIcon size={14} />
              <span>Kontekst (RAM) ({contextTurns.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("history")}
              style={{
                background: activeTab === "history" ? "rgba(245, 158, 11, 0.15)" : "transparent",
                color: activeTab === "history" ? "#f59e0b" : "var(--text-secondary)",
                border: `1px solid ${activeTab === "history" ? "rgba(245, 158, 11, 0.3)" : "transparent"}`,
                borderRadius: 8,
                padding: "8px 16px",
                fontSize: 13,
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <ChatIcon size={14} />
              <span>Suhbatlar Arxivi ({conversations.length})</span>
            </button>
          </div>

          {/* Tab Clear Button */}
          {activeTab === "knowledge" && knowledge.length > 0 && (
            <button
              onClick={() => setConfirmClear("knowledge")}
              style={{
                background: "rgba(239, 68, 68, 0.08)",
                border: "1px solid rgba(239, 68, 68, 0.2)",
                color: "#f87171",
                borderRadius: 8,
                padding: "6px 12px",
                fontSize: 12,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <TrashIcon size={13} />
              <span>Bilimlarni tozalash</span>
            </button>
          )}

          {activeTab === "context" && contextTurns.length > 0 && (
            <button
              onClick={() => setConfirmClear("context")}
              style={{
                background: "rgba(239, 68, 68, 0.08)",
                border: "1px solid rgba(239, 68, 68, 0.2)",
                color: "#f87171",
                borderRadius: 8,
                padding: "6px 12px",
                fontSize: 12,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <TrashIcon size={13} />
              <span>Kontekstni tozalash</span>
            </button>
          )}

          {activeTab === "history" && conversations.length > 0 && (
            <button
              onClick={() => setConfirmClear("history")}
              style={{
                background: "rgba(239, 68, 68, 0.08)",
                border: "1px solid rgba(239, 68, 68, 0.2)",
                color: "#f87171",
                borderRadius: 8,
                padding: "6px 12px",
                fontSize: 12,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <TrashIcon size={13} />
              <span>Arxivni tozalash</span>
            </button>
          )}
        </div>

        {/* Global Search Bar (except for Profile tab) */}
        {activeTab !== "profile" && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              background: "var(--surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 10,
              padding: "0 14px",
              gap: 10,
            }}
          >
            <SearchIcon size={16} color="var(--text-muted)" />
            <input
              type="text"
              placeholder={
                activeTab === "knowledge"
                  ? "Bilimlar kaliti va mazmunidan qidirish..."
                  : activeTab === "context"
                  ? "Joriy kontekst xabarlaridan qidirish..."
                  : "Suhbatlar arxividan qidirish..."
              }
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                padding: "10px 0",
                color: "var(--text-primary)",
                fontSize: 13,
                outline: "none",
              }}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                }}
              >
                <CloseIcon size={14} />
              </button>
            )}
          </div>
        )}

        {/* ========== SECTION 1: KNOWLEDGE BASE ========== */}
        {activeTab === "knowledge" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* Add Knowledge Box */}
            <form
              onSubmit={handleSaveKnowledge}
              style={{
                background: "var(--surface)",
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
                <span>Yangi bilim yoki fakt kiritish</span>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <input
                  type="text"
                  placeholder="Kalit so'z (masalan: sevimli_til, loyiha_vazifasi)"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  style={{
                    flex: "1 1 240px",
                    background: "rgba(0, 0, 0, 0.25)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "8px 12px",
                    color: "var(--text-primary)",
                    fontSize: 13,
                    outline: "none",
                  }}
                />
                <input
                  type="text"
                  placeholder="Mazmun / Qiymat (masalan: Python va Rust, Mikasa AI 7.x desktop)"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  style={{
                    flex: "2 1 360px",
                    background: "rgba(0, 0, 0, 0.25)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "8px 12px",
                    color: "var(--text-primary)",
                    fontSize: 13,
                    outline: "none",
                  }}
                />
                <button
                  type="submit"
                  disabled={!newKey.trim() || !newValue.trim() || isSavingKnowledge}
                  style={{
                    background: "var(--accent)",
                    color: "#0a0f1d",
                    border: "none",
                    borderRadius: 8,
                    padding: "8px 20px",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: newKey.trim() && newValue.trim() ? "pointer" : "default",
                    opacity: newKey.trim() && newValue.trim() ? 1 : 0.6,
                    transition: "all 0.15s ease",
                  }}
                >
                  {isSavingKnowledge ? "Saqlanmoqda..." : "Saqlash"}
                </button>
              </div>
            </form>

            {/* Knowledge Cards Grid */}
            {loading ? (
              <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
                Bilimlar yuklanmoqda...
              </div>
            ) : filteredKnowledge.length === 0 ? (
              <div
                style={{
                  textAlign: "center",
                  padding: "40px 0",
                  color: "var(--text-muted)",
                  background: "rgba(255, 255, 255, 0.02)",
                  borderRadius: 12,
                  border: "1px dashed var(--border-subtle)",
                }}
              >
                {searchQuery ? `"${searchQuery}" bo'yicha hech qanday bilim topilmadi` : "Hozircha hech qanday bilim saqlanmagan"}
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
                  gap: 12,
                }}
              >
                {filteredKnowledge.map((item) => (
                  <div
                    key={item.key}
                    style={{
                      background: "var(--surface)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: 10,
                      padding: "14px 16px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      gap: 10,
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = "rgba(16, 185, 129, 0.3)")}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                        <code
                          style={{
                            fontSize: 12,
                            fontWeight: 600,
                            color: "var(--accent)",
                            background: "rgba(16, 185, 129, 0.1)",
                            padding: "2px 8px",
                            borderRadius: 4,
                          }}
                        >
                          {item.key}
                        </code>
                        <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                          {item.saved_at ? new Date(item.saved_at).toLocaleDateString() : ""}
                        </span>
                      </div>
                      <p
                        style={{
                          margin: 0,
                          fontSize: 13,
                          color: "var(--text-primary)",
                          lineHeight: 1.45,
                          wordBreak: "break-word",
                        }}
                      >
                        {item.value}
                      </p>
                    </div>

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        borderTop: "1px solid rgba(255, 255, 255, 0.04)",
                        paddingTop: 8,
                      }}
                    >
                      <button
                        onClick={() =>
                          setInspectItem({
                            title: item.key,
                            subtitle: "Bilimlar bazasi yozuvi",
                            content: item.value,
                            meta: {
                              "Saqlangan vaqt": item.saved_at,
                              "Murojaatlar soni": item.access_count ?? 0,
                            },
                          })
                        }
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "var(--text-secondary)",
                          fontSize: 11,
                          cursor: "pointer",
                          padding: "2px 6px",
                        }}
                      >
                        Batafsil
                      </button>

                      <div style={{ display: "flex", gap: 6 }}>
                        <button
                          onClick={() => setEditingItem({ key: item.key, value: item.value, originalKey: item.key })}
                          style={{
                            background: "rgba(255, 255, 255, 0.05)",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: 6,
                            padding: "4px 8px",
                            color: "var(--text-secondary)",
                            fontSize: 11,
                            cursor: "pointer",
                          }}
                        >
                          Tahrirlash
                        </button>
                        <button
                          onClick={() => handleDeleteKnowledge(item.key)}
                          style={{
                            background: "rgba(239, 68, 68, 0.1)",
                            border: "1px solid rgba(239, 68, 68, 0.2)",
                            borderRadius: 6,
                            padding: "4px 8px",
                            color: "#f87171",
                            fontSize: 11,
                            cursor: "pointer",
                          }}
                        >
                          O'chirish
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ========== SECTION 2: PROFILE ========== */}
        {activeTab === "profile" && (
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 14,
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: 20,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <UserIcon size={20} color="var(--secondary)" />
                <div>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Foydalanuvchi Shaxsiy Profili</h3>
                  <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
                    Mikasa sizga murojaat qilishda ushbu parametrlar va qiziqishlaringizdan foydalanadi
                  </p>
                </div>
              </div>
              <button
                onClick={handleSaveProfile}
                disabled={isSavingProfile}
                style={{
                  background: "var(--secondary)",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 20px",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {isSavingProfile ? "Saqlanmoqda..." : "Profilni saqlash"}
              </button>
            </div>

            {/* Existing Profile Fields Form */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: 16,
              }}
            >
              {Object.entries(editProfile).map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    background: "rgba(0, 0, 0, 0.2)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 10,
                    padding: "12px 14px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 6,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <label style={{ fontSize: 11, fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase" }}>
                      {k}
                    </label>
                    {!["ism", "ovoz_turi", "til"].includes(k) && (
                      <button
                        onClick={() => handleDeleteProfileField(k)}
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "#f87171",
                          cursor: "pointer",
                          padding: 2,
                        }}
                      >
                        <CloseIcon size={12} />
                      </button>
                    )}
                  </div>
                  <input
                    type="text"
                    value={Array.isArray(v) ? v.join(", ") : String(v ?? "")}
                    onChange={(e) => {
                      const val = e.target.value;
                      setEditProfile((prev) => ({
                        ...prev,
                        [k]: Array.isArray(v) ? val.split(",").map((s) => s.trim()) : val,
                      }));
                    }}
                    style={{
                      background: "rgba(255, 255, 255, 0.04)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: 6,
                      padding: "8px 10px",
                      color: "var(--text-primary)",
                      fontSize: 13,
                      outline: "none",
                    }}
                  />
                </div>
              ))}
            </div>

            {/* Add Custom Profile Field */}
            <div
              style={{
                borderTop: "1px solid var(--border-subtle)",
                paddingTop: 16,
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>
                + Yangi shaxsiy profil maydoni qo'shish
              </span>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <input
                  type="text"
                  placeholder="Maydon nomi (masalan: kasb, shahar, sevimli_mavzu)"
                  value={newProfileFieldKey}
                  onChange={(e) => setNewProfileFieldKey(e.target.value)}
                  style={{
                    flex: "1 1 200px",
                    background: "rgba(0, 0, 0, 0.2)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "8px 12px",
                    color: "var(--text-primary)",
                    fontSize: 12,
                    outline: "none",
                  }}
                />
                <input
                  type="text"
                  placeholder="Qiymat (masalan: Dasturchi, Toshkent, Sun'iy intellekt)"
                  value={newProfileFieldValue}
                  onChange={(e) => setNewProfileFieldValue(e.target.value)}
                  style={{
                    flex: "2 1 280px",
                    background: "rgba(0, 0, 0, 0.2)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "8px 12px",
                    color: "var(--text-primary)",
                    fontSize: 12,
                    outline: "none",
                  }}
                />
                <button
                  onClick={handleAddProfileField}
                  disabled={!newProfileFieldKey.trim() || !newProfileFieldValue.trim()}
                  style={{
                    background: "rgba(255, 255, 255, 0.08)",
                    border: "1px solid var(--border-subtle)",
                    color: "var(--text-primary)",
                    borderRadius: 8,
                    padding: "8px 16px",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                >
                  Qo'shish
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ========== SECTION 3: CONVERSATION CONTEXT (RAM) ========== */}
        {activeTab === "context" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 12,
                padding: "16px 20px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Qisqa muddatli operativ xotira (RAM Context)</h4>
                <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
                  Oxirgi muloqot qadamlari. AI savollarga javob berishda shu joriy kontekstni tahlil qiladi.
                </p>
              </div>
              <span
                style={{
                  fontSize: 11,
                  padding: "4px 10px",
                  borderRadius: 12,
                  background: "rgba(147, 51, 234, 0.15)",
                  color: "var(--primary-glow)",
                  border: "1px solid rgba(147, 51, 234, 0.3)",
                }}
              >
                {contextTurns.length} ta navbat
              </span>
            </div>

            {filteredContext.length === 0 ? (
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
                {searchQuery ? `"${searchQuery}" bo'yicha kontekst topilmadi` : "Joriy suhbat konteksti bo'sh"}
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {filteredContext.map((turn, idx) => {
                  const isUser = turn.role === "user";
                  return (
                    <div
                      key={idx}
                      style={{
                        background: isUser ? "rgba(59, 130, 246, 0.06)" : "var(--surface)",
                        border: `1px solid ${isUser ? "rgba(59, 130, 246, 0.2)" : "var(--border-subtle)"}`,
                        borderRadius: 10,
                        padding: "12px 16px",
                        display: "flex",
                        flexDirection: "column",
                        gap: 6,
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 600,
                            color: isUser ? "var(--secondary)" : "var(--accent)",
                            textTransform: "capitalize",
                          }}
                        >
                          {isUser ? "Foydalanuvchi" : "Mikasa AI"}
                        </span>
                        <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                          {turn.time ? new Date(turn.time).toLocaleTimeString() : ""}
                        </span>
                      </div>
                      <p style={{ margin: 0, fontSize: 13, color: "var(--text-primary)", lineHeight: 1.45 }}>
                        {turn.content}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ========== SECTION 4: SAVED INFORMATION / CONVERSATION HISTORY ========== */}
        {activeTab === "history" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {filteredConversations.length === 0 ? (
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
                {searchQuery ? `"${searchQuery}" bo'yicha suhbat topilmadi` : "Suhbatlar arxivi bo'sh"}
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {filteredConversations.map((conv, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "var(--surface)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: 10,
                      padding: "14px 16px",
                      display: "flex",
                      flexDirection: "column",
                      gap: 10,
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = "rgba(245, 158, 11, 0.3)")}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-subtle)")}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span
                          style={{
                            fontSize: 10,
                            padding: "2px 6px",
                            borderRadius: 4,
                            background: "rgba(245, 158, 11, 0.15)",
                            color: "#f59e0b",
                            fontWeight: 600,
                          }}
                        >
                          Dialog #{filteredConversations.length - idx}
                        </span>
                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                          {conv.time ? new Date(conv.time).toLocaleString() : ""}
                        </span>
                      </div>

                      <button
                        onClick={() =>
                          setInspectItem({
                            title: `Suhbat #${filteredConversations.length - idx}`,
                            subtitle: conv.time,
                            content: `Foydalanuvchi:\n${conv.user}\n\nMikasa:\n${conv.agent}`,
                          })
                        }
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "var(--text-secondary)",
                          fontSize: 11,
                          cursor: "pointer",
                        }}
                      >
                        Batafsil ko'rish
                      </button>
                    </div>

                    {/* User Question */}
                    <div style={{ display: "flex", gap: 8 }}>
                      <strong style={{ fontSize: 12, color: "var(--secondary)", flexShrink: 0 }}>Siz:</strong>
                      <span style={{ fontSize: 13, color: "var(--text-primary)" }}>{conv.user}</span>
                    </div>

                    {/* Agent Response */}
                    <div style={{ display: "flex", gap: 8 }}>
                      <strong style={{ fontSize: 12, color: "var(--accent)", flexShrink: 0 }}>Mikasa:</strong>
                      <span
                        style={{
                          fontSize: 13,
                          color: "var(--text-secondary)",
                          lineHeight: 1.45,
                          maxHeight: 80,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {conv.agent}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ========== EDIT KNOWLEDGE MODAL ========== */}
      {editingItem && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.7)",
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: 20,
          }}
          onClick={() => setEditingItem(null)}
        >
          <form
            onSubmit={handleUpdateKnowledge}
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-strong)",
              borderRadius: 14,
              maxWidth: 480,
              width: "100%",
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Bilimni Tahrirlash</h3>
              <button
                type="button"
                onClick={() => setEditingItem(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <CloseIcon size={16} />
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Kalit so'z:</label>
              <input
                type="text"
                value={editingItem.key}
                onChange={(e) => setEditingItem((prev) => (prev ? { ...prev, key: e.target.value } : null))}
                style={{
                  background: "rgba(0, 0, 0, 0.2)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 8,
                  padding: "8px 12px",
                  color: "var(--text-primary)",
                  fontSize: 13,
                  outline: "none",
                }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Mazmun / Qiymat:</label>
              <textarea
                rows={4}
                value={editingItem.value}
                onChange={(e) => setEditingItem((prev) => (prev ? { ...prev, value: e.target.value } : null))}
                style={{
                  background: "rgba(0, 0, 0, 0.2)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 8,
                  padding: "8px 12px",
                  color: "var(--text-primary)",
                  fontSize: 13,
                  outline: "none",
                  resize: "vertical",
                }}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
              <button
                type="button"
                onClick={() => setEditingItem(null)}
                style={{
                  background: "transparent",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-secondary)",
                  borderRadius: 8,
                  padding: "8px 16px",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Bekor qilish
              </button>
              <button
                type="submit"
                style={{
                  background: "var(--accent)",
                  color: "#0a0f1d",
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 18px",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Yangilash
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ========== INSPECT DETAILS MODAL ========== */}
      {inspectItem && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.7)",
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: 20,
          }}
          onClick={() => setInspectItem(null)}
        >
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-strong)",
              borderRadius: 14,
              maxWidth: 520,
              width: "100%",
              maxHeight: "80vh",
              overflowY: "auto",
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{inspectItem.title}</h3>
                {inspectItem.subtitle && (
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{inspectItem.subtitle}</span>
                )}
              </div>
              <button
                onClick={() => setInspectItem(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <CloseIcon size={16} />
              </button>
            </div>

            <div
              style={{
                background: "rgba(0, 0, 0, 0.25)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 8,
                padding: "12px 14px",
                fontSize: 13,
                color: "var(--text-primary)",
                lineHeight: 1.5,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {inspectItem.content}
            </div>

            {inspectItem.meta && (
              <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 11, color: "var(--text-secondary)" }}>
                {Object.entries(inspectItem.meta).map(([k, v]) => (
                  <div key={k} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span>{k}:</span>
                    <strong style={{ color: "var(--text-primary)" }}>{String(v)}</strong>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
              <button
                onClick={() => handleCopy(inspectItem.content)}
                style={{
                  background: "rgba(255, 255, 255, 0.08)",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-primary)",
                  borderRadius: 8,
                  padding: "6px 14px",
                  fontSize: 12,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                {copiedNotification ? <CheckIcon size={12} /> : <CopyIcon size={12} />}
                <span>{copiedNotification ? "Nusxalandi" : "Nusxalash"}</span>
              </button>
              <button
                onClick={() => setInspectItem(null)}
                style={{
                  background: "var(--secondary)",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: 8,
                  padding: "6px 16px",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Yopish
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== CLEAR CONFIRMATION MODAL ========== */}
      {confirmClear && (
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
          onClick={() => setConfirmClear(null)}
        >
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              borderRadius: 14,
              maxWidth: 440,
              width: "100%",
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#f87171" }}>
              <TrashIcon size={20} />
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Tozalashni tasdiqlang</h3>
            </div>

            <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
              {confirmClear === "knowledge"
                ? "Barcha saqlangan bilimlar butunlay o'chiriladi. Ushbu amalni ortga qaytarib bo'lmaydi."
                : confirmClear === "context"
                ? "Joriy suhbat konteksti (RAM) tozalanadi. AI avvalgi xabarlarni unutadi."
                : "Barcha saqlangan suhbatlar arxivi to'liq tozalanadi."}
            </p>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
              <button
                onClick={() => setConfirmClear(null)}
                style={{
                  background: "transparent",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-secondary)",
                  borderRadius: 8,
                  padding: "8px 16px",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Bekor qilish
              </button>
              <button
                onClick={handleExecuteClear}
                disabled={isClearing}
                style={{
                  background: "#ef4444",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 18px",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {isClearing ? "Tozalanmoqda..." : "Ha, tozalansin"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoryPage;
