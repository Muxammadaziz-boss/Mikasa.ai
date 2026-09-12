// ========== SchedulerPage.tsx ==========
// Mikasa AI 7.1.0 — Rejalashtiruvchi va Eslatmalar Tizimi
// agent_scheduler.py va scheduled_tasks.json bilan real vaqtda bog'langan

import React, { useState, useEffect } from "react";
import {
  SchedulerIcon,
  HomeIcon,
  SparklesIcon,
  TrashIcon,
  CommandsIcon,
} from "../components/icons/Icons";
import {
  backendService,
  ScheduledTaskItem,
  SchedulerResponse,
} from "../services/backendService";

interface SchedulerPageProps {
  onNavigateHome: () => void;
}

export const SchedulerPage: React.FC<SchedulerPageProps> = ({ onNavigateHome }) => {
  const [tasks, setTasks] = useState<ScheduledTaskItem[]>([]);
  const [activeCount, setActiveCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  // Yangi vazifa shakli
  const [text, setText] = useState("");
  const [delayMinutes, setDelayMinutes] = useState(15);
  const [repeat, setRepeat] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeAlarm, setActiveAlarm] = useState<string | null>(null);

  const fetchTasks = async () => {
    setLoading(true);
    const res: SchedulerResponse = await backendService.getScheduler();
    if (res.ok) {
      setTasks(res.tasks || []);
      setActiveCount(res.active_count || 0);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 6000);

    // Jonli eslatma signali kelganda bildirishnoma
    const unsub = backendService.onSchedulerAlarm((data) => {
      setActiveAlarm(data.text);
      fetchTasks();
    });

    return () => {
      clearInterval(interval);
      unsub();
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
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
      setActiveCount((prev) => Math.max(0, prev - 1));
    }
  };

  const handleClearCompleted = async () => {
    const ok = await backendService.clearCompletedTasks();
    if (ok) {
      await fetchTasks();
    }
  };

  const activeTasks = tasks.filter((t) => !t.completed);
  const completedTasks = tasks.filter((t) => t.completed);

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
                Rejalashtiruvchi
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
              Vaqtli topshiriqlar, eslatmalar va avtomatik reja dispetcheri
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
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span style={{ fontSize: 20 }}>⏰</span>
              <div>
                <strong style={{ fontSize: 13 }}>Vaqt keldi! Eslatma:</strong>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#ffffff", marginTop: 2 }}>
                  {activeAlarm}
                </div>
              </div>
            </div>
            <button
              onClick={() => setActiveAlarm(null)}
              style={{
                background: "rgba(255, 255, 255, 0.1)",
                border: "none",
                borderRadius: 6,
                padding: "6px 12px",
                color: "#ffffff",
                fontSize: 12,
                cursor: "pointer",
              }}
            >
              Tushundim
            </button>
          </div>
        )}

        {/* Quick Preset Reminders */}
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
              <CommandsIcon size={14} color="#F59E0B" />
              <span>15 daqiqadan keyin eslat</span>
            </button>
            <button
              onClick={() => handleAddTask("1 soatlik reja yakuni", 60, false)}
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
                gap: 6,
              }}
            >
              <span>⏰ 1 soatdan keyin eslat</span>
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
            <span>Yangi vazifa yoki eslatma yaratish</span>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <input
              type="text"
              placeholder="Eslatma matni (masalan: Uchrashuvga chiqish, Dori ichish...)"
              value={text}
              onChange={(e) => setText(e.target.value)}
              style={{
                flex: "2 1 320px",
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
              onClick={() => handleAddTask()}
              disabled={!text.trim() || isSubmitting}
              style={{
                background: "#f59e0b",
                color: "#18181b",
                border: "none",
                borderRadius: 8,
                padding: "0 18px",
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {isSubmitting ? "Rejalashtirilmoqda..." : "Rejalashtirish"}
            </button>
          </div>
        </div>

        {/* Active Tasks */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Faol Vazifalar ({activeTasks.length})</h2>
          </div>

          {loading ? (
            <div style={{ textAlign: "center", padding: "20px", color: "var(--text-secondary)" }}>
              Vazifalar yuklanmoqda...
            </div>
          ) : activeTasks.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "32px",
                color: "var(--text-muted)",
                border: "1px dashed var(--border-subtle)",
                borderRadius: 10,
              }}
            >
              Hozircha faol eslatmalar yo'q. Yuqoridagi tezkor tugmalar orqali qo'shing!
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {activeTasks.map((t) => (
                <div
                  key={t.id}
                  style={{
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: 10,
                    padding: "14px 18px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 16,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span style={{ fontSize: 16 }}>⏰</span>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 500 }}>{t.data?.text || "Eslatma"}</div>
                      <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                        Bajarilish vaqti: {t.run_at} {t.repeat ? "• Takrorlanuvchi" : ""}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleRemoveTask(t.id)}
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
                  >
                    <TrashIcon size={12} />
                    <span>Bekor qilish</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Completed Tasks */}
        {completedTasks.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 style={{ margin: 0, fontSize: 14, fontWeight: 500, color: "var(--text-secondary)" }}>
                Bajarilgan Vazifalar ({completedTasks.length})
              </h2>
              <button
                onClick={handleClearCompleted}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-muted)",
                  fontSize: 12,
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                Tarixni tozalash
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {completedTasks.slice(-5).map((t) => (
                <div
                  key={t.id}
                  style={{
                    background: "rgba(255, 255, 255, 0.015)",
                    border: "1px solid rgba(255, 255, 255, 0.03)",
                    borderRadius: 8,
                    padding: "10px 14px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    opacity: 0.6,
                  }}
                >
                  <span style={{ fontSize: 13, textDecoration: "line-through" }}>
                    {t.data?.text || "Vazifa"}
                  </span>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Bajarilgan</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default SchedulerPage;
