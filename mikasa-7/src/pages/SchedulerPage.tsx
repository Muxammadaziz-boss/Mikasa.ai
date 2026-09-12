// ========== SchedulerPage.tsx ==========
// Mikasa AI 7.1.0 — Rejalashtiruvchi va Eslatmalar Tizimi
// agent_scheduler.py va scheduled_tasks.json bilan real vaqtda bog'langan
// 5 ta holat: active, repeating, completed, failed, cancelled

import React, { useState, useEffect, useMemo } from "react";
import {
  SchedulerIcon,
  HomeIcon,
  SparklesIcon,
  TrashIcon,
  PlayIcon,
  PauseIcon,
  EditIcon,
  RepeatIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  XCircleIcon,
  SearchIcon,
  ClockIcon,
  CloseIcon,
  CheckIcon,
} from "../components/icons/Icons";
import {
  backendService,
  ScheduledTaskItem,
  SchedulerResponse,
  TaskStatus,
} from "../services/backendService";

interface SchedulerPageProps {
  onNavigateHome: () => void;
}

export const SchedulerPage: React.FC<SchedulerPageProps> = ({ onNavigateHome }) => {
  const [tasks, setTasks] = useState<ScheduledTaskItem[]>([]);
  const [activeCount, setActiveCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");

  // Yangi vazifa shakli
  const [text, setText] = useState("");
  const [delayMinutes, setDelayMinutes] = useState(15);
  const [repeat, setRepeat] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeAlarm, setActiveAlarm] = useState<string | null>(null);

  // Tahrirlash modali
  const [editingTask, setEditingTask] = useState<ScheduledTaskItem | null>(null);
  const [editText, setEditText] = useState("");
  const [editDelayMinutes, setEditDelayMinutes] = useState(15);
  const [editRepeatMinutes, setEditRepeatMinutes] = useState(0);
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  const mountedRef = React.useRef(true);

  const fetchTasks = async () => {
    if (!mountedRef.current) return;
    setLoading(true);
    const res: SchedulerResponse = await backendService.getScheduler();
    if (mountedRef.current && res.ok) {
      setTasks(res.tasks || []);
      setActiveCount(res.active_count || 0);
    }
    if (mountedRef.current) {
      setLoading(false);
    }
  };

  useEffect(() => {
    mountedRef.current = true;
    fetchTasks();
    const interval = setInterval(() => {
      if (mountedRef.current) fetchTasks();
    }, 6000);

    // Jonli eslatma signali kelganda bildirishnoma
    const unsubAlarm = backendService.onSchedulerAlarm((data) => {
      if (mountedRef.current) {
        setActiveAlarm(data.text);
        fetchTasks();
      }
    });

    return () => {
      mountedRef.current = false;
      clearInterval(interval);
      unsubAlarm();
    };
  }, []);

  const handleAddTask = async (
    customText?: string,
    customDelay?: number,
    customRepeat?: boolean
  ) => {
    const taskText = (customText || text).trim();
    const delay = customDelay !== undefined ? customDelay : delayMinutes;
    const isRep = customRepeat !== undefined ? customRepeat : repeat;

    if (!taskText || isSubmitting) return;
    setIsSubmitting(true);

    const repeatMins = isRep ? delay : 0;
    const res = await backendService.addSchedulerTask(taskText, delay, repeatMins, "reminder");
    if (res.ok) {
      setText("");
      await fetchTasks();
    }
    setIsSubmitting(false);
  };

  const handleRemoveTask = async (taskId: string) => {
    const ok = await backendService.removeSchedulerTask(taskId);
    if (ok) {
      setTasks((prev) => prev.filter((t) => t.id !== taskId && t.task_id !== taskId));
      setActiveCount((prev) => Math.max(0, prev - 1));
    }
  };

  const handleToggleTask = async (task: ScheduledTaskItem) => {
    const taskId = task.id || task.task_id || "";
    if (!taskId) return;

    if (task.status === "cancelled" || !task.enabled) {
      const ok = await backendService.enableSchedulerTask(taskId);
      if (ok) await fetchTasks();
    } else {
      const ok = await backendService.disableSchedulerTask(taskId);
      if (ok) await fetchTasks();
    }
  };

  const handleExecuteNow = async (taskId: string) => {
    const ok = await backendService.executeSchedulerTask(taskId);
    if (ok) {
      await fetchTasks();
    }
  };

  const handleOpenEdit = (task: ScheduledTaskItem) => {
    setEditingTask(task);
    setEditText(task.data?.text || "");
    setEditDelayMinutes(15);
    setEditRepeatMinutes(task.repeat_seconds ? Math.round(task.repeat_seconds / 60) : 0);
  };

  const handleSaveEdit = async () => {
    if (!editingTask) return;
    const taskId = editingTask.id || editingTask.task_id || "";
    if (!taskId || !editText.trim()) return;

    setIsSavingEdit(true);
    const res = await backendService.editSchedulerTask(
      taskId,
      editText.trim(),
      editDelayMinutes,
      editRepeatMinutes
    );
    if (res.ok) {
      setEditingTask(null);
      await fetchTasks();
    }
    setIsSavingEdit(false);
  };

  const handleClearCompleted = async () => {
    const ok = await backendService.clearCompletedTasks();
    if (ok) {
      await fetchTasks();
    }
  };

  // Status statistikasi
  const stats = useMemo(() => {
    const total = tasks.length;
    let active = 0;
    let repeating = 0;
    let completed = 0;
    let failed = 0;
    let cancelled = 0;

    tasks.forEach((t) => {
      const s = t.status || (t.completed ? "completed" : t.repeat ? "repeating" : "active");
      if (s === "repeating") repeating++;
      else if (s === "completed") completed++;
      else if (s === "failed") failed++;
      else if (s === "cancelled") cancelled++;
      else active++;
    });

    return { total, active, repeating, completed, failed, cancelled };
  }, [tasks]);

  // Filtrlangan vazifalar
  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      const s = t.status || (t.completed ? "completed" : t.repeat ? "repeating" : "active");
      if (filterStatus !== "all" && s !== filterStatus) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const txt = (t.data?.text || "").toLowerCase();
        const id = (t.id || t.task_id || "").toLowerCase();
        if (!txt.includes(q) && !id.includes(q)) return false;
      }
      return true;
    });
  }, [tasks, filterStatus, searchQuery]);

  const renderStatusBadge = (status: TaskStatus | string) => {
    switch (status) {
      case "active":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: 6,
              background: "rgba(16, 185, 129, 0.15)",
              color: "#34d399",
              border: "1px solid rgba(16, 185, 129, 0.3)",
            }}
          >
            <ClockIcon size={11} color="#34d399" />
            <span>Faol</span>
          </span>
        );
      case "repeating":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: 6,
              background: "rgba(245, 158, 11, 0.15)",
              color: "#fbbf24",
              border: "1px solid rgba(245, 158, 11, 0.3)",
            }}
          >
            <RepeatIcon size={11} color="#fbbf24" />
            <span>Takrorlanuvchi</span>
          </span>
        );
      case "completed":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: 6,
              background: "rgba(59, 130, 246, 0.15)",
              color: "#60a5fa",
              border: "1px solid rgba(59, 130, 246, 0.3)",
            }}
          >
            <CheckCircleIcon size={11} color="#60a5fa" />
            <span>Bajarilgan</span>
          </span>
        );
      case "failed":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: 6,
              background: "rgba(239, 68, 68, 0.15)",
              color: "#f87171",
              border: "1px solid rgba(239, 68, 68, 0.3)",
            }}
          >
            <AlertCircleIcon size={11} color="#f87171" />
            <span>Xatolik</span>
          </span>
        );
      case "cancelled":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 11,
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: 6,
              background: "rgba(100, 116, 139, 0.15)",
              color: "#94a3b8",
              border: "1px solid rgba(100, 116, 139, 0.3)",
            }}
          >
            <XCircleIcon size={11} color="#94a3b8" />
            <span>To'xtatilgan</span>
          </span>
        );
      default:
        return null;
    }
  };

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
              background: "rgba(245, 158, 11, 0.15)",
              border: "1px solid rgba(245, 158, 11, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <SchedulerIcon size={20} color="#f59e0b" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600, letterSpacing: "-0.01em" }}>
                Vazifalar Jadvali va Eslatmalar
              </h1>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 12,
                  background: "rgba(245, 158, 11, 0.15)",
                  color: "#f59e0b",
                  fontWeight: 500,
                  border: "1px solid rgba(245, 158, 11, 0.2)",
                }}
              >
                {activeCount} ta faol eslatma
              </span>
            </div>
            <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--text-secondary)" }}>
              5 holatli avtomatik dispetcher: active, repeating, completed, failed, cancelled
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
        {/* Live Alarm Banner */}
        {activeAlarm && (
          <div
            style={{
              background: "rgba(245, 158, 11, 0.15)",
              border: "1px solid rgba(245, 158, 11, 0.4)",
              borderRadius: 12,
              padding: "14px 18px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              color: "#fbbf24",
              boxShadow: "0 4px 20px rgba(245, 158, 11, 0.2)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "rgba(245, 158, 11, 0.25)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <ClockIcon size={18} color="#fbbf24" />
              </div>
              <div>
                <strong style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  Eslatma Vaqti Yetdi:
                </strong>
                <div style={{ fontSize: 15, fontWeight: 600, color: "#ffffff", marginTop: 2 }}>
                  {activeAlarm}
                </div>
              </div>
            </div>
            <button
              onClick={() => setActiveAlarm(null)}
              style={{
                background: "rgba(255, 255, 255, 0.15)",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                borderRadius: 6,
                padding: "6px 14px",
                color: "#ffffff",
                fontSize: 12,
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Tushundim
            </button>
          </div>
        )}

        {/* Quick Presets */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text-secondary)" }}>
            Tezkor Eslatmalar:
          </span>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              onClick={() => handleAddTask("Suv ichish vaqti keldi!", 30, true)}
              style={{
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 10,
                padding: "8px 14px",
                color: "var(--text-primary)",
                fontSize: 12,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <SchedulerIcon size={14} color="#38BDF8" />
              <span>Suv ichish (30 daq)</span>
            </button>
            <button
              onClick={() => handleAddTask("Ko'zlarni 2 daqiqa dam oldiring!", 20, true)}
              style={{
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 10,
                padding: "8px 14px",
                color: "var(--text-primary)",
                fontSize: 12,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <SchedulerIcon size={14} color="#10B981" />
              <span>Ko'zlarni dam oldirish (20 daq)</span>
            </button>
            <button
              onClick={() => handleAddTask("Muhim vazifani tekshirish", 15, false)}
              style={{
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 10,
                padding: "8px 14px",
                color: "var(--text-primary)",
                fontSize: 12,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <ClockIcon size={14} color="#F59E0B" />
              <span>15 daqiqadan keyin eslat</span>
            </button>
            <button
              onClick={() => handleAddTask("1 soatlik diqqat sessiyasi yakuni", 60, false)}
              style={{
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 10,
                padding: "8px 14px",
                color: "var(--text-primary)",
                fontSize: 12,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <ClockIcon size={14} color="#818CF8" />
              <span>1 soatlik sessiya</span>
            </button>
          </div>
        </div>

        {/* Custom Task Form */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid var(--border-subtle)",
            borderRadius: 14,
            padding: "18px 22px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, fontWeight: 500 }}>
            <SparklesIcon size={15} color="#f59e0b" />
            <span>Yangi vazifa yoki eslatma rejalashtirish</span>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleAddTask();
            }}
            style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}
          >
            <input
              type="text"
              placeholder="Eslatma matni (masalan: Uchrashuvga chiqish, Dori ichish, Tizim zaxirasini olish...)"
              value={text}
              onChange={(e) => setText(e.target.value)}
              style={{
                flex: "2 1 300px",
                background: "rgba(0, 0, 0, 0.25)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 8,
                padding: "10px 14px",
                color: "var(--text-primary)",
                fontSize: 13,
                outline: "none",
              }}
            />

            <select
              value={delayMinutes}
              onChange={(e) => setDelayMinutes(Number(e.target.value))}
              style={{
                flex: "1 1 140px",
                background: "rgba(0, 0, 0, 0.25)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 8,
                padding: "10px 12px",
                color: "var(--text-primary)",
                fontSize: 13,
                outline: "none",
              }}
            >
              <option value={1}>1 daqiqadan keyin</option>
              <option value={5}>5 daqiqadan keyin</option>
              <option value={15}>15 daqiqadan keyin</option>
              <option value={30}>30 daqiqadan keyin</option>
              <option value={60}>1 soatdan keyin</option>
              <option value={120}>2 soatdan keyin</option>
              <option value={1440}>24 soatdan keyin</option>
            </select>

            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontSize: 12,
                color: "var(--text-secondary)",
                cursor: "pointer",
                userSelect: "none",
              }}
            >
              <input
                type="checkbox"
                checked={repeat}
                onChange={(e) => setRepeat(e.target.checked)}
                style={{ accentColor: "#f59e0b" }}
              />
              <span>Har safar takrorlash</span>
            </label>

            <button
              type="submit"
              disabled={!text.trim() || isSubmitting}
              style={{
                background: "#f59e0b",
                color: "#18181b",
                border: "none",
                borderRadius: 8,
                padding: "10px 20px",
                fontSize: 13,
                fontWeight: 600,
                cursor: !text.trim() || isSubmitting ? "not-allowed" : "pointer",
                opacity: !text.trim() || isSubmitting ? 0.6 : 1,
                transition: "all 0.15s ease",
              }}
            >
              {isSubmitting ? "Rejalashtirilmoqda..." : "Rejalashtirish"}
            </button>
          </form>
        </div>

        {/* Filter and Search Bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          {/* Status Tabs */}
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {[
              { id: "all", label: `Barchasi (${stats.total})` },
              { id: "active", label: `Faol (${stats.active})` },
              { id: "repeating", label: `Takrorlanuvchi (${stats.repeating})` },
              { id: "completed", label: `Bajarilgan (${stats.completed})` },
              { id: "failed", label: `Xatolik (${stats.failed})` },
              { id: "cancelled", label: `To'xtatilgan (${stats.cancelled})` },
            ].map((tab) => {
              const active = filterStatus === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setFilterStatus(tab.id)}
                  style={{
                    background: active ? "rgba(245, 158, 11, 0.2)" : "rgba(255, 255, 255, 0.04)",
                    border: active ? "1px solid rgba(245, 158, 11, 0.4)" : "1px solid var(--border-subtle)",
                    color: active ? "#fbbf24" : "var(--text-secondary)",
                    borderRadius: 8,
                    padding: "6px 12px",
                    fontSize: 12,
                    fontWeight: active ? 600 : 400,
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Search Box & Clear Completed */}
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                background: "rgba(0, 0, 0, 0.25)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 8,
                padding: "6px 10px",
                width: 220,
              }}
            >
              <SearchIcon size={13} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Vazifalardan izlash..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: "var(--text-primary)",
                  fontSize: 12,
                  width: "100%",
                }}
              />
            </div>

            {stats.completed > 0 && (
              <button
                onClick={handleClearCompleted}
                style={{
                  background: "rgba(239, 68, 68, 0.1)",
                  border: "1px solid rgba(239, 68, 68, 0.2)",
                  color: "#f87171",
                  borderRadius: 8,
                  padding: "6px 12px",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Bajarilganlarni tozalash
              </button>
            )}
          </div>
        </div>

        {/* Task List */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {loading ? (
            <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
              Vazifalar yuklanmoqda...
            </div>
          ) : filteredTasks.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "48px 20px",
                color: "var(--text-muted)",
                border: "1px dashed var(--border-subtle)",
                borderRadius: 12,
                fontSize: 13,
              }}
            >
              Hech qanday vazifa topilmadi. Yuqoridagi shakl orqali yangi eslatma rejalashtirishingiz mumkin.
            </div>
          ) : (
            filteredTasks.map((t) => {
              const taskId = t.id || t.task_id || "";
              const status = t.status || (t.completed ? "completed" : t.repeat ? "repeating" : "active");
              const isInactive = status === "completed" || status === "cancelled";

              return (
                <div
                  key={taskId}
                  style={{
                    background: isInactive ? "rgba(255, 255, 255, 0.015)" : "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 12,
                    padding: "16px 20px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 16,
                    flexWrap: "wrap",
                    opacity: isInactive ? 0.75 : 1,
                    transition: "all 0.15s ease",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 14, flex: 1 }}>
                    <div style={{ marginTop: 2 }}>{renderStatusBadge(status)}</div>

                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      <div
                        style={{
                          fontSize: 14,
                          fontWeight: 500,
                          color: "var(--text-primary)",
                          textDecoration: status === "completed" ? "line-through" : "none",
                        }}
                      >
                        {t.data?.text || "Vazifa"}
                      </div>

                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          fontSize: 11,
                          color: "var(--text-muted)",
                          flexWrap: "wrap",
                        }}
                      >
                        <span>Reja vaqti: {t.run_at}</span>
                        {t.last_run && <span>Oxirgi ijro: {t.last_run}</span>}
                        {t.repeat_seconds && t.repeat_seconds > 0 ? (
                          <span>Har {Math.round(t.repeat_seconds / 60)} daqiqada</span>
                        ) : null}
                        <span style={{ fontFamily: "monospace", opacity: 0.6 }}>ID: {taskId.slice(0, 16)}</span>
                      </div>

                      {t.last_error && (
                        <div
                          style={{
                            fontSize: 11,
                            color: "#f87171",
                            background: "rgba(239, 68, 68, 0.1)",
                            padding: "4px 8px",
                            borderRadius: 6,
                            marginTop: 2,
                          }}
                        >
                          Xatolik: {t.last_error}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    {/* Execute Now */}
                    <button
                      onClick={() => handleExecuteNow(taskId)}
                      title="Darhol bajarish"
                      style={{
                        background: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-secondary)",
                        borderRadius: 6,
                        padding: "6px 8px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: 11,
                      }}
                    >
                      <PlayIcon size={12} color="#34d399" />
                      <span>Ijro</span>
                    </button>

                    {/* Enable / Disable */}
                    <button
                      onClick={() => handleToggleTask(t)}
                      title={status === "cancelled" ? "Faollashtirish" : "To'xtatish"}
                      style={{
                        background: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-secondary)",
                        borderRadius: 6,
                        padding: "6px 8px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: 11,
                      }}
                    >
                      {status === "cancelled" ? (
                        <>
                          <CheckIcon size={12} color="#38bdf8" />
                          <span>Yoqish</span>
                        </>
                      ) : (
                        <>
                          <PauseIcon size={12} color="#fbbf24" />
                          <span>To'xtatish</span>
                        </>
                      )}
                    </button>

                    {/* Edit */}
                    <button
                      onClick={() => handleOpenEdit(t)}
                      title="Tahrirlash"
                      style={{
                        background: "rgba(255, 255, 255, 0.05)",
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-secondary)",
                        borderRadius: 6,
                        padding: "6px 8px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: 11,
                      }}
                    >
                      <EditIcon size={12} />
                      <span>Tahrir</span>
                    </button>

                    {/* Remove */}
                    <button
                      onClick={() => handleRemoveTask(taskId)}
                      title="O'chirish"
                      style={{
                        background: "rgba(239, 68, 68, 0.1)",
                        border: "1px solid rgba(239, 68, 68, 0.2)",
                        color: "#f87171",
                        borderRadius: 6,
                        padding: "6px 8px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: 11,
                      }}
                    >
                      <TrashIcon size={12} />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {editingTask && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.7)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 100,
            padding: 20,
          }}
          onClick={() => setEditingTask(null)}
        >
          <div
            style={{
              background: "#0e1422",
              border: "1px solid var(--border-subtle)",
              borderRadius: 14,
              padding: 24,
              width: "100%",
              maxWidth: 480,
              display: "flex",
              flexDirection: "column",
              gap: 16,
              boxShadow: "0 10px 40px rgba(0, 0, 0, 0.5)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <EditIcon size={16} color="#f59e0b" />
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Vazifani Tahrirlash</h3>
              </div>
              <button
                onClick={() => setEditingTask(null)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                }}
              >
                <CloseIcon size={14} />
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Eslatma matni:</label>
              <input
                type="text"
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                style={{
                  background: "rgba(0, 0, 0, 0.3)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: 8,
                  padding: "10px 12px",
                  color: "var(--text-primary)",
                  fontSize: 13,
                  outline: "none",
                }}
              />
            </div>

            <div style={{ display: "flex", gap: 12 }}>
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
                <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Keyinroqqa surish:</label>
                <select
                  value={editDelayMinutes}
                  onChange={(e) => setEditDelayMinutes(Number(e.target.value))}
                  style={{
                    background: "rgba(0, 0, 0, 0.3)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "10px 12px",
                    color: "var(--text-primary)",
                    fontSize: 13,
                    outline: "none",
                  }}
                >
                  <option value={1}>1 daqiqadan keyin</option>
                  <option value={5}>5 daqiqadan keyin</option>
                  <option value={15}>15 daqiqadan keyin</option>
                  <option value={30}>30 daqiqadan keyin</option>
                  <option value={60}>1 soatdan keyin</option>
                  <option value={120}>2 soatdan keyin</option>
                </select>
              </div>

              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
                <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>Takrorlanish oralig'i:</label>
                <select
                  value={editRepeatMinutes}
                  onChange={(e) => setEditRepeatMinutes(Number(e.target.value))}
                  style={{
                    background: "rgba(0, 0, 0, 0.3)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 8,
                    padding: "10px 12px",
                    color: "var(--text-primary)",
                    fontSize: 13,
                    outline: "none",
                  }}
                >
                  <option value={0}>Bir marta (takrorlanmas)</option>
                  <option value={15}>Har 15 daqiqada</option>
                  <option value={30}>Har 30 daqiqada</option>
                  <option value={60}>Har 1 soatda</option>
                  <option value={120}>Har 2 soatda</option>
                  <option value={1440}>Har 24 soatda</option>
                </select>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 8 }}>
              <button
                onClick={() => setEditingTask(null)}
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-secondary)",
                  padding: "8px 16px",
                  borderRadius: 8,
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Bekor qilish
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={!editText.trim() || isSavingEdit}
                style={{
                  background: "#f59e0b",
                  color: "#18181b",
                  border: "none",
                  padding: "8px 18px",
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: !editText.trim() || isSavingEdit ? "not-allowed" : "pointer",
                }}
              >
                {isSavingEdit ? "Saqlanmoqda..." : "Saqlash"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default SchedulerPage;
