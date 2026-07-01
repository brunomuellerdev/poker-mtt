import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { useAuthStore } from "@/stores/authStore";
import type { AccessToken, User } from "@/types/api";

export function useCurrentUser() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/auth/me"),
    enabled: token !== null,
  });
}

export function useLogin() {
  const setAccessToken = useAuthStore((s) => s.setAccessToken);
  return useMutation({
    mutationFn: (vars: { email: string; password: string }) =>
      api.post<AccessToken>("/auth/login", vars),
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (vars: { name: string; email: string; password: string }) =>
      api.post<User>("/auth/register", vars),
  });
}

export function useLogout() {
  const clear = useAuthStore((s) => s.clear);
  return useMutation({
    mutationFn: () => api.post<void>("/auth/logout"),
    onSettled: () => {
      clear();
      queryClient.clear();
    },
  });
}
