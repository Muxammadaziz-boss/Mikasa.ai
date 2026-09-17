// ========== DevicesPage.tsx ==========
// Mikasa AI v8.0.0 — Phase 40: Universal Account & Device Management 2.0
// Multi-Device management page: list, select, rename, revoke

import React, { useState, useEffect, useCallback } from "react";
import {
  backendService,
  UserDevice,
} from "../services/backendService";
import {
  LaptopIcon,
  RefreshIcon,
  CheckIcon,
  TrashIcon,
  CopyIcon,
  AlertTriangleIcon,
  ClockIcon,
} from "../components/icons/Icons";

interface DevicesPageProps {
  onNavigateHome: () => void;
}

export const DevicesPage: React.FC<DevicesPageProps> = ({ onNavigateHome }) => {
  const [devices, setDevices] = useState<UserDevice[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Rename modal state
  const [renameModalOpen, setRenameModalOpen] = useState<boolean>(false);
  const [deviceToRename, setDeviceToRename] = useState<UserDevice | null>(null);
  const [newName, setNewName] = useState<string>("");
  const [renameError, setRenameError] = useState<string | null>(null);
  const [renameSubmitting, setRenameSubmitting] = useState<boolean>(false);

  // Revoke modal state
  const [revokeModalOpen, setRevokeModalOpen] = useState<boolean>(false);
  const [deviceToRevoke, setDeviceToRevoke] = useState<UserDevice | null>(null);
  const [revokeSubmitting, setRevokeSubmitting] = useState<boolean>(false);

  // Notification message
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const showNotification = (type: "success" | "error", text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const loadDevices = useCallback(async () => {
    setLoading(true);
    try {
      const res = await backendService.getDevices();
      if (res.ok && res.devices) {
        setDevices(res.devices);
        setSelectedDeviceId(res.selected_device_id || null);
      }
    } catch (err: any) {
      showNotification("error", `Qurilmalarni yuklashda xatolik: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDevices();

    // WebSocket real-time updates
    const unsubscribe = backendService.subscribe((msg: any) => {
      if (
        msg.type === "DEVICE_SELECTED" ||
        msg.type === "DEVICE_RENAMED" ||
        msg.type === "DEVICE_REVOKED" ||
        msg.type === "DEVICE_ADDED" ||
        msg.action === "DEVICE_SELECTED" ||
        msg.action === "DEVICE_RENAMED"
      ) {
        loadDevices();
      }
    });

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [loadDevices]);

  const handleSelectDevice = async (dev: UserDevice) => {
    try {
      const res = await backendService.selectDevice(dev.device_id);
      if (res.ok) {
        setSelectedDeviceId(dev.device_id);
        showNotification("success", `'${dev.name}' kompyuteri faol boshqaruv uchun tanlandi.`);
      } else {
        showNotification("error", res.error || "Qurilmani tanlashda xatolik yuz berdi.");
      }
    } catch (err: any) {
      showNotification("error", err.message || "Server xatosi");
    }
  };

  const openRenameModal = (dev: UserDevice) => {
    setDeviceToRename(dev);
    setNewName(dev.name);
    setRenameError(null);
    setRenameModalOpen(true);
  };

  const submitRename = async () => {
    if (!deviceToRename) return;
    const cleanName = newName.trim();
    if (!cleanName) {
      setRenameError("Qurilma nomi bo'sh bo'lishi mumkin emas.");
      return;
    }
    if (cleanName.length > 64) {
      setRenameError("Qurilma nomi 64 belgidan oshmasligi kerak.");
      return;
    }

    setRenameSubmitting(true);
    try {
      const res = await backendService.renameDevice(deviceToRename.device_id, cleanName);
      if (res.ok && res.device) {
        setDevices((prev) =>
          prev.map((d) => (d.id === res.device!.id ? res.device! : d))
        );
        setRenameModalOpen(false);
        showNotification("success", "Qurilma nomi muvaffaqiyatli o'zgartirildi.");
      } else {
        setRenameError(res.error || "Nomni o'zgartirishda xatolik.");
      }
    } catch (err: any) {
      setRenameError(err.message || "Server bilan aloqa uzildi.");
    } finally {
      setRenameSubmitting(false);
    }
  };

  const openRevokeModal = (dev: UserDevice) => {
    setDeviceToRevoke(dev);
    setRevokeModalOpen(true);
  };

  const submitRevoke = async () => {
    if (!deviceToRevoke) return;
    setRevokeSubmitting(true);
    try {
      const res = await backendService.revokeDevice(deviceToRevoke.device_id);
      if (res.ok) {
        setDevices((prev) => prev.filter((d) => d.id !== deviceToRevoke.id && d.device_id !== deviceToRevoke.device_id));
        if (selectedDeviceId === deviceToRevoke.device_id || selectedDeviceId === deviceToRevoke.id) {
          setSelectedDeviceId(null);
        }
        setRevokeModalOpen(false);
        showNotification("success", `'${deviceToRevoke.name}' muvaffaqiyatli o'chirildi va barcha sessiyalar to'xtatildi.`);
      } else {
        showNotification("error", res.error || "Qurilmani bekor qilishda xatolik.");
      }
    } catch (err: any) {
      showNotification("error", err.message || "Server xatosi");
    } finally {
      setRevokeSubmitting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(text);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "online":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Onlayn
          </span>
        );
      case "standby":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-950/80 text-amber-400 border border-amber-800/60">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Kutish rejimi
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-neutral-900 text-neutral-400 border border-neutral-800">
            <span className="w-1.5 h-1.5 rounded-full bg-neutral-500" />
            Oflayn
          </span>
        );
    }
  };

  const formatTimestamp = (ts?: number | null) => {
    if (!ts) return "Mavjud emas";
    return new Date(ts * 1000).toLocaleString("uz-UZ", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const onlineCount = devices.filter((d) => d.status.toLowerCase() === "online").length;
  const selectedDevice = devices.find((d) => d.device_id === selectedDeviceId || d.id === selectedDeviceId);

  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-800/80 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-950/60 border border-emerald-800/50 text-emerald-400 shadow-lg shadow-emerald-950/40">
              <LaptopIcon size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-neutral-100 tracking-tight">
                Qurilmalar Boshqaruvi
              </h1>
              <p className="text-xs text-neutral-400 mt-0.5">
                Multi-User Identity → Account → Multi-Device arxitekturasi
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onNavigateHome && (
            <button
              type="button"
              onClick={onNavigateHome}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-900 hover:bg-neutral-800 text-neutral-300 text-xs font-medium border border-neutral-700/60 transition-colors cursor-pointer"
            >
              <span>← Bosh sahifa</span>
            </button>
          )}
          <button
            type="button"
            onClick={loadDevices}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-neutral-800/80 hover:bg-neutral-700/80 text-neutral-200 text-xs font-medium border border-neutral-700/60 transition-colors cursor-pointer"
          >
            <RefreshIcon size={14} className={loading ? "animate-spin" : ""} />
            <span>Yangilash</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {message && (
        <div
          className={`p-3 rounded-xl border text-xs font-medium flex items-center justify-between animate-in fade-in duration-150 ${
            message.type === "success"
              ? "bg-emerald-950/40 border-emerald-800/80 text-emerald-300"
              : "bg-red-950/40 border-red-800/80 text-red-300"
          }`}
        >
          <span>{message.text}</span>
          <button
            type="button"
            onClick={() => setMessage(null)}
            className="text-neutral-400 hover:text-neutral-200 ml-4 cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800/80 backdrop-blur-sm">
          <div className="text-xs text-neutral-400 font-medium">Jami Kompyuterlar</div>
          <div className="text-2xl font-bold text-neutral-100 mt-1">{devices.length}</div>
          <div className="text-[11px] text-neutral-500 mt-1">Sizning hisobingizga ulangan</div>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800/80 backdrop-blur-sm">
          <div className="text-xs text-neutral-400 font-medium">Onlayn Holatda</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{onlineCount}</div>
          <div className="text-[11px] text-neutral-500 mt-1">Aloqaga tayyor kompyuterlar</div>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800/80 backdrop-blur-sm">
          <div className="text-xs text-neutral-400 font-medium">Faol Tanlangan Kompyuter</div>
          <div className="text-lg font-bold text-neutral-100 mt-1 truncate">
            {selectedDevice ? selectedDevice.name : "Tanlanmagan"}
          </div>
          <div className="text-[11px] text-neutral-500 mt-1 truncate">
            {selectedDevice ? `ID: ${selectedDevice.device_id}` : "Buyruqlar uchun birorta kompyuter tanlang"}
          </div>
        </div>
      </div>

      {/* Device List */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-neutral-200 uppercase tracking-wider">
          Kompyuterlar Ro'yxati ({devices.length})
        </h2>

        {loading && devices.length === 0 ? (
          <div className="p-12 text-center text-neutral-500 text-sm">
            Kompyuterlar yuklanmoqda...
          </div>
        ) : devices.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-neutral-900/40 border border-neutral-800/80 space-y-3">
            <LaptopIcon size={36} className="mx-auto text-neutral-600" />
            <h3 className="text-base font-medium text-neutral-300">Kompyuterlar topilmadi</h3>
            <p className="text-xs text-neutral-500 max-w-md mx-auto">
              Hisobingizga birorta ham kompyuter ulanmagan. Mikasa Desktop ilovasi orqali kompyuteringizni ro'yxatdan o'tkazing.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {devices.map((dev) => {
              const isSelected = dev.device_id === selectedDeviceId || dev.id === selectedDeviceId;
              return (
                <div
                  key={dev.id}
                  className={`p-5 rounded-2xl border transition-all duration-200 backdrop-blur-sm relative flex flex-col justify-between ${
                    isSelected
                      ? "bg-neutral-900/90 border-emerald-500/50 shadow-xl shadow-emerald-950/20 ring-1 ring-emerald-500/20"
                      : "bg-neutral-900/50 border-neutral-800/80 hover:border-neutral-700/80"
                  }`}
                >
                  <div>
                    {/* Top Row: Title, Status, and Active Badge */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-semibold text-neutral-100 truncate">
                            {dev.name}
                          </h3>
                          {isSelected && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                              <CheckIcon size={10} />
                              Faol
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-neutral-500 font-mono truncate">
                            {dev.device_id}
                          </span>
                          <button
                            type="button"
                            onClick={() => copyToClipboard(dev.device_id)}
                            className="text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer"
                            title="Nusxa olish"
                          >
                            <CopyIcon size={12} />
                          </button>
                          {copiedId === dev.device_id && (
                            <span className="text-[10px] text-emerald-400">Nusxa olindi!</span>
                          )}
                        </div>
                      </div>

                      <div>{getStatusBadge(dev.status)}</div>
                    </div>

                    {/* Metadata Specs */}
                    <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-neutral-800/60 text-xs">
                      <div>
                        <span className="text-neutral-500 block text-[10px] uppercase">Xost nomi</span>
                        <span className="text-neutral-300 font-medium truncate block">
                          {dev.hostname || "Aniqlanmagan"}
                        </span>
                      </div>
                      <div>
                        <span className="text-neutral-500 block text-[10px] uppercase">Platforma</span>
                        <span className="text-neutral-300 font-medium capitalize block">
                          {dev.platform || "Windows"}
                        </span>
                      </div>
                      <div>
                        <span className="text-neutral-500 block text-[10px] uppercase">Agent Versiyasi</span>
                        <span className="text-neutral-300 font-mono block">
                          v{dev.agent_version || "8.0.0"}
                        </span>
                      </div>
                      <div>
                        <span className="text-neutral-500 block text-[10px] uppercase">Oxirgi faollik</span>
                        <span className="text-neutral-300 flex items-center gap-1">
                          <ClockIcon size={11} className="text-neutral-500" />
                          {formatTimestamp(dev.last_seen_at || dev.last_heartbeat_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions Footer */}
                  <div className="flex items-center justify-between gap-2 mt-5 pt-3 border-t border-neutral-800/60">
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => openRenameModal(dev)}
                        className="px-2.5 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-medium border border-neutral-700/60 transition-colors cursor-pointer"
                      >
                        Nomlash
                      </button>
                      <button
                        type="button"
                        onClick={() => openRevokeModal(dev)}
                        className="p-1.5 rounded-lg bg-neutral-800/40 hover:bg-red-950/50 text-neutral-400 hover:text-red-400 border border-neutral-700/40 hover:border-red-800/60 transition-colors cursor-pointer"
                        title="Kompyuterni bekor qilish / o'chirish"
                      >
                        <TrashIcon size={14} />
                      </button>
                    </div>

                    <div>
                      {isSelected ? (
                        <span className="text-xs text-emerald-400 font-medium flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/40">
                          <CheckIcon size={12} />
                          Tanlangan
                        </span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleSelectDevice(dev)}
                          className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950 transition-all cursor-pointer"
                        >
                          Faol Tanlash
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Rename Modal */}
      {renameModalOpen && deviceToRename && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl animate-in zoom-in-95 duration-150">
            <div>
              <h3 className="text-base font-semibold text-neutral-100">
                Kompyuter nomini o'zgartirish
              </h3>
              <p className="text-xs text-neutral-400 mt-1">
                Ushbu kompyuterni oson ajratib olish uchun qulay nom bering (masalan: "Gaming PC", "Ofis Noutbuk").
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-neutral-300 block">
                Do'stona nom
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Kompyuter nomini kiriting"
                maxLength={64}
                className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-800 text-neutral-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                autoFocus
              />
              {renameError && (
                <p className="text-xs text-red-400">{renameError}</p>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setRenameModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs text-neutral-300 hover:bg-neutral-800 transition-colors cursor-pointer"
              >
                Bekor qilish
              </button>
              <button
                type="button"
                onClick={submitRename}
                disabled={renameSubmitting}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium shadow-md shadow-emerald-950 transition-colors cursor-pointer"
              >
                {renameSubmitting ? "Saqlanmoqda..." : "Saqlash"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Revoke Modal */}
      {revokeModalOpen && deviceToRevoke && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-red-950/60 border border-red-800/60 text-red-400 flex-shrink-0">
                <AlertTriangleIcon size={20} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-neutral-100">
                  Kompyuterni o'chirishni tasdiqlang
                </h3>
                <p className="text-xs text-neutral-400 mt-1">
                  Haqiqatan ham <strong className="text-neutral-200">'{deviceToRevoke.name}'</strong> kompyuterini hisobingizdan o'chirmoqchimisiz?
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-800/80 text-xs text-neutral-400 space-y-1">
              <p className="font-semibold text-neutral-300">Xavfsizlik oqibatlari:</p>
              <ul className="list-disc pl-4 space-y-0.5 text-neutral-400">
                <li>Ushbu kompyuterdagi barcha faol masofaviy sessiyalar darhol to'xtatiladi.</li>
                <li>Foydalanuvchi ruxsatlari profili bekor qilinadi.</li>
                <li>Kompyuter qayta ulangunga qadar unga buyruq yuborib bo'lmaydi.</li>
              </ul>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setRevokeModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs text-neutral-300 hover:bg-neutral-800 transition-colors cursor-pointer"
              >
                Bekor qilish
              </button>
              <button
                type="button"
                onClick={submitRevoke}
                disabled={revokeSubmitting}
                className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow-md shadow-red-950 transition-colors cursor-pointer"
              >
                {revokeSubmitting ? "O'chirilmoqda..." : "Ha, o'chirilsin"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
