// ========== MemoryPage.tsx ==========
// Mikasa AI 8.0.0 — Intelligent Knowledge Space & Memory Center
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
  MemoryPolicyConfig,
  MemoryMetrics,
  ContextTraceItem,
} from "../services/backendService";

interface MemoryPageProps {
  onNavigateHome: () => void;
}

export const MemoryPage: React.FC<MemoryPageProps> = ({ onNavigateHome }) => {
  // Navigation Tabs (Phase 30 extended)
  const [activeTab, setActiveTab] = useState<"knowledge" | "privacy" | "observability" | "profile" | "context" | "history">("knowledge");

  // State Data
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([]);
  const [profile, setProfile] = useState<Record<string, any>>({});
  const [conversations, setConversations] = useState<Array<{ user: string; agent: string; time: string }>>([]);
  const [contextTurns, setContextTurns] = useState<ContextTurn[]>([]);
  const [stats, setStats] = useState<{
    kontekst_hajmi?: number;
    suhbatlar_soni?: number;
    bilimlar_soni?: number;
    faol_bilimlar_soni?: number;
    pinned_bilimlar_soni?: number;
    profil_toliq?: boolean;
  }>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Search & Filter (Phase 30 Inspector Filters)
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedSearch, setDebouncedSearch] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [pinnedFilter, setPinnedFilter] = useState<string>("all"); // "all" | "pinned"
  const [statusFilter, setStatusFilter] = useState<string>("all"); // "all" | "active" | "superseded"

  // Add Knowledge State
  const [newKey, setNewKey] = useState<string>("");
  const [newValue, setNewValue] = useState<string>("");
  const [newType, setNewType] = useState<string>("fact");
  const [newImportance, setNewImportance] = useState<number>(0.5);
  const [newPinned, setNewPinned] = useState<boolean>(false);
  const [isSavingKnowledge, setIsSavingKnowledge] = useState<boolean>(false);

  // Phase 30: Edit Modal State (Full Metadata)
  const [editingKnowledge, setEditingKnowledge] = useState<{
    id: string;
    key: string;
    value: string;
    type: string;
    importance: number;
    pinned: boolean;
  } | null>(null);
  const [isUpdatingKnowledge, setIsUpdatingKnowledge] = useState<boolean>(false);

  // Phase 30: Safe Delete Modal State
  const [deletingKnowledge, setDeletingKnowledge] = useState<{
    idOrKey: string;
    key: string;
    value: string;
  } | null>(null);
  const [isDeletingKnowledge, setIsDeletingKnowledge] = useState<boolean>(false);

  // Profile Edit State
  const [editProfile, setEditProfile] = useState<Record<string, any>>({});
  const [isSavingProfile, setIsSavingProfile] = useState<boolean>(false);
  const [newProfileFieldKey, setNewProfileFieldKey] = useState<string>("");
  const [newProfileFieldValue, setNewProfileFieldValue] = useState<string>("");

  // Phase 30: Privacy Policy State
  const [policyConfig, setPolicyConfig] = useState<MemoryPolicyConfig>({
    do_not_remember_all: false,
    blocked_types: [],
    blocked_keys: [],
  });
  const [isSavingPolicy, setIsSavingPolicy] = useState<boolean>(false);
  const [newBlockedKey, setNewBlockedKey] = useState<string>("");

  // Phase 30: Observability State
  const [metrics, setMetrics] = useState<MemoryMetrics | null>(null);
  const [traces, setTraces] = useState<ContextTraceItem[]>([]);
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);
  const [loadingObservability, setLoadingObservability] = useState<boolean>(false);

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
    setLoadError(null);
    try {
      const res: MemoryResponse = await backendService.getMemory();
      if (res.ok) {
        setKnowledge(res.knowledge || []);
        setProfile(res.profile || {});
        setEditProfile(res.profile || {});
        setConversations(res.conversations || []);
        setContextTurns(res.context || []);
        setStats(res.stats || {});
      }
    } catch (err: any) {
      setLoadError(err.message || "Backend serveriga ulanib bo'lmadi");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMemory();
  }, [fetchMemory]);

  // ========== KNOWLEDGE ACTIONS ==========
  const handleSaveKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim() || isSavingKnowledge) return;
    setIsSavingKnowledge(true);
    const ok = await backendService.saveKnowledge(
      newKey.trim(),
      newValue.trim(),
      newType,
      newImportance,
      newPinned
    );
    if (ok) {
      setNewKey("");
      setNewValue("");
      setNewType("fact");
      setNewImportance(0.5);
      setNewPinned(false);
      await fetchMemory();
    }
    setIsSavingKnowledge(false);
  };

  const handleTogglePin = async (item: KnowledgeItem) => {
    const idOrKey = item.id || item.key;
    const newPinned = !item.pinned;
    // Optimistic UI update
    setKnowledge((prev) =>
      prev.map((k) => (k.key === item.key || (k.id && k.id === item.id) ? { ...k, pinned: newPinned } : k))
    );
    const ok = await backendService.togglePinKnowledge(idOrKey, newPinned);
    if (!ok) {
      await fetchMemory();
    }
  };

  const handleOpenEditKnowledge = (item: KnowledgeItem) => {
    setEditingKnowledge({
      id: item.id || item.key,
      key: item.key,
      value: item.content || item.value,
      type: item.type || "fact",
      importance: item.importance ?? 0.5,
      pinned: Boolean(item.pinned),
    });
  };

  const handleUpdateKnowledgeItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingKnowledge || !editingKnowledge.key.trim() || !editingKnowledge.value.trim() || isUpdatingKnowledge) return;
    setIsUpdatingKnowledge(true);
    const res = await backendService.updateKnowledgeItem(editingKnowledge.id, {
      key: editingKnowledge.key.trim(),
      value: editingKnowledge.value.trim(),
      content: editingKnowledge.value.trim(),
      type: editingKnowledge.type,
      importance: Number(editingKnowledge.importance),
      pinned: editingKnowledge.pinned,
    });
    if (res.ok) {
      setEditingKnowledge(null);
      await fetchMemory();
    }
    setIsUpdatingKnowledge(false);
  };

  const handleOpenDeleteKnowledge = (item: KnowledgeItem) => {
    setDeletingKnowledge({
      idOrKey: item.id || item.key,
      key: item.key,
      value: item.content || item.value,
    });
  };

  const handleConfirmDeleteKnowledge = async () => {
    if (!deletingKnowledge || isDeletingKnowledge) return;
    setIsDeletingKnowledge(true);
    const ok = await backendService.deleteKnowledgeItem(deletingKnowledge.idOrKey);
    if (ok) {
      setKnowledge((prev) => prev.filter((k) => k.key !== deletingKnowledge.key && k.id !== deletingKnowledge.idOrKey));
      setDeletingKnowledge(null);
    }
    setIsDeletingKnowledge(false);
  };

  // ========== PRIVACY & DO-NOT-REMEMBER ACTIONS ==========
  const fetchPolicy = useCallback(async () => {
    try {
      const p = await backendService.getMemoryPolicy();
      setPolicyConfig(p);
    } catch {
      // ignore
    }
  }, []);

  const handleSavePolicy = async (updated: Partial<MemoryPolicyConfig>) => {
    setIsSavingPolicy(true);
    const newCfg = { ...policyConfig, ...updated };
    const ok = await backendService.saveMemoryPolicy(newCfg);
    if (ok) {
      setPolicyConfig(newCfg);
    }
    setIsSavingPolicy(false);
  };

  const handleToggleBlockedType = (typeKey: string) => {
    const list = policyConfig.blocked_types || [];
    const exists = list.includes(typeKey);
    const nextList = exists ? list.filter((t) => t !== typeKey) : [...list, typeKey];
    handleSavePolicy({ blocked_types: nextList });
  };

  const handleAddBlockedKey = () => {
    const trimmed = newBlockedKey.trim().toLowerCase();
    if (!trimmed) return;
    const list = policyConfig.blocked_keys || [];
    if (!list.includes(trimmed)) {
      handleSavePolicy({ blocked_keys: [...list, trimmed] });
    }
    setNewBlockedKey("");
  };

  const handleRemoveBlockedKey = (keyToRemove: string) => {
    const list = policyConfig.blocked_keys || [];
    handleSavePolicy({ blocked_keys: list.filter((k) => k !== keyToRemove) });
  };

  // ========== OBSERVABILITY ACTIONS ==========
  const fetchObservability = useCallback(async () => {
    setLoadingObservability(true);
    try {
      const [m, t] = await Promise.all([
        backendService.getMemoryMetrics(),
        backendService.getContextTraces(),
      ]);
      setMetrics(m);
      setTraces(t);
    } catch {
      // ignore
    } finally {
      setLoadingObservability(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "observability") {
      fetchObservability();
    } else if (activeTab === "privacy") {
      fetchPolicy();
    }
  }, [activeTab, fetchObservability, fetchPolicy]);

  // ========== PROFILE ACTIONS ==========
  const handleSaveProfile = async () => {
    setIsSavingProfile(true);
    const ok = await backendService.saveProfile(editProfile);
    if (ok) {
      setProfile(editProfile);
    }
    setIsSavingProfile(false);
  };

  const handleDeleteProfileField = (fieldKey: string) => {
    setEditProfile((prev) => {
      const next = { ...prev };
      delete next[fieldKey];
      return next;
    });
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

  // ========== MODAL & CLIPBOARD ACTIONS ==========
  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedNotification(true);
      setTimeout(() => setCopiedNotification(false), 2000);
    } catch {
      // ignore
    }
  };

  const handleExecuteClear = async () => {
    if (!confirmClear || isClearing) return;
    setIsClearing(true);
    let ok = false;
    if (confirmClear === "knowledge") {
      ok = await backendService.clearKnowledge();
      if (ok) setKnowledge([]);
    } else if (confirmClear === "context") {
      ok = await backendService.clearContext();
      if (ok) setContextTurns([]);
    } else if (confirmClear === "history") {
      ok = await backendService.clearHistory();
      if (ok) setConversations([]);
    }
    if (ok) {
      setConfirmClear(null);
      await fetchMemory();
    }
    setIsClearing(false);
  };

  // ========== FILTERED LISTS ==========
  const filteredKnowledge = useMemo(() => {
    const q = debouncedSearch.toLowerCase().trim();
    let list = knowledge;

    // Search query filter
    if (q) {
      list = list.filter((k) =>
        k.key.toLowerCase().includes(q) ||
        (k.content || k.value || "").toLowerCase().includes(q)
      );
    }

    // Type filter
    if (typeFilter !== "all") {
      list = list.filter((k) => (k.type || "fact").toLowerCase() === typeFilter.toLowerCase());
    }

    // Pinned filter
    if (pinnedFilter === "pinned") {
      list = list.filter((k) => Boolean(k.pinned));
    }

    // Status filter
    if (statusFilter === "active") {
      list = list.filter((k) => k.is_active !== false && !k.superseded_by);
    } else if (statusFilter === "superseded") {
      list = list.filter((k) => k.is_active === false || Boolean(k.superseded_by));
    }

    // Sort: pinned first, then by access count or created
    return [...list].sort((a, b) => {
      if (Boolean(a.pinned) !== Boolean(b.pinned)) {
        return a.pinned ? -1 : 1;
      }
      return (b.access_count ?? 0) - (a.access_count ?? 0);
    });
  }, [knowledge, debouncedSearch, typeFilter, pinnedFilter, statusFilter]);

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

            <button
              onClick={() => setActiveTab("privacy")}
              style={{
                background: activeTab === "privacy" ? "rgba(236, 72, 153, 0.15)" : "transparent",
                color: activeTab === "privacy" ? "#ec4899" : "var(--text-secondary)",
                border: `1px solid ${activeTab === "privacy" ? "rgba(236, 72, 153, 0.3)" : "transparent"}`,
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
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <span>Maxfiylik (Privacy)</span>
            </button>

            <button
              onClick={() => setActiveTab("observability")}
              style={{
                background: activeTab === "observability" ? "rgba(14, 165, 233, 0.15)" : "transparent",
                color: activeTab === "observability" ? "#0ea5e9" : "var(--text-secondary)",
                border: `1px solid ${activeTab === "observability" ? "rgba(14, 165, 233, 0.3)" : "transparent"}`,
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
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M3 12h1m16 0h1M12 3v1m0 16v1m-6.36-13.64.7.7m11.32 11.32.7.7m0-12.72-.7.7M6.34 17.66l-.7.7"/>
              </svg>
              <span>Kuzatuv & Izlar</span>
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
            {/* Add Knowledge Box with Phase 30 fields */}
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
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 500 }}>
                  <SparklesIcon size={15} color="var(--accent)" />
                  <span>Yangi bilim yoki fakt kiritish</span>
                </div>
                <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-secondary)", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={newPinned}
                    onChange={(e) => setNewPinned(e.target.checked)}
                    style={{ accentColor: "#f59e0b", cursor: "pointer" }}
                  />
                  <span>Muhim / Qadalgan (Pin)</span>
                </label>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <input
                  type="text"
                  placeholder="Kalit so'z (masalan: sevimli_til, loyiha_muhiti)"
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  style={{
                    flex: "1 1 200px",
                    background: "rgba(0, 0, 0, 0.25)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "8px 12px",
                    color: "var(--text-primary)",
                    fontSize: 13,
                    outline: "none",
                  }}
                />

                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  style={{
                    flex: "0 0 140px",
                    background: "rgba(0, 0, 0, 0.25)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "8px 10px",
                    color: "var(--text-primary)",
                    fontSize: 12,
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  <option value="fact">Fakt (Fact)</option>
                  <option value="preference">Xohish (Preference)</option>
                  <option value="work_context">Ish muhiti (Work)</option>
                  <option value="task">Vazifa (Task)</option>
                  <option value="note">Eslatma (Note)</option>
                </select>

                <input
                  type="text"
                  placeholder="Mazmun / Qiymat (masalan: Python va Rust, Mikasa AI 7.x desktop)"
                  value={newValue}
                  onChange={(e) => setNewValue(e.target.value)}
                  style={{
                    flex: "2 1 280px",
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

            {/* Memory Inspector Filter Bar */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: 10,
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 10,
                padding: "8px 14px",
              }}
            >
              {/* Type Filter Pills */}
              <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                <span style={{ fontSize: 11, color: "var(--text-muted)", marginRight: 4 }}>Tur:</span>
                {[
                  { id: "all", label: "Barchasi" },
                  { id: "fact", label: "Fakt" },
                  { id: "preference", label: "Xohish" },
                  { id: "work_context", label: "Ish muhiti" },
                  { id: "task", label: "Vazifa" },
                  { id: "note", label: "Eslatma" },
                ].map((tf) => (
                  <button
                    key={tf.id}
                    onClick={() => setTypeFilter(tf.id)}
                    style={{
                      background: typeFilter === tf.id ? "rgba(16, 185, 129, 0.18)" : "rgba(255, 255, 255, 0.04)",
                      color: typeFilter === tf.id ? "var(--accent)" : "var(--text-secondary)",
                      border: `1px solid ${typeFilter === tf.id ? "rgba(16, 185, 129, 0.35)" : "transparent"}`,
                      borderRadius: 6,
                      padding: "4px 10px",
                      fontSize: 11,
                      fontWeight: typeFilter === tf.id ? 600 : 400,
                      cursor: "pointer",
                    }}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>

              {/* Pinned & Status Filters */}
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <button
                  onClick={() => setPinnedFilter((prev) => (prev === "pinned" ? "all" : "pinned"))}
                  style={{
                    background: pinnedFilter === "pinned" ? "rgba(245, 158, 11, 0.2)" : "rgba(255, 255, 255, 0.04)",
                    color: pinnedFilter === "pinned" ? "#f59e0b" : "var(--text-secondary)",
                    border: `1px solid ${pinnedFilter === "pinned" ? "rgba(245, 158, 11, 0.4)" : "transparent"}`,
                    borderRadius: 6,
                    padding: "4px 10px",
                    fontSize: 11,
                    fontWeight: pinnedFilter === "pinned" ? 600 : 400,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                  }}
                >
                  <span>★</span>
                  <span>{pinnedFilter === "pinned" ? "Faqat qadalgan" : "Qadalganlar"}</span>
                </button>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    background: "rgba(0, 0, 0, 0.2)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 6,
                    padding: "4px 8px",
                    color: "var(--text-secondary)",
                    fontSize: 11,
                    outline: "none",
                    cursor: "pointer",
                  }}
                >
                  <option value="all">Holat: Barchasi</option>
                  <option value="active">Holat: Faol</option>
                  <option value="superseded">Holat: Eskirgan</option>
                </select>
              </div>
            </div>

            {/* Knowledge Cards Grid */}
            {loading ? (
              <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text-muted)" }}>
                Bilimlar yuklanmoqda...
              </div>
            ) : loadError ? (
              <div
                style={{
                  display: "flex", flexDirection: "column", alignItems: "center",
                  justifyContent: "center", padding: "48px 24px", gap: "14px", textAlign: "center",
                }}
                role="alert"
              >
                <div style={{ width: 52, height: 52, borderRadius: "50%", background: "rgba(239, 68, 68, 0.1)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                </div>
                <span style={{ fontSize: "15px", fontWeight: 600, color: "#F1F5F9" }}>Xotira ma'lumotlari yuklanmadi</span>
                <span style={{ fontSize: "13px", color: "#94A3B8", maxWidth: "380px", lineHeight: 1.5 }}>{loadError}. Backend server ishga tushganligini tekshiring.</span>
                <button onClick={() => fetchMemory()} style={{ display: "flex", alignItems: "center", gap: "6px", padding: "9px 18px", borderRadius: "8px", border: "none", background: "#10B981", color: "#fff", fontSize: "13px", fontWeight: 500, cursor: "pointer" }}>
                  Qayta yuklash
                </button>
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
                {searchQuery || typeFilter !== "all" || pinnedFilter !== "all"
                  ? "Tanlangan filtrlar bo'yicha hech qanday bilim topilmadi"
                  : "Hozircha hech qanday bilim saqlanmagan"}
              </div>
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
                  gap: 12,
                }}
              >
                {filteredKnowledge.map((item) => {
                  const isItemActive = item.is_active !== false && !item.superseded_by;
                  const itemType = item.type || "fact";

                  // Type badge colors
                  const typeColors: Record<string, { bg: string; text: string }> = {
                    fact: { bg: "rgba(59, 130, 246, 0.15)", text: "#60a5fa" },
                    preference: { bg: "rgba(168, 85, 247, 0.15)", text: "#c084fc" },
                    work_context: { bg: "rgba(245, 158, 11, 0.15)", text: "#fbbf24" },
                    task: { bg: "rgba(6, 182, 212, 0.15)", text: "#22d3ee" },
                    note: { bg: "rgba(16, 185, 129, 0.15)", text: "#34d399" },
                  };
                  const tColor = typeColors[itemType] || typeColors.fact;

                  return (
                    <div
                      key={item.id || item.key}
                      style={{
                        background: "var(--surface)",
                        border: `1px solid ${item.pinned ? "rgba(245, 158, 11, 0.35)" : "var(--border-subtle)"}`,
                        borderRadius: 10,
                        padding: "14px 16px",
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: "space-between",
                        gap: 10,
                        transition: "all 0.15s ease",
                        position: "relative",
                        boxShadow: item.pinned ? "0 0 12px rgba(245, 158, 11, 0.08)" : "none",
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.borderColor = item.pinned ? "rgba(245, 158, 11, 0.6)" : "rgba(16, 185, 129, 0.3)")}
                      onMouseLeave={(e) => (e.currentTarget.style.borderColor = item.pinned ? "rgba(245, 158, 11, 0.35)" : "var(--border-subtle)")}
                    >
                      <div>
                        {/* Card Top: Badges & Pin Action */}
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
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
                            <span
                              style={{
                                fontSize: 10,
                                padding: "1px 6px",
                                borderRadius: 4,
                                background: tColor.bg,
                                color: tColor.text,
                                fontWeight: 500,
                              }}
                            >
                              {itemType}
                            </span>
                            {!isItemActive && (
                              <span
                                style={{
                                  fontSize: 9,
                                  padding: "1px 5px",
                                  borderRadius: 4,
                                  background: "rgba(239, 68, 68, 0.15)",
                                  color: "#f87171",
                                }}
                                title="Yangi ma'lumot bilan almashtirilgan"
                              >
                                eskirgan
                              </span>
                            )}
                          </div>

                          {/* Pin Toggle Button */}
                          <button
                            onClick={() => handleTogglePin(item)}
                            title={item.pinned ? "Qadoqdan chiqarish (Unpin)" : "Muhim qilib qadash (Pin)"}
                            style={{
                              background: item.pinned ? "rgba(245, 158, 11, 0.2)" : "rgba(255, 255, 255, 0.05)",
                              border: `1px solid ${item.pinned ? "rgba(245, 158, 11, 0.4)" : "var(--border-subtle)"}`,
                              borderRadius: "50%",
                              width: 26,
                              height: 26,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              cursor: "pointer",
                              color: item.pinned ? "#f59e0b" : "var(--text-muted)",
                              fontSize: 13,
                              transition: "all 0.15s ease",
                            }}
                          >
                            ★
                          </button>
                        </div>

                        <p
                          style={{
                            margin: "4px 0 8px",
                            fontSize: 13,
                            color: "var(--text-primary)",
                            lineHeight: 1.45,
                            wordBreak: "break-word",
                          }}
                        >
                          {item.content || item.value}
                        </p>

                        {/* Metadata row: Importance bar & access count */}
                        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 10, color: "var(--text-muted)" }}>
                          <span>Muhimlik: {Math.round((item.importance ?? 0.5) * 100)}%</span>
                          <span>•</span>
                          <span>{item.access_count ?? 0} ta murojaat</span>
                        </div>
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
                              subtitle: `Xotira ID: ${item.id || "N/A"} (${itemType})`,
                              content: item.content || item.value,
                              meta: {
                                "ID": item.id || "N/A",
                                "Turi (Type)": itemType,
                                "Manba (Source)": item.source || "user",
                                "Muhimlik": item.importance ?? 0.5,
                                "Ishonchlilik (Confidence)": item.confidence ?? 1.0,
                                "Qadalgan (Pinned)": item.pinned ? "Ha" : "Yo'q",
                                "Faollik": isItemActive ? "Faol" : "Eskirgan / Superseded",
                                "Yaratilgan": item.created_at || item.saved_at || "N/A",
                                "Yangilangan": item.updated_at || "N/A",
                                "So'nggi foydalanish": item.last_used_at || "N/A",
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
                            onClick={() => handleOpenEditKnowledge(item)}
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
                            onClick={() => handleOpenDeleteKnowledge(item)}
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
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ========== SECTION: PRIVACY & DO-NOT-REMEMBER ========== */}
        {activeTab === "privacy" && (
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-subtle)",
              borderRadius: 14,
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: 24,
            }}
          >
            {/* Header */}
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: "50%",
                  background: "rgba(236, 72, 153, 0.15)",
                  border: "1px solid rgba(236, 72, 153, 0.3)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#ec4899",
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Xotira Maxfiyligi va Do-Not-Remember Boshqaruvi</h3>
                <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
                  Mikasa AI xotirasi faqat DATA bo'lib, foydalanuvchi to'liq nazoratiga ega. Xotiraga doimiy yozishni cheklash sozlamalari.
                </p>
              </div>
            </div>

            {/* Global Do-Not-Remember Toggle Box */}
            <div
              style={{
                background: (policyConfig.do_not_remember_all || policyConfig.do_not_remember) ? "rgba(236, 72, 153, 0.08)" : "rgba(255, 255, 255, 0.02)",
                border: `1px solid ${(policyConfig.do_not_remember_all || policyConfig.do_not_remember) ? "rgba(236, 72, 153, 0.3)" : "var(--border-subtle)"}`,
                borderRadius: 12,
                padding: "18px 20px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 16,
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                    Barcha xotira yozuvlarini to'xtatish (Do-Not-Remember All)
                  </span>
                  {(policyConfig.do_not_remember_all || policyConfig.do_not_remember) && (
                    <span
                      style={{
                        fontSize: 10,
                        padding: "2px 8px",
                        borderRadius: 12,
                        background: "rgba(236, 72, 153, 0.2)",
                        color: "#ec4899",
                        fontWeight: 600,
                      }}
                    >
                      FAOL (BLOKLANGAN)
                    </span>
                  )}
                </div>
                <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.45, maxWidth: 640 }}>
                  Yoqilganda, AI siz bilan odatiy rejimda suhbatlashishda davom etadi, ammo birorta ham yangi fakt, xohish yoki kontekst xotiraga saqlanmaydi.
                </p>
              </div>

              <button
                onClick={() =>
                  handleSavePolicy({
                    do_not_remember_all: !(policyConfig.do_not_remember_all || policyConfig.do_not_remember),
                  })
                }
                disabled={isSavingPolicy}
                style={{
                  background: (policyConfig.do_not_remember_all || policyConfig.do_not_remember) ? "#ec4899" : "rgba(255, 255, 255, 0.1)",
                  color: (policyConfig.do_not_remember_all || policyConfig.do_not_remember) ? "#ffffff" : "var(--text-secondary)",
                  border: "none",
                  borderRadius: 20,
                  padding: "8px 20px",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  whiteSpace: "nowrap",
                }}
              >
                {(policyConfig.do_not_remember_all || policyConfig.do_not_remember) ? "O'chirish" : "Yoqish"}
              </button>
            </div>

            {/* Blocked Types */}
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Turlar bo'yicha cheklov (Blocked Memory Types)</h4>
                <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
                  Belgilangan turlarga tegishli bilimlarni xotiraga avtomatik yozilishi taqiqlanadi:
                </p>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10 }}>
                {[
                  { id: "work_context", label: "Ish muhiti (Work Context)", desc: "Loyiha va operatsion tizim tafsilotlari" },
                  { id: "preference", label: "Shaxsiy did (Preferences)", desc: "Foydalanuvchi xohish-istaklari" },
                  { id: "fact", label: "Faktlar (Facts)", desc: "Shaxsiy barqaror faktlar" },
                  { id: "task", label: "Vazifalar (Tasks)", desc: "Davom etayotgan vazifa parametrlari" },
                  { id: "note", label: "Eslatmalar (Notes)", desc: "Qisqa yozuv va eslatmalar" },
                ].map((typeItem) => {
                  const isBlocked = (policyConfig.blocked_types || []).includes(typeItem.id);
                  return (
                    <label
                      key={typeItem.id}
                      style={{
                        background: isBlocked ? "rgba(236, 72, 153, 0.08)" : "rgba(0, 0, 0, 0.2)",
                        border: `1px solid ${isBlocked ? "rgba(236, 72, 153, 0.35)" : "var(--border-subtle)"}`,
                        borderRadius: 10,
                        padding: "12px 14px",
                        display: "flex",
                        flexDirection: "column",
                        gap: 4,
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: isBlocked ? "#ec4899" : "var(--text-primary)" }}>
                          {typeItem.label}
                        </span>
                        <input
                          type="checkbox"
                          checked={isBlocked}
                          onChange={() => handleToggleBlockedType(typeItem.id)}
                          style={{ accentColor: "#ec4899", cursor: "pointer" }}
                        />
                      </div>
                      <span style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.35 }}>
                        {typeItem.desc}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Blocked Keys & Topics */}
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div>
                <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Kalit so'zlar bo'yicha cheklov (Blocked Keys)</h4>
                <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
                  Quyidagi kalit so'zlarni o'z ichiga olgan bilimlarni xotiraga yozish qat'iyan man etiladi:
                </p>
              </div>

              <div style={{ display: "flex", gap: 8, maxWidth: 500 }}>
                <input
                  type="text"
                  placeholder="Yangi taqiqlangan kalit (masalan: maosh, parol, karta)"
                  value={newBlockedKey}
                  onChange={(e) => setNewBlockedKey(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleAddBlockedKey();
                    }
                  }}
                  style={{
                    flex: 1,
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
                  type="button"
                  onClick={handleAddBlockedKey}
                  disabled={!newBlockedKey.trim()}
                  style={{
                    background: "rgba(236, 72, 153, 0.2)",
                    border: "1px solid rgba(236, 72, 153, 0.35)",
                    color: "#ec4899",
                    borderRadius: 8,
                    padding: "8px 16px",
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: newBlockedKey.trim() ? "pointer" : "default",
                    opacity: newBlockedKey.trim() ? 1 : 0.6,
                  }}
                >
                  Qo'shish
                </button>
              </div>

              {/* Blocked Keys Tags */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 4 }}>
                {(policyConfig.blocked_keys || []).length === 0 ? (
                  <span style={{ fontSize: 12, color: "var(--text-muted)", fontStyle: "italic" }}>
                    Hozircha birorta ham kalit so'z bloklanmagan
                  </span>
                ) : (
                  (policyConfig.blocked_keys || []).map((k) => (
                    <span
                      key={k}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        background: "rgba(236, 72, 153, 0.12)",
                        border: "1px solid rgba(236, 72, 153, 0.25)",
                        color: "#ec4899",
                        borderRadius: 6,
                        padding: "4px 10px",
                        fontSize: 12,
                        fontWeight: 500,
                      }}
                    >
                      <code>{k}</code>
                      <button
                        onClick={() => handleRemoveBlockedKey(k)}
                        title="O'chirish"
                        style={{
                          background: "transparent",
                          border: "none",
                          color: "inherit",
                          cursor: "pointer",
                          padding: 0,
                          lineHeight: 1,
                          fontSize: 12,
                        }}
                      >
                        ✕
                      </button>
                    </span>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========== SECTION: OBSERVABILITY & CONTEXT TRACES ========== */}
        {activeTab === "observability" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* Telemetry Metrics Cards */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
                gap: 12,
              }}
            >
              <div style={{ background: "var(--surface)", border: "1px solid var(--border-subtle)", borderRadius: 10, padding: "14px 16px" }}>
                <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>Umumiy Xotiralar</span>
                <div style={{ fontSize: 20, fontWeight: 700, color: "var(--accent)", marginTop: 4 }}>
                  {metrics?.total_memories ?? knowledge.length}
                </div>
                <div style={{ display: "flex", gap: 8, fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
                  <span>Faol: {metrics?.active_memories ?? stats.faol_bilimlar_soni ?? knowledge.length}</span>
                  <span>•</span>
                  <span>Qadalgan: {metrics?.pinned_memories ?? stats.pinned_bilimlar_soni ?? 0}</span>
                </div>
              </div>

              <div style={{ background: "var(--surface)", border: "1px solid var(--border-subtle)", borderRadius: 10, padding: "14px 16px" }}>
                <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>Qidiruv So'rovlari</span>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#0ea5e9", marginTop: 4 }}>
                  {metrics?.retrieval_requests_total ?? metrics?.total_retrieval_requests ?? 0}
                </div>
                <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                  Muvaffaqiyatli: {metrics?.memory_hit_count ?? 0} ta
                </span>
              </div>

              <div style={{ background: "var(--surface)", border: "1px solid var(--border-subtle)", borderRadius: 10, padding: "14px 16px" }}>
                <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>Xotira Hit Rate</span>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#10b981", marginTop: 4 }}>
                  {Math.round(((metrics?.memory_hit_rate ?? metrics?.hit_rate) || 0) * 100)}%
                </div>
                <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                  O'rtacha: {metrics?.average_selected_per_request ?? 0} ta/so'rov
                </span>
              </div>

              <div style={{ background: "var(--surface)", border: "1px solid var(--border-subtle)", borderRadius: 10, padding: "14px 16px" }}>
                <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>Rad Etilgan Yozuvlar</span>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#f59e0b", marginTop: 4 }}>
                  {metrics?.rejected_writes_total ?? 0}
                </div>
                <div style={{ display: "flex", gap: 6, fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>
                  <span>Maxfiy: {metrics?.rejected_writes_sensitive ?? 0}</span>
                  <span>•</span>
                  <span>Siyosat: {metrics?.rejected_writes_policy ?? 0}</span>
                </div>
              </div>

              <div style={{ background: "var(--surface)", border: "1px solid var(--border-subtle)", borderRadius: 10, padding: "14px 16px" }}>
                <span style={{ fontSize: 11, color: "var(--text-secondary)" }}>Foydalanuvchi O'chirishlari</span>
                <div style={{ fontSize: 20, fontWeight: 700, color: "#f87171", marginTop: 4 }}>
                  {metrics?.deleted_items_total ?? metrics?.user_deletions ?? 0}
                </div>
                <span style={{ fontSize: 10, color: "var(--text-muted)" }}>Xavfsiz o'chirilgan bilimlar</span>
              </div>
            </div>

            {/* Context Trace Pipeline Section */}
            <div
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 14,
                padding: "20px 24px",
                display: "flex",
                flexDirection: "column",
                gap: 16,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: "50%",
                      background: "rgba(14, 165, 233, 0.15)",
                      border: "1px solid rgba(14, 165, 233, 0.3)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "#0ea5e9",
                    }}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="3" />
                      <path d="M3 12h1m16 0h1M12 3v1m0 16v1m-6.36-13.64.7.7m11.32 11.32.7.7m0-12.72-.7.7M6.34 17.66l-.7.7" />
                    </svg>
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>So'nggi Kontekst Izlari (Ring Buffer: 25 ta)</h3>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      AI quvuri bosqichlari (Stages) va ijro vaqti (maxfiy ma'lumotlar avtomatik yashirilgan)
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => fetchObservability()}
                  style={{
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "6px 12px",
                    color: "var(--text-secondary)",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                >
                  Yangilash
                </button>
              </div>

              {loadingObservability ? (
                <div style={{ textAlign: "center", padding: "30px 0", color: "var(--text-muted)", fontSize: 13 }}>
                  Izlar yuklanmoqda...
                </div>
              ) : traces.length === 0 ? (
                <div
                  style={{
                    textAlign: "center",
                    padding: "36px 0",
                    color: "var(--text-muted)",
                    background: "rgba(255, 255, 255, 0.015)",
                    borderRadius: 10,
                    border: "1px dashed var(--border-subtle)",
                    fontSize: 13,
                  }}
                >
                  Hozircha birorta ham so'rov izi qayd etilmagan. AI bilan suhbatlashganda bu yerda quvur bosqichlari aks etadi.
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {[...traces].reverse().map((tr) => {
                    const isExpanded = expandedTraceId === tr.trace_id;
                    return (
                      <div
                        key={tr.trace_id}
                        style={{
                          background: "rgba(0, 0, 0, 0.22)",
                          border: `1px solid ${isExpanded ? "rgba(14, 165, 233, 0.4)" : "var(--border-subtle)"}`,
                          borderRadius: 10,
                          padding: "12px 16px",
                          display: "flex",
                          flexDirection: "column",
                          gap: 10,
                          transition: "all 0.15s ease",
                        }}
                      >
                        {/* Trace Row Header */}
                        <div
                          onClick={() => setExpandedTraceId(isExpanded ? null : tr.trace_id)}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            cursor: "pointer",
                            gap: 12,
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <span
                              style={{
                                width: 8,
                                height: 8,
                                borderRadius: "50%",
                                background: tr.success !== false ? "#10b981" : "#ef4444",
                              }}
                            />
                            <code style={{ fontSize: 11, color: "#0ea5e9", fontWeight: 600 }}>{tr.trace_id}</code>
                            <span style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 500 }}>
                              {tr.query ? `"${tr.query.slice(0, 60)}${tr.query.length > 60 ? "..." : ""}"` : "So'rov"}
                            </span>
                          </div>

                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <span
                              style={{
                                fontSize: 11,
                                padding: "2px 8px",
                                borderRadius: 4,
                                background: "rgba(14, 165, 233, 0.12)",
                                color: "#38bdf8",
                                fontWeight: 500,
                              }}
                            >
                              {tr.total_duration_ms || tr.duration_ms || 0} ms
                            </span>
                            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                              {tr.stages?.length || tr.stage_count || 0} bosqich
                            </span>
                            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                              {isExpanded ? "▲" : "▼"}
                            </span>
                          </div>
                        </div>

                        {/* Expanded Stages Timeline */}
                        {isExpanded && (
                          <div
                            style={{
                              borderTop: "1px solid rgba(255, 255, 255, 0.05)",
                              paddingTop: 12,
                              display: "flex",
                              flexDirection: "column",
                              gap: 8,
                            }}
                          >
                            <span style={{ fontSize: 11, color: "var(--text-secondary)", fontWeight: 600 }}>
                              Quvur bosqichlari (Pipeline Stages):
                            </span>
                            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                              {(tr.stages || []).map((stg, sIdx) => (
                                <div
                                  key={sIdx}
                                  style={{
                                    background: "rgba(255, 255, 255, 0.02)",
                                    border: "1px solid rgba(255, 255, 255, 0.04)",
                                    borderRadius: 6,
                                    padding: "8px 12px",
                                    display: "flex",
                                    flexDirection: "column",
                                    gap: 4,
                                  }}
                                >
                                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                      <span style={{ fontSize: 11, fontWeight: 600, color: "#38bdf8" }}>
                                        {sIdx + 1}. {stg.stage}
                                      </span>
                                      <span
                                        style={{
                                          fontSize: 9,
                                          padding: "1px 5px",
                                          borderRadius: 4,
                                          background: stg.status === "ok" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                                          color: stg.status === "ok" ? "#34d399" : "#f87171",
                                          fontWeight: 600,
                                        }}
                                      >
                                        {stg.status}
                                      </span>
                                    </div>
                                    <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                                      {stg.duration_ms ?? 0} ms
                                    </span>
                                  </div>

                                  {(stg.details || stg.data) && Object.keys(stg.details || stg.data || {}).length > 0 && (
                                    <pre
                                      style={{
                                        margin: "4px 0 0",
                                        padding: "6px 8px",
                                        borderRadius: 4,
                                        background: "rgba(0, 0, 0, 0.3)",
                                        fontSize: 10,
                                        color: "var(--text-secondary)",
                                        whiteSpace: "pre-wrap",
                                        wordBreak: "break-all",
                                        fontFamily: "monospace",
                                        maxHeight: 120,
                                        overflowY: "auto",
                                      }}
                                    >
                                      {JSON.stringify(stg.details || stg.data, null, 2)}
                                    </pre>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
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

      {/* ========== EDIT KNOWLEDGE MODAL (PHASE 30) ========== */}
      {editingKnowledge && (
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
          onClick={() => setEditingKnowledge(null)}
        >
          <form
            onSubmit={handleUpdateKnowledgeItem}
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border-strong)",
              borderRadius: 14,
              maxWidth: 500,
              width: "100%",
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Xotira Elementini Tahrirlash</h3>
              <button
                type="button"
                onClick={() => setEditingKnowledge(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <CloseIcon size={16} />
              </button>
            </div>

            {/* Key */}
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Kalit so'z (Key):</label>
              <input
                type="text"
                value={editingKnowledge.key}
                onChange={(e) => setEditingKnowledge((prev) => (prev ? { ...prev, key: e.target.value } : null))}
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

            {/* Type & Importance row */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Turi (Type):</label>
                <select
                  value={editingKnowledge.type}
                  onChange={(e) => setEditingKnowledge((prev) => (prev ? { ...prev, type: e.target.value } : null))}
                  style={{
                    background: "rgba(0, 0, 0, 0.2)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "8px 12px",
                    color: "var(--text-primary)",
                    fontSize: 13,
                    outline: "none",
                  }}
                >
                  <option value="fact">Fakt (fact)</option>
                  <option value="preference">Xohish (preference)</option>
                  <option value="work_context">Ish muhiti (work_context)</option>
                  <option value="task">Vazifa (task)</option>
                  <option value="note">Eslatma (note)</option>
                </select>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Muhimlik darajasi:</label>
                  <span style={{ fontSize: 12, color: "var(--accent)", fontWeight: 600 }}>
                    {Math.round((editingKnowledge.importance ?? 0.5) * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={editingKnowledge.importance}
                  onChange={(e) =>
                    setEditingKnowledge((prev) => (prev ? { ...prev, importance: parseFloat(e.target.value) } : null))
                  }
                  style={{ marginTop: 6, accentColor: "var(--accent)" }}
                />
              </div>
            </div>

            {/* Pinned Checkbox */}
            <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 13 }}>
              <input
                type="checkbox"
                checked={editingKnowledge.pinned}
                onChange={(e) => setEditingKnowledge((prev) => (prev ? { ...prev, pinned: e.target.checked } : null))}
                style={{ accentColor: "#f59e0b" }}
              />
              <span style={{ color: "#f59e0b", fontWeight: 500 }}>★ Doimiy qadalgan xotira (Pinned)</span>
            </label>

            {/* Content */}
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Mazmun / Qiymat (Content):</label>
              <textarea
                rows={4}
                value={editingKnowledge.value}
                onChange={(e) => setEditingKnowledge((prev) => (prev ? { ...prev, value: e.target.value } : null))}
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
                onClick={() => setEditingKnowledge(null)}
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
                disabled={isUpdatingKnowledge}
                style={{
                  background: "var(--accent)",
                  color: "#0a0f1d",
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 18px",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                  opacity: isUpdatingKnowledge ? 0.7 : 1,
                }}
              >
                {isUpdatingKnowledge ? "Yangilanmoqda..." : "Yangilash"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ========== DELETE KNOWLEDGE CONFIRMATION MODAL (PHASE 30) ========== */}
      {deletingKnowledge && (
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
          onClick={() => setDeletingKnowledge(null)}
        >
          <div
            style={{
              background: "var(--surface)",
              border: "1px solid rgba(239, 68, 68, 0.35)",
              borderRadius: 14,
              maxWidth: 460,
              width: "100%",
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#f87171" }}>
                <TrashIcon size={20} />
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Xotirani o'chirishni tasdiqlang</h3>
              </div>
              <button
                type="button"
                onClick={() => setDeletingKnowledge(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              >
                <CloseIcon size={16} />
              </button>
            </div>

            <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
              <strong style={{ color: "var(--text-primary)" }}>"{deletingKnowledge.key}"</strong> kalitiga ega
              xotira elementi butunlay o'chiriladi. Ushbu amalni ortga qaytarib bo'lmaydi.
            </p>

            <div
              style={{
                background: "rgba(0, 0, 0, 0.25)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 8,
                padding: "10px 12px",
                fontSize: 12,
                color: "var(--text-muted)",
                maxHeight: 90,
                overflowY: "auto",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
              }}
            >
              {deletingKnowledge.value}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
              <button
                type="button"
                onClick={() => setDeletingKnowledge(null)}
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
                type="button"
                onClick={handleConfirmDeleteKnowledge}
                disabled={isDeletingKnowledge}
                style={{
                  background: "#ef4444",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: 8,
                  padding: "8px 18px",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                  opacity: isDeletingKnowledge ? 0.7 : 1,
                }}
              >
                {isDeletingKnowledge ? "O'chirilmoqda..." : "Ha, o'chirilsin"}
              </button>
            </div>
          </div>
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
