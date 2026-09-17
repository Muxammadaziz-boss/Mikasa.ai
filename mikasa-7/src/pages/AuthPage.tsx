// ========== AuthPage.tsx ==========
// Mikasa AI v8.0.0 — Phase 41: Account Registration & Authentication System
// Glassmorphic Auth Gate for Login, Registration, Password Reset and Email Verification

import React, { useState } from "react";
import {
  backendService,
  MikasaAuthUser,
} from "../services/backendService";
import {
  SparklesIcon,
  ShieldIcon,
  KeyIcon,
  UserIcon,
  CheckIcon,
  AlertTriangleIcon,
} from "../components/icons/Icons";

interface AuthPageProps {
  onAuthSuccess: (user: MikasaAuthUser) => void;
}

type AuthTab = "login" | "register" | "forgot" | "reset" | "verify";

export const AuthPage: React.FC<AuthPageProps> = ({ onAuthSuccess }) => {
  const [activeTab, setActiveTab] = useState<AuthTab>("login");

  // Form fields
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [token, setToken] = useState("");

  // Status & Feedback
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Clear messages on tab change
  const handleTabChange = (tab: AuthTab) => {
    setActiveTab(tab);
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  // Password validation helper
  const isPasswordStrong = (pwd: string) => {
    return pwd.length >= 8 && /[a-zA-Z]/.test(pwd) && /[0-9]/.test(pwd);
  };

  // 1. LOGIN HANDLER
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setErrorMsg("Foydalanuvchi nomi yoki email va parolni kiriting");
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await backendService.login({
        username_or_email: username.trim(),
        password,
      });

      if (res.ok && res.user) {
        setSuccessMsg("Muvaffaqiyatli tizimga kirildi!");
        setTimeout(() => {
          onAuthSuccess(res.user!);
        }, 400);
      } else {
        setErrorMsg(res.error || "Kirishda xatolik yuz berdi");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Server bilan bog'lanishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  // 2. REGISTER HANDLER
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setErrorMsg("Foydalanuvchi nomi va parolni kiriting");
      return;
    }
    if (!isPasswordStrong(password)) {
      setErrorMsg("Parol kamida 8 ta belgidan iborat bo'lib, harf va raqam qatnashishi shart");
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg("Parollar bir-biriga mos kelmadi");
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await backendService.register({
        username: username.trim(),
        email: email.trim() || undefined,
        password,
        confirm_password: confirmPassword,
      });

      if (res.ok && res.user) {
        setSuccessMsg("Hisob muvaffaqiyatli yaratildi!");
        setTimeout(() => {
          onAuthSuccess(res.user!);
        }, 500);
      } else {
        setErrorMsg(res.error || "Ro'yxatdan o'tishda xatolik");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Server bilan bog'lanishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  // 3. FORGOT PASSWORD HANDLER
  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    const target = email.trim() || username.trim();
    if (!target) {
      setErrorMsg("Email yoki foydalanuvchi nomingizni kiriting");
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await backendService.forgotPassword(target);
      if (res.ok) {
        if (res.token) {
          setToken(res.token);
          setSuccessMsg(`${res.message || "Tiklash kodi yaratildi."} Qayta tiklash formasiga o'ting.`);
          setTimeout(() => {
            setActiveTab("reset");
          }, 1200);
        } else {
          setSuccessMsg(res.message || "Agar hisob mavjud bo'lsa, tiklash xabari yuborildi.");
        }
      } else {
        setErrorMsg(res.error || "So'rov yuborishda xatolik");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Server bilan bog'lanishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  // 4. RESET PASSWORD HANDLER
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setErrorMsg("Tiklash tokenini kiriting");
      return;
    }
    if (!isPasswordStrong(password)) {
      setErrorMsg("Yangi parol kamida 8 ta belgidan iborat bo'lib, harf va raqam qatnashishi kerak");
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg("Yangi parollar mos kelmadi");
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await backendService.resetPassword({
        token: token.trim(),
        new_password: password,
        confirm_password: confirmPassword,
      });

      if (res.ok) {
        setSuccessMsg(res.message || "Parol muvaffaqiyatli yangilandi! Endi kirishingiz mumkin.");
        setPassword("");
        setConfirmPassword("");
        setTimeout(() => {
          setActiveTab("login");
        }, 1200);
      } else {
        setErrorMsg(res.error || "Parolni yangilashda xatolik");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Server bilan bog'lanishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  // 5. VERIFY EMAIL HANDLER
  const handleVerifyEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setErrorMsg("Tasdiqlash tokenini kiriting");
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await backendService.verifyEmail(token.trim());
      if (res.ok) {
        setSuccessMsg(res.message || "Email manzilingiz muvaffaqiyatli tasdiqlandi!");
        setTimeout(() => {
          setActiveTab("login");
        }, 1200);
      } else {
        setErrorMsg(res.error || "Emailni tasdiqlashda xatolik");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Server bilan bog'lanishda xatolik");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        width: "100%",
        background: "radial-gradient(ellipse at 50% 20%, rgba(16, 185, 129, 0.12) 0%, rgba(10, 15, 29, 0.98) 70%, #050811 100%)",
        color: "#F8FAFC",
        fontFamily: "inherit",
        position: "relative",
        overflow: "hidden",
        padding: "20px",
        boxSizing: "border-box",
      }}
    >
      {/* Ambient background blur elements */}
      <div
        style={{
          position: "absolute",
          top: "15%",
          left: "25%",
          width: "380px",
          height: "380px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 70%)",
          filter: "blur(60px)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "15%",
          right: "25%",
          width: "420px",
          height: "420px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(6, 182, 212, 0.07) 0%, transparent 70%)",
          filter: "blur(70px)",
          pointerEvents: "none",
        }}
      />

      {/* Main Glass Card */}
      <div
        style={{
          width: "100%",
          maxWidth: "460px",
          background: "rgba(15, 23, 42, 0.75)",
          backdropFilter: "blur(24px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: "20px",
          boxShadow: "0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(16, 185, 129, 0.06)",
          padding: "36px 32px",
          position: "relative",
          zIndex: 10,
        }}
      >
        {/* Header Branding */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: "56px",
              height: "56px",
              borderRadius: "16px",
              background: "linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(6, 182, 212, 0.15) 100%)",
              border: "1px solid rgba(16, 185, 129, 0.4)",
              boxShadow: "0 0 20px rgba(16, 185, 129, 0.25)",
              marginBottom: "14px",
            }}
          >
            <SparklesIcon size={26} color="#10B981" />
          </div>
          <h1
            style={{
              margin: "0 0 6px",
              fontSize: "22px",
              fontWeight: 700,
              letterSpacing: "-0.02em",
              background: "linear-gradient(135deg, #FFFFFF 30%, #A7F3D0 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Mikasa AI
          </h1>
          <p style={{ margin: 0, fontSize: "13px", color: "#94A3B8" }}>
            Avtonom AI Yordamchi & Masofaviy Boshqaruv
          </p>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: "flex",
            background: "rgba(0, 0, 0, 0.3)",
            borderRadius: "10px",
            padding: "4px",
            marginBottom: "24px",
            border: "1px solid rgba(255, 255, 255, 0.06)",
          }}
        >
          <button
            type="button"
            onClick={() => handleTabChange("login")}
            style={{
              flex: 1,
              padding: "9px 0",
              border: "none",
              borderRadius: "8px",
              background: activeTab === "login" ? "rgba(16, 185, 129, 0.22)" : "transparent",
              color: activeTab === "login" ? "#34D399" : "#94A3B8",
              fontSize: "13.5px",
              fontWeight: activeTab === "login" ? 600 : 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            Kirish
          </button>
          <button
            type="button"
            onClick={() => handleTabChange("register")}
            style={{
              flex: 1,
              padding: "9px 0",
              border: "none",
              borderRadius: "8px",
              background: activeTab === "register" ? "rgba(16, 185, 129, 0.22)" : "transparent",
              color: activeTab === "register" ? "#34D399" : "#94A3B8",
              fontSize: "13.5px",
              fontWeight: activeTab === "register" ? 600 : 500,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            Ro'yxatdan o'tish
          </button>
        </div>

        {/* Alerts / Feedback */}
        {errorMsg && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "10px",
              background: "rgba(239, 68, 68, 0.12)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#FCA5A5",
              fontSize: "13px",
              marginBottom: "18px",
              lineHeight: 1.4,
            }}
          >
            <AlertTriangleIcon size={18} color="#EF4444" />
            <span style={{ flex: 1 }}>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "12px 14px",
              borderRadius: "10px",
              background: "rgba(16, 185, 129, 0.12)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              color: "#6EE7B7",
              fontSize: "13px",
              marginBottom: "18px",
              lineHeight: 1.4,
            }}
          >
            <CheckIcon size={18} color="#10B981" />
            <span style={{ flex: 1 }}>{successMsg}</span>
          </div>
        )}

        {/* TAB 1: LOGIN FORM */}
        {activeTab === "login" && (
          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Foydalanuvchi nomi yoki Email
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin yoki user@example.com"
                  required
                  style={{
                    width: "100%",
                    padding: "11px 14px 11px 38px",
                    background: "rgba(0, 0, 0, 0.3)",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: "10px",
                    color: "#FFFFFF",
                    fontSize: "14px",
                    outline: "none",
                    boxSizing: "border-box",
                    transition: "border-color 0.15s ease",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#10B981")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.12)")}
                />
                <div style={{ position: "absolute", left: "12px", top: "12px", opacity: 0.5 }}>
                  <UserIcon size={16} />
                </div>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                  Parol
                </label>
                <button
                  type="button"
                  onClick={() => handleTabChange("forgot")}
                  style={{
                    background: "none",
                    border: "none",
                    padding: 0,
                    color: "#34D399",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  Parolni unutdingizmi?
                </button>
              </div>
              <div style={{ position: "relative" }}>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: "100%",
                    padding: "11px 14px 11px 38px",
                    background: "rgba(0, 0, 0, 0.3)",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: "10px",
                    color: "#FFFFFF",
                    fontSize: "14px",
                    outline: "none",
                    boxSizing: "border-box",
                    transition: "border-color 0.15s ease",
                  }}
                  onFocus={(e) => (e.target.style.borderColor = "#10B981")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.12)")}
                />
                <div style={{ position: "absolute", left: "12px", top: "12px", opacity: 0.5 }}>
                  <KeyIcon size={16} />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: "8px",
                padding: "12px 18px",
                background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                border: "none",
                borderRadius: "10px",
                color: "#052E16",
                fontSize: "14.5px",
                fontWeight: 600,
                cursor: loading ? "default" : "pointer",
                boxShadow: "0 4px 14px rgba(16, 185, 129, 0.35)",
                transition: "all 0.15s ease",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Kirilmoqda..." : "Tizimga kirish"}
            </button>
          </form>
        )}

        {/* TAB 2: REGISTER FORM */}
        {activeTab === "register" && (
          <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Foydalanuvchi nomi
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="masalan: sherzod_dev"
                  required
                  style={{
                    width: "100%",
                    padding: "10px 14px 10px 38px",
                    background: "rgba(0, 0, 0, 0.3)",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: "10px",
                    color: "#FFFFFF",
                    fontSize: "13.5px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
                <div style={{ position: "absolute", left: "12px", top: "11px", opacity: 0.5 }}>
                  <UserIcon size={16} />
                </div>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Email manzil (ixtiyoriy)
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  background: "rgba(0, 0, 0, 0.3)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: "10px",
                  color: "#FFFFFF",
                  fontSize: "13.5px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Parol (kamida 8 belgi, harf va raqam)
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: "100%",
                    padding: "10px 14px 10px 38px",
                    background: "rgba(0, 0, 0, 0.3)",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: "10px",
                    color: "#FFFFFF",
                    fontSize: "13.5px",
                    outline: "none",
                    boxSizing: "border-box",
                  }}
                />
                <div style={{ position: "absolute", left: "12px", top: "11px", opacity: 0.5 }}>
                  <KeyIcon size={16} />
                </div>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Parolni tasdiqlang
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  background: "rgba(0, 0, 0, 0.3)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: "10px",
                  color: "#FFFFFF",
                  fontSize: "13.5px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: "8px",
                padding: "12px 18px",
                background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                border: "none",
                borderRadius: "10px",
                color: "#052E16",
                fontSize: "14.5px",
                fontWeight: 600,
                cursor: loading ? "default" : "pointer",
                boxShadow: "0 4px 14px rgba(16, 185, 129, 0.35)",
                transition: "all 0.15s ease",
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Yaratilmoqda..." : "Hisob yaratish"}
            </button>
          </form>
        )}

        {/* TAB 3: FORGOT PASSWORD FORM */}
        {activeTab === "forgot" && (
          <form onSubmit={handleForgotPassword} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ fontSize: "13px", color: "#94A3B8", lineHeight: 1.5 }}>
              Hisobingizga tegishli email manzil yoki foydalanuvchi nomini kiriting. Biz parolni tiklash kodini jo'natamiz.
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Email yoki Foydalanuvchi nomi
              </label>
              <input
                type="text"
                value={email || username}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setUsername(e.target.value);
                }}
                placeholder="user@example.com"
                required
                style={{
                  width: "100%",
                  padding: "11px 14px",
                  background: "rgba(0, 0, 0, 0.3)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: "10px",
                  color: "#FFFFFF",
                  fontSize: "14px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: "4px",
                padding: "11px 18px",
                background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                border: "none",
                borderRadius: "10px",
                color: "#052E16",
                fontSize: "14px",
                fontWeight: 600,
                cursor: loading ? "default" : "pointer",
              }}
            >
              {loading ? "Yuborilmoqda..." : "Tiklash kodini yuborish"}
            </button>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "8px" }}>
              <button
                type="button"
                onClick={() => handleTabChange("login")}
                style={{
                  background: "none",
                  border: "none",
                  color: "#94A3B8",
                  fontSize: "12.5px",
                  cursor: "pointer",
                }}
              >
                ← Kirishga qaytish
              </button>
              <button
                type="button"
                onClick={() => handleTabChange("reset")}
                style={{
                  background: "none",
                  border: "none",
                  color: "#34D399",
                  fontSize: "12.5px",
                  cursor: "pointer",
                }}
              >
                Kodingiz bormi? Tiklash →
              </button>
            </div>
          </form>
        )}

        {/* TAB 4: RESET PASSWORD FORM */}
        {activeTab === "reset" && (
          <form onSubmit={handleResetPassword} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ fontSize: "13px", color: "#94A3B8", lineHeight: 1.5 }}>
              Yuborilgan bir martalik tiklash tokeni va yangi parolingizni kiriting.
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Tiklash tokeni
              </label>
              <input
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="masalan: 1a2b3c4d..."
                required
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  background: "rgba(0, 0, 0, 0.3)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: "10px",
                  color: "#FFFFFF",
                  fontSize: "13.5px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Yangi parol
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  background: "rgba(0, 0, 0, 0.3)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: "10px",
                  color: "#FFFFFF",
                  fontSize: "13.5px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Yangi parolni tasdiqlang
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  background: "rgba(0, 0, 0, 0.3)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: "10px",
                  color: "#FFFFFF",
                  fontSize: "13.5px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: "6px",
                padding: "11px 18px",
                background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                border: "none",
                borderRadius: "10px",
                color: "#052E16",
                fontSize: "14px",
                fontWeight: 600,
                cursor: loading ? "default" : "pointer",
              }}
            >
              {loading ? "Yangilanmoqda..." : "Parolni yangilash"}
            </button>

            <button
              type="button"
              onClick={() => handleTabChange("login")}
              style={{
                background: "none",
                border: "none",
                color: "#94A3B8",
                fontSize: "12.5px",
                cursor: "pointer",
                marginTop: "4px",
              }}
            >
              ← Kirishga qaytish
            </button>
          </form>
        )}

        {/* TAB 5: VERIFY EMAIL FORM */}
        {activeTab === "verify" && (
          <form onSubmit={handleVerifyEmail} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ fontSize: "13px", color: "#94A3B8", lineHeight: 1.5 }}>
              Email manzilingizga yuborilgan tasdiqlash tokenini kiriting.
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12.5px", color: "#94A3B8", fontWeight: 500 }}>
                Tasdiqlash tokeni
              </label>
              <input
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="masalan: 1a2b3c4d..."
                required
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  background: "rgba(0, 0, 0, 0.3)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  borderRadius: "10px",
                  color: "#FFFFFF",
                  fontSize: "13.5px",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: "4px",
                padding: "11px 18px",
                background: "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                border: "none",
                borderRadius: "10px",
                color: "#052E16",
                fontSize: "14px",
                fontWeight: 600,
                cursor: loading ? "default" : "pointer",
              }}
            >
              {loading ? "Tasdiqlanmoqda..." : "Emailni tasdiqlash"}
            </button>

            <button
              type="button"
              onClick={() => handleTabChange("login")}
              style={{
                background: "none",
                border: "none",
                color: "#94A3B8",
                fontSize: "12.5px",
                cursor: "pointer",
                marginTop: "4px",
              }}
            >
              ← Kirishga qaytish
            </button>
          </form>
        )}

        {/* Footer info */}
        <div
          style={{
            marginTop: "26px",
            paddingTop: "18px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "11.5px",
            color: "#64748B",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <ShieldIcon size={14} color="#10B981" />
            <span>PBKDF2 600k HMAC-SHA256</span>
          </div>
          <span>v8.0.0 Dev</span>
        </div>
      </div>
    </div>
  );
};
