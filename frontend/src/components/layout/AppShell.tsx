import {
  BarChart3,
  Bookmark,
  LayoutDashboard,
  ListOrdered,
  LogOut,
  PlayCircle,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { CardSprite } from "@/components/replayer/CardSprite";
import { Button } from "@/components/ui/button";
import { useLogout } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";

const SECTIONS = [
  {
    label: "MTT",
    items: [
      { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
      { to: "/tournaments", label: "Tournaments", icon: ListOrdered, end: false },
      { to: "/analytics", label: "Analytics", icon: BarChart3, end: false },
    ],
  },
  {
    label: "Poker Hands",
    items: [
      { to: "/hands/marked", label: "Marked Hands", icon: Bookmark, end: false },
      { to: "/hands/replayer", label: "Hand Replayer", icon: PlayCircle, end: false },
    ],
  },
];

export function AppShell() {
  const logout = useLogout();
  const user = useAuthStore((s) => s.user);

  return (
    <div className="flex min-h-screen">
      <CardSprite />
      <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card md:flex">
        <div className="flex h-14 items-center gap-2 border-b border-border px-5">
          <div className="h-6 w-6 rounded bg-primary" />
          <span className="font-semibold tracking-tight">Poker Tracker</span>
        </div>
        <nav className="flex-1 space-y-5 p-3">
          {SECTIONS.map((section) => (
            <div key={section.label} className="space-y-1">
              <p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                {section.label}
              </p>
              {section.items.map(({ to, label, icon: Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                      isActive
                        ? "bg-secondary text-foreground"
                        : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-border px-5">
          <div className="text-sm text-muted-foreground">
            {user ? user.name : ""}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </header>
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
