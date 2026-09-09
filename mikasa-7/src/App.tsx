import { useState } from "react";
import { AppShell } from "./layout/AppShell";
import { LandingPlaceholder } from "./pages/LandingPlaceholder";
import { RoutePlaceholder } from "./pages/RoutePlaceholder";
import {
  MicIcon,
  ChatIcon,
  CommandsIcon,
  MemoryIcon,
  SchedulerIcon,
  PluginsIcon,
  UserIcon,
} from "./components/icons/Icons";

export function App() {
  const [currentPath, setCurrentPath] = useState<string>("/");

  const renderContent = () => {
    switch (currentPath) {
      case "/":
        return <LandingPlaceholder onNavigate={setCurrentPath} />;
      case "/voice":
        return (
          <RoutePlaceholder
            title="Ovozli muloqot"
            subtitle="Mikasa bilan tabiiy ovozli dialog interfeysi keyingi bosqichda ulanadi."
            icon={<MicIcon size={24} color="var(--primary-glow)" />}
            onNavigateHome={() => setCurrentPath("/")}
          />
        );
      case "/chat":
        return (
          <RoutePlaceholder
            title="AI Suhbat"
            subtitle="Kuchli matnli muloqot, agent reasoning va asboblar oqimi keyingi bosqichda ulanadi."
            icon={<ChatIcon size={24} color="var(--primary-glow)" />}
            onNavigateHome={() => setCurrentPath("/")}
          />
        );
      case "/commands":
        return (
          <RoutePlaceholder
            title="Buyruqlar"
            subtitle="Tizim boshqaruvi va avtomatlashtirish buyruqlari keyingi bosqichda ulanadi."
            icon={<CommandsIcon size={24} color="var(--secondary)" />}
            onNavigateHome={() => setCurrentPath("/")}
          />
        );
      case "/memory":
        return (
          <RoutePlaceholder
            title="Xotira"
            subtitle="Agent konteksti va uzoq muddatli xotira boshqaruvi keyingi bosqichda ulanadi."
            icon={<MemoryIcon size={24} color="var(--accent)" />}
            onNavigateHome={() => setCurrentPath("/")}
          />
        );
      case "/scheduler":
        return (
          <RoutePlaceholder
            title="Rejalashtiruvchi"
            subtitle="Vaqtli topshiriqlar va avtomatik rejalashtiruvchi keyingi bosqichda ulanadi."
            icon={<SchedulerIcon size={24} color="var(--text-secondary)" />}
            onNavigateHome={() => setCurrentPath("/")}
          />
        );
      case "/plugins":
        return (
          <RoutePlaceholder
            title="Plaginlar"
            subtitle="Kengaytmalar va tashqi integratsiyalar keyingi bosqichda ulanadi."
            icon={<PluginsIcon size={24} color="var(--text-secondary)" />}
            onNavigateHome={() => setCurrentPath("/")}
          />
        );
      case "/account":
        return (
          <RoutePlaceholder
            title="Foydalanuvchi Hisobi va Sozlamalar"
            subtitle="Shaxsiy profil va ilova sozlamalari yagona hisob markazida joylashadi."
            icon={<UserIcon size={24} color="var(--primary-glow)" />}
            onNavigateHome={() => setCurrentPath("/")}
          />
        );
      default:
        return <LandingPlaceholder onNavigate={setCurrentPath} />;
    }
  };

  return (
    <AppShell currentPath={currentPath} onNavigate={setCurrentPath}>
      {renderContent()}
    </AppShell>
  );
}

export default App;
