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

export function App() {
  const [currentPath, setCurrentPath] = useState<string>("/");
  const [chatInitialPrompt, setChatInitialPrompt] = useState<string>("");

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
        return <LandingPage onNavigate={handleNavigate} />;
      case "/voice":
        return (
          <VoicePage
            onNavigateHome={() => handleNavigate("/")}
            onNavigateChat={() => handleNavigate("/chat")}
          />
        );
      case "/chat":
        return (
          <ChatPage
            initialPrompt={chatInitialPrompt}
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
        return <AccountPage onNavigateHome={() => handleNavigate("/")} />;
      default:
        return <LandingPage onNavigate={handleNavigate} />;
    }
  };

  return (
    <AppShell currentPath={currentPath} onNavigate={handleNavigate}>
      {renderContent()}
    </AppShell>
  );
}

export default App;
