import { useEffect, useState } from "react";
import {
  Navigate,
  Outlet,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { useCurrentUser } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { HandReplayerPage } from "@/pages/HandReplayerPage";
import { MarkedHandsPage } from "@/pages/MarkedHandsPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { TournamentsPage } from "@/pages/TournamentsPage";
import { useAuthStore } from "@/stores/authStore";

function ProtectedLayout() {
  const token = useAuthStore((s) => s.accessToken);
  const setUser = useAuthStore((s) => s.setUser);
  const { data: user, isLoading } = useCurrentUser();

  useEffect(() => {
    if (user) setUser(user);
  }, [user, setUser]);

  if (token === null) return <Navigate to="/login" replace />;
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }
  return <Outlet />;
}

export default function App() {
  // On first load, try to restore a session via the httpOnly refresh cookie.
  const [bootstrapped, setBootstrapped] = useState(false);
  useEffect(() => {
    api.refresh().finally(() => setBootstrapped(true));
  }, []);

  if (!bootstrapped) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedLayout />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/tournaments" element={<TournamentsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/hands/marked" element={<MarkedHandsPage />} />
            <Route path="/hands/replayer" element={<HandReplayerPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
