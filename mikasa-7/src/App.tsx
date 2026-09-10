import { useState, useEffect } from "react";
import { AppShell } from "./layout/AppShell";
import { LandingPage } from "./pages/LandingPage";
import { ChatPage } from "./pages/ChatPage";
import { VoicePage } from "./pages/VoicePage";
import { RoutePlaceholder } from "./pages/RoutePlaceholder";
import {
  CommandsIcon,
  MemoryIcon,
  SchedulerIcon,
  PluginsIcon,
  UserIcon,
} from "./components/icons/Icons";

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
        return (
          <RoutePlaceholder
            title="Buyruqlar"
            subtitle="Tizim amallari va avtomatlashtirish buyruqlari keyingi bosqichda ulanadi."
            icon={<CommandsIcon size={26} color="var(--secondary)" />}
            onNavigateHome={() => handleNavigate("/")}
          />
        );
      case "/memory":
        return (
          <RoutePlaceholder
            title="Xotira"
            subtitle="Agent konteksti va uzoq muddatli xotira boshqaruvi keyingi bosqichda ulanadi."
            icon={<MemoryIcon size={26} color="var(--accent)" />}
            onNavigateHome={() => handleNavigate("/")}
          />
        );
      case "/scheduler":
        return (
          <RoutePlaceholder
            title="Rejalashtiruvchi"
            subtitle="Vaqtli topshiriqlar va avtomatik rejalashtiruvchi keyingi bosqichda ulanadi."
            icon={<SchedulerIcon size={26} color="var(--text-secondary)" />}
            onNavigateHome={() => handleNavigate("/")}
          />
        );
      case "/plugins":
        return (
          <RoutePlaceholder
            title="Plaginlar"
            subtitle="Kengaytmalar va tashqi vositalar integratsiyasi keyingi bosqichda ulanadi."
            icon={<PluginsIcon size={26} color="var(--text-secondary)" />}
            onNavigateHome={() => handleNavigate("/")}
          />
        );
      case "/account":
        return (
          <RoutePlaceholder
            title="Foydalanuvchi Hisobi va Sozlamalar"
            subtitle="Shaxsiy profil va ilova sozlamalari yagona hisob markazida joylashadi."
            icon={<UserIcon size={26} color="var(--primary-glow)" />}
            onNavigateHome={() => handleNavigate("/")}
          />
        );
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
