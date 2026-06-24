// App — the shell. Three surfaces inside the shared AppShell chrome.
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppShell } from "@/components/AppShell";
import { useRoute } from "@/lib/router";
import { QnaPortal } from "@/pages/QnaPortal";
import { Observability } from "@/pages/Observability";
import { KnowledgeBase } from "@/pages/KnowledgeBase";

export default function App() {
  const route = useRoute();
  return (
    <TooltipProvider delayDuration={300}>
      <AppShell>
        {route === "/observability" ? (
          <Observability />
        ) : route === "/knowledge-base" ? (
          <KnowledgeBase />
        ) : (
          <QnaPortal />
        )}
      </AppShell>
    </TooltipProvider>
  );
}
