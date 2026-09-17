// ========== DeviceSelector.tsx ==========
// Mikasa AI v8.0.0 — Phase 40: Multi-Device Selector Dropdown
// Quick device switching and status indicator for header/navigation

import React, { useState, useEffect, useRef, useCallback } from "react";
import { backendService, UserDevice } from "../services/backendService";
import { LaptopIcon, CheckIcon, ExternalLinkIcon } from "./icons/Icons";

interface DeviceSelectorProps {
  onNavigateToDevices?: () => void;
  className?: string;
}

export const DeviceSelector: React.FC<DeviceSelectorProps> = ({
  onNavigateToDevices,
  className = "",
}) => {
  const [devices, setDevices] = useState<UserDevice[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchDevices = useCallback(async () => {
    try {
      const res = await backendService.getDevices();
      if (res.ok && res.devices) {
        setDevices(res.devices);
        setSelectedDeviceId(res.selected_device_id || null);
      }
    } catch (err) {
      console.error("Error fetching devices:", err);
    }
  }, []);

  useEffect(() => {
    fetchDevices();

    // WebSocket tinglovchisi orqali real-time sinxronlash
    const unsubscribe = backendService.subscribe((msg: any) => {
      if (
        msg.type === "DEVICE_SELECTED" ||
        msg.type === "DEVICE_RENAMED" ||
        msg.type === "DEVICE_REVOKED" ||
        msg.type === "DEVICE_ADDED" ||
        msg.action === "DEVICE_SELECTED" ||
        msg.action === "DEVICE_RENAMED"
      ) {
        fetchDevices();
      }
    });

    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [fetchDevices]);

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = async (dev: UserDevice) => {
    setLoading(true);
    try {
      const res = await backendService.selectDevice(dev.device_id);
      if (res.ok) {
        setSelectedDeviceId(dev.device_id);
        setIsOpen(false);
      }
    } catch (err) {
      console.error("Error selecting device:", err);
    } finally {
      setLoading(false);
    }
  };

  const selectedDevice = devices.find(
    (d) => d.device_id === selectedDeviceId || d.id === selectedDeviceId
  );

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "online":
        return "bg-emerald-500 shadow-emerald-500/50";
      case "standby":
        return "bg-amber-500 shadow-amber-500/50";
      default:
        return "bg-neutral-500 shadow-neutral-500/50";
    }
  };

  return (
    <div ref={dropdownRef} className={`relative inline-block text-left ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-neutral-900/60 hover:bg-neutral-800/80 border border-neutral-700/60 text-xs font-medium text-neutral-200 transition-all duration-150 backdrop-blur-md focus:outline-none focus:ring-1 focus:ring-emerald-500/50 cursor-pointer"
        title="Faol kompyuterni tanlash"
      >
        <LaptopIcon size={14} className="text-emerald-400" />
        <span className="max-w-[120px] truncate font-medium">
          {selectedDevice ? selectedDevice.name : "Kompyuter tanlang"}
        </span>
        {selectedDevice && (
          <span
            className={`w-2 h-2 rounded-full shadow-sm ${getStatusColor(
              selectedDevice.status
            )}`}
          />
        )}
        <svg
          className={`w-3.5 h-3.5 text-neutral-400 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 rounded-xl bg-neutral-900/95 border border-neutral-800 shadow-2xl backdrop-blur-xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div className="px-3 py-2 border-b border-neutral-800/80 bg-neutral-950/40">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400">
              Ulangan Kompyuterlar
            </span>
          </div>

          <div className="max-h-56 overflow-y-auto p-1 divide-y divide-neutral-800/40">
            {devices.length === 0 ? (
              <div className="px-3 py-3 text-center text-xs text-neutral-500">
                Ulangan kompyuterlar topilmadi
              </div>
            ) : (
              devices.map((dev) => {
                const isSelected =
                  dev.device_id === selectedDeviceId || dev.id === selectedDeviceId;
                return (
                  <button
                    key={dev.id}
                    type="button"
                    onClick={() => handleSelect(dev)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left text-xs transition-colors cursor-pointer ${
                      isSelected
                        ? "bg-emerald-950/40 text-emerald-300 font-medium"
                        : "hover:bg-neutral-800/60 text-neutral-300"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0 pr-2">
                      <span
                        className={`w-2 h-2 rounded-full flex-shrink-0 ${getStatusColor(
                          dev.status
                        )}`}
                      />
                      <div className="truncate">
                        <div className="truncate font-medium text-neutral-200">
                          {dev.name}
                        </div>
                        <div className="text-[10px] text-neutral-500 truncate font-mono">
                          {dev.device_id}
                        </div>
                      </div>
                    </div>

                    {isSelected && (
                      <CheckIcon size={14} className="text-emerald-400 flex-shrink-0" />
                    )}
                  </button>
                );
              })
            )}
          </div>

          {onNavigateToDevices && (
            <div className="p-1 border-t border-neutral-800/80 bg-neutral-950/40">
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  onNavigateToDevices();
                }}
                className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-emerald-400 hover:text-emerald-300 hover:bg-emerald-950/30 transition-colors font-medium cursor-pointer"
              >
                <span>Barcha qurilmalarni boshqarish</span>
                <ExternalLinkIcon size={12} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
