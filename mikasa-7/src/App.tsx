import { useState, useEffect, lazy, Suspense } from "react";
import { AppShell } from "./layout/AppShell";
import { CommandPalette } from "./components/CommandPalette";
import { backendService } from "./services/backendService";

const LandingPage = lazy(() => import("./pages/LandingPage").then(m => ({ default: m.LandingPage })));
const ChatPage = lazy(() => import("./pages/ChatPage").then(m => ({ default: m.ChatPage })));
const VoicePage = lazy(() => import("./pages/VoicePage").then(m => ({ default: m.VoicePage })));
const CommandsPage = lazy(() => import("./pages/CommandsPage").then(m => ({ default: m.CommandsPage })));
const MemoryPage = lazy(() => import("./pages/MemoryPage").then(m => ({ default: m.MemoryPage })));
const SchedulerPage = lazy(() => import("./pages/SchedulerPage").then(m => ({ default: m.SchedulerPage })));
const PluginsPage = lazy(() => import("./pages/PluginsPage").then(m => ({ default: m.PluginsPage })));
const AccountPage = lazy(() => import("./pages/AccountPage").then(m => ({ default: m.AccountPage })));

const PageLoadingFallback = () => (
  <div
    style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      height: "100%",
      minHeight: "400px",
      color: "var(--text-muted, #94A3B8)",
      fontSize: "14px",
      gap: "14px",
    }}
  >
    <div
      style={{
        width: "28px",
        height: "28px",
        border: "2px solid rgba(16, 185, 129, 0.2)",
        borderTopColor: "#10B981",
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
      }}
    />
    <span>Yuklanmoqda...</span>
  </div>
);

export function App() {
  const [currentPath, setCurrentPath] = useState<string>("/");
  const [chatInitialPrompt, setChatInitialPrompt] = useState<string>("");
  const [isPaletteOpen, setIsPaletteOpen] = useState<boolean>(false);
  const [userName, setUserName] = useState<string>(() => {
    return localStorage.getItem("mikasa_user_name") || "Ustoz";
  });
  const [userAvatar, setUserAvatar] = useState<string>(() => {
    return localStorage.getItem("mikasa_user_avatar") || "emerald";
  });

  // Listen to status updates to keep username synchronized
  useEffect(() => {
    const unsub = backendService.onStatusChange((status) => {
      if (status.user && status.user.trim()) {
        const freshUser = status.user.trim();
        setUserName((prev) => (prev !== freshUser ? freshUser : prev));
        try {
          localStorage.setItem("mikasa_user_name", freshUser);
        } catch {}
      }
    });
    return () => unsub();
  }, []);

  // Listen to account updates (avatar & name)
  useEffect(() => {
    const unsub = backendService.onAccountChange((data) => {
      if (data.name) setUserName(data.name);
      if (data.avatar) setUserAvatar(data.avatar);
    });
    return () => unsub();
  }, []);

  const handleUserUpdated = (newName: string, newAvatar?: string) => {
    setUserName(newName);
    try {
      localStorage.setItem("mikasa_user_name", newName);
    } catch {}
    if (newAvatar) {
      setUserAvatar(newAvatar);
      try {
        localStorage.setItem("mikasa_user_avatar", newAvatar);
      } catch {}
    }
  };

  const handleNavigate = (path: string, initialPrompt?: string) => {
    if (initialPrompt !== undefined) {
      setChatInitialPrompt(initialPrompt);
    }
    setCurrentPath(path);
  };

  // Global Ctrl+K Command Palette shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const renderContent = () => {
    switch (currentPath) {
      case "/":
        return <LandingPage userName={userName} onNavigate={handleNavigate} />;
      case "/voice":
        return (
          <VoicePage
            userName={userName}
            onNavigateHome={() => handleNavigate("/")}
            onNavigateChat={() => handleNavigate("/chat")}
          />
        );
      case "/chat":
        return (
          <ChatPage
            initialPrompt={chatInitialPrompt}
            userName={userName}
            onNavigateHome={() => handleNavigate("/")}
            onNavigateVoice={() => handleNavigate("/voice")}
          />
        );
      case "/commands":
        return <CommandsPage onNavigateHome={() => handleNavigate("/")} />;
      case "/memory":
        return <MemoryPage onNavigateHome={() => handleNavigate("/")} />;
      case "/scheduler":
        return <SchedulerPage onNavigateHome={() => handleNavigate("/")} />;
      case "/plugins":
        return <PluginsPage onNavigateHome={() => handleNavigate("/")} />;
      case "/account":
        return (
          <AccountPage
            onNavigateHome={() => handleNavigate("/")}
            onUserUpdated={handleUserUpdated}
          />
        );
      default:
        return <LandingPage userName={userName} onNavigate={handleNavigate} />;
    }
  };

  return (
    <>
      <AppShell
        currentPath={currentPath}
        userName={userName}
        userAvatar={userAvatar}
        onNavigate={handleNavigate}
        onOpenCommandPalette={() => setIsPaletteOpen(true)}
      >
        <Suspense fallback={<PageLoadingFallback />}>
          {renderContent()}
        </Suspense>
      </AppShell>
      <CommandPalette
        isOpen={isPaletteOpen}
        onClose={() => setIsPaletteOpen(false)}
        onNavigate={handleNavigate}
      />
    </>
  );
}

export default App;

