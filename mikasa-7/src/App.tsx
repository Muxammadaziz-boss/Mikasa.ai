import { useState, useEffect } from "react";
import { AppShell } from "./layout/AppShell";
import { LandingPage } from "./pages/LandingPage";
import { ChatPage } from "./pages/ChatPage";
import { VoicePage } from "./pages/VoicePage";
import { CommandsPage } from "./pages/CommandsPage";
import { MemoryPage } from "./pages/MemoryPage";
import { SchedulerPage } from "./pages/SchedulerPage";
import { PluginsPage } from "./pages/PluginsPage";
import { AccountPage } from "./pages/AccountPage";
import { backendService } from "./services/backendService";

export function App() {
  const [currentPath, setCurrentPath] = useState<string>("/");
  const [chatInitialPrompt, setChatInitialPrompt] = useState<string>("");
  const [userName, setUserName] = useState<string>(() => {
    return localStorage.getItem("mikasa_user_name") || "Ustoz";
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

  const handleUserUpdated = (newName: string) => {
    setUserName(newName);
    try {
      localStorage.setItem("mikasa_user_name", newName);
    } catch {}
  };

  const handleNavigate = (path: string, initialPrompt?: string) => {
    if (initialPrompt !== undefined) {
      setChatInitialPrompt(initialPrompt);
    }
    setCurrentPath(path);
  };

  // Keyboard navigation shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const input = document.querySelector<HTMLInputElement>(".landing-composer input");
        if (input) {
          input.focus();
        }
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
    <AppShell currentPath={currentPath} userName={userName} onNavigate={handleNavigate}>
      {renderContent()}
    </AppShell>
  );
}

export default App;
