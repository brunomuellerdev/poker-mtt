import { create } from "zustand";
import type { User } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  user: User | null;
  setAccessToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  clear: () => void;
}

// Access token is held in memory only (not localStorage) to limit XSS exposure.
// The refresh token lives in an httpOnly cookie set by the backend; on reload we
// silently call /auth/refresh to repopulate the access token.
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setAccessToken: (token) => set({ accessToken: token }),
  setUser: (user) => set({ user }),
  clear: () => set({ accessToken: null, user: null }),
}));
