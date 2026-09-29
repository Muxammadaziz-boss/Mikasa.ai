// ========== DeviceSelector.tsx ==========
// Misa AI v9.0.0 - Multi-Device Selector Dropdown
// Bioluminescent Void dizayn tizimiga mos — inline styles (Tailwind yo'q)

import React, { useState, useEffect, useRef, useCallback } from "react";
import { backendService, UserDevice } from "../services/backendService";
import { LaptopIcon, CheckIcon, ExternalLinkIcon } from "./icons/Icons";

interface DeviceSelectorProps {
  onNavigateToDevices?: () => void;
  onManageDevices?: () => void;
  className?: string;
}

const getStatusColor = (status: string): string => {
  switch (status?.toLowerCase()) {
    case "online":
      return "#4EDEA3";
    case "standby":
      return "#F59E0B";
    default:
      return "#6B7280";
  }
};

export const DeviceSelector: React.FC<DeviceSelectorProps> = ({
  onNavigateToDevices,
  onManageDevices,
}) => {
  const handleNavigate = onNavigateToDevices || onManageDevices;
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

  return (
    <div ref={dropdownRef} style={{ position: "relative", display: "inline-block" }}>
      {/* ── Trigger tugmasi ── */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        title="Faol kompyuterni tanlash"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "7px",
          padding: "5px 11px",
          borderRadius: "9999px",
          background: isOpen ? "rgba(147, 3, 197, 0.14)" : "rgba(255, 255, 255, 0.035)",
          border: isOpen
            ? "1px solid rgba(192, 76, 253, 0.35)"
            : "1px solid rgba(255, 255, 255, 0.08)",
          color: "var(--text-secondary)",
          fontSize: "12px",
          fontWeight: 500,
          cursor: loading ? "wait" : "pointer",
          transition: "all 0.2s ease",
          backdropFilter: "blur(12px)",
          opacity: loading ? 0.6 : 1,
        }}
        onMouseEnter={(e) => {
          if (!isOpen) {
            e.currentTarget.style.background = "rgba(147, 3, 197, 0.14)";
            e.currentTarget.style.borderColor = "rgba(192, 76, 253, 0.35)";
            e.currentTarget.style.color = "#FFFFFF";
          }
        }}
        onMouseLeave={(e) => {
          if (!isOpen) {
            e.currentTarget.style.background = "rgba(255, 255, 255, 0.035)";
            e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
            e.currentTarget.style.color = "var(--text-secondary)";
          }
        }}
      >
        <LaptopIcon size={13} color="#4EDEA3" />
        <span
          style={{
            maxWidth: "110px",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            fontWeight: 500,
          }}
        >
          {selectedDevice ? selectedDevice.name : "Kompyuter"}
        </span>
        {selectedDevice && (
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: getStatusColor(selectedDevice.status),
              boxShadow: `0 0 6px ${getStatusColor(selectedDevice.status)}80`,
              flexShrink: 0,
            }}
          />
        )}
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          style={{
            transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease",
            opacity: 0.6,
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* ── Dropdown menu ── */}
      {isOpen && (
        <div
          className="misa-ultra-glass"
          style={{
            position: "absolute",
            top: "calc(100% + 10px)",
            right: 0,
            width: "260px",
            borderRadius: "18px",
            background: "rgba(15, 11, 26, 0.94)",
            backdropFilter: "blur(28px)",
            WebkitBackdropFilter: "blur(28px)",
            border: "1px solid rgba(232, 179, 255, 0.18)",
            boxShadow:
              "0 24px 60px rgba(2, 6, 14, 0.92), 0 0 30px rgba(147, 3, 197, 0.15)",
            zIndex: 300,
            animation: "misa-fade-in 0.16s ease-out",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "8px 12px 6px",
              borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
              background: "rgba(2, 6, 14, 0.4)",
            }}
          >
            <span
              style={{
                fontSize: "10px",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "var(--text-muted)",
              }}
            >
              Ulangan Kompyuterlar
            </span>
          </div>

          {/* Device list */}
          <div
            style={{
              maxHeight: "220px",
              overflowY: "auto",
              padding: "4px",
            }}
          >
            {devices.length === 0 ? (
              <div
                style={{
                  padding: "16px 12px",
                  textAlign: "center",
                  fontSize: "12px",
                  color: "var(--text-muted)",
                }}
              >
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
                    style={{
                      width: "100%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 10px",
                      borderRadius: "12px",
                      textAlign: "left",
                      fontSize: "12px",
                      background: isSelected ? "rgba(78, 222, 163, 0.1)" : "transparent",
                      border: isSelected
                        ? "1px solid rgba(78, 222, 163, 0.25)"
                        : "1px solid transparent",
                      color: isSelected ? "#4EDEA3" : "var(--text-primary)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = "transparent";
                      }
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "9px",
                        minWidth: 0,
                        flex: 1,
                      }}
                    >
                      <span
                        style={{
                          width: "7px",
                          height: "7px",
                          borderRadius: "50%",
                          backgroundColor: getStatusColor(dev.status),
                          boxShadow: `0 0 5px ${getStatusColor(dev.status)}60`,
                          flexShrink: 0,
                        }}
                      />
                      <div style={{ minWidth: 0, flex: 1 }}>
                        <div
                          style={{
                            fontSize: "12.5px",
                            fontWeight: 600,
                            color: isSelected ? "#FFFFFF" : "var(--text-primary)",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {dev.name}
                        </div>
                        <div
                          style={{
                            fontSize: "10px",
                            fontFamily: "var(--font-mono)",
                            color: "var(--text-muted)",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {dev.device_id}
                        </div>
                      </div>
                    </div>

                    {isSelected && (
                      <CheckIcon size={14} color="#4EDEA3" />
                    )}
                  </button>
                );
              })
            )}
          </div>

          {/* Footer — Boshqarish havolasi */}
          {handleNavigate && (
            <div
              style={{
                padding: "4px",
                borderTop: "1px solid rgba(255, 255, 255, 0.06)",
                background: "rgba(2, 6, 14, 0.4)",
              }}
            >
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  handleNavigate();
                }}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px",
                  padding: "7px 10px",
                  borderRadius: "10px",
                  fontSize: "11.5px",
                  fontWeight: 600,
                  color: "#4EDEA3",
                  background: "transparent",
                  border: "1px solid transparent",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(78, 222, 163, 0.08)";
                  e.currentTarget.style.borderColor = "rgba(78, 222, 163, 0.2)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.borderColor = "transparent";
                }}
              >
                <span>Barcha qurilmalarni boshqarish</span>
                <ExternalLinkIcon size={11} color="currentColor" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
