import { useState, useEffect, lazy, Suspense } from "react";
import { AppShell } from "./layout/AppShell";
import { CommandPalette } from "./components/CommandPalette";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { backendService, MikasaAuthUser } from "./services/backendService";
import { AuthPage } from "./pages/AuthPage";

const LandingPage = lazy(() => import("./pages/LandingPage").then(m => ({ default: m.LandingPage })));
const ChatPage = lazy(() => import("./pages/ChatPage").then(m => ({ default: m.ChatPage })));
const VoicePage = lazy(() => import("./pages/VoicePage").then(m => ({ default: m.VoicePage })));
const CommandsPage = lazy(() => import("./pages/CommandsPage").then(m => ({ default: m.CommandsPage })));
const MemoryPage = lazy(() => import("./pages/MemoryPage").then(m => ({ default: m.MemoryPage })));
const SchedulerPage = lazy(() => import("./pages/SchedulerPage").then(m => ({ default: m.SchedulerPage })));
const PluginsPage = lazy(() => import("./pages/PluginsPage").then(m => ({ default: m.PluginsPage })));
const RemoteControlPage = lazy(() => import("./pages/RemoteControlPage").then(m => ({ default: m.RemoteControlPage })));
const TelegramIntegrationPage = lazy(() => import("./pages/TelegramIntegrationPage").then(m => ({ default: m.TelegramIntegrationPage })));
const DevicesPage = lazy(() => import("./pages/DevicesPage").then(m => ({ default: m.DevicesPage })));
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
  const [authChecking, setAuthChecking] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<MikasaAuthUser | null>(null);
  const [userName, setUserName] = useState<string>(() => {
    return localStorage.getItem("mikasa_user_name") || "Ustoz";
  });
  const [userAvatar, setUserAvatar] = useState<string>(() => {
    return localStorage.getItem("mikasa_user_avatar") || "emerald";
  });

  // Verify auth session on startup
  useEffect(() => {
    let mounted = true;
    const verifyAuth = async () => {
      try {
        const res = await backendService.getMe();
        if (mounted) {
          if (res.ok && res.authenticated && res.user) {
            setIsAuthenticated(true);
            setCurrentUser(res.user);
            setUserName(res.user.username);
            try {
              localStorage.setItem("mikasa_user_name", res.user.username);
            } catch {}
            backendService.updateAccount({ name: res.user.username }).catch(() => {});
          } else {
            setIsAuthenticated(false);
            setCurrentUser(null);
          }
        }
      } catch {
        if (mounted) {
          setIsAuthenticated(false);
          setCurrentUser(null);
        }
      } finally {
        if (mounted) {
          setAuthChecking(false);
        }
      }
    };

    verifyAuth();

    const unsubAuth = backendService.onAuthChange((user) => {
      if (user) {
        setIsAuthenticated(true);
        setCurrentUser(user);
        setUserName(user.username);
        try {
          localStorage.setItem("mikasa_user_name", user.username);
        } catch {}
        backendService.updateAccount({ name: user.username }).catch(() => {});
      } else {
        setIsAuthenticated(false);
        setCurrentUser(null);
      }
    });

    return () => {
      mounted = false;
      unsubAuth();
    };
  }, []);

  // Listen to status updates to keep username synchronized
  useEffect(() => {
    const unsub = backendService.onStatusChange((status) => {
      if (status.user && status.user.trim()) {
        const freshUser = status.user.trim();
        // Never let test users or placeholder e2e name overwrite the user
        if (freshUser.toLowerCase().includes("sinov") || freshUser.toLowerCase().includes("test")) {
          return;
        }
        // If current user is authenticated, keep authenticated name
        if (currentUser && currentUser.username) {
          return;
        }
        setUserName((prev) => (prev !== freshUser ? freshUser : prev));
        try {
          localStorage.setItem("mikasa_user_name", freshUser);
        } catch {}
      }
    });
    return () => unsub();
  }, [currentUser]);

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
      case "/remote":
        return <RemoteControlPage onNavigateHome={() => handleNavigate("/")} />;
      case "/telegram":
        return <TelegramIntegrationPage onNavigateHome={() => handleNavigate("/")} />;
      case "/devices":
        return <DevicesPage onNavigateHome={() => handleNavigate("/")} />;
      case "/account":
        return (
          <AccountPage
            onNavigateHome={() => handleNavigate("/")}
            onNavigateToDevices={() => handleNavigate("/devices")}
            onNavigateToTelegram={() => handleNavigate("/telegram")}
            onUserUpdated={handleUserUpdated}
            currentUser={currentUser}
            onLogout={handleLogout}
          />
        );
      default:
        return <LandingPage userName={userName} onNavigate={handleNavigate} />;
    }
  };

  const handleLogout = async () => {
    await backendService.logout();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setCurrentPath("/");
  };

  if (authChecking) {
    return <PageLoadingFallback />;
  }

  if (!isAuthenticated) {
    return (
      <AuthPage
        onAuthSuccess={(user) => {
          setIsAuthenticated(true);
          setCurrentUser(user);
          setUserName(user.username);
          try {
            localStorage.setItem("mikasa_user_name", user.username);
          } catch {}
        }}
      />
    );
  }

  return (
    <>
      <AppShell
        currentPath={currentPath}
        userName={userName}
        userAvatar={userAvatar}
        userAvatarUrl={currentUser?.avatar_url}
        onNavigate={handleNavigate}
        onOpenCommandPalette={() => setIsPaletteOpen(true)}
      >
        <ErrorBoundary fallbackNavigate={() => handleNavigate("/")}>
          <Suspense fallback={<PageLoadingFallback />}>
            {renderContent()}
          </Suspense>
        </ErrorBoundary>
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

