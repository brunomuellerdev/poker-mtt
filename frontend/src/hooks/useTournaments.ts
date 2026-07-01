import {
  useInfiniteQuery,
  useMutation,
  useQuery,
} from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type {
  Page,
  Summary,
  Tournament,
  TournamentCreate,
  TournamentFilters,
} from "@/types/api";

function filtersToQuery(f: TournamentFilters): Record<string, string> {
  const q: Record<string, string> = {};
  for (const [k, v] of Object.entries(f)) {
    if (v !== undefined && v !== null && v !== "") q[k] = String(v);
  }
  return q;
}

export function useTournaments(filters: TournamentFilters, limit = 20) {
  return useInfiniteQuery({
    queryKey: ["tournaments", filters, limit],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api.get<Page<Tournament>>("/tournaments", {
        ...filtersToQuery(filters),
        limit,
        offset: pageParam,
      }),
    getNextPageParam: (last) => last.next_offset ?? undefined,
  });
}

export function useSummary(filters: TournamentFilters) {
  return useQuery({
    queryKey: ["summary", filters],
    queryFn: () =>
      api.get<Summary>("/tournaments/summary", filtersToQuery(filters)),
  });
}

export function useCreateTournament() {
  return useMutation({
    mutationFn: (data: TournamentCreate) =>
      api.post<Tournament>("/tournaments", data),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["tournaments"],
          refetchType: "all",
        }),
        queryClient.invalidateQueries({
          queryKey: ["summary"],
          refetchType: "all",
        }),
      ]);
    },
  });
}

export function useUpdateTournament() {
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<TournamentCreate> }) =>
      api.patch<Tournament>(`/tournaments/${id}`, data),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["tournaments"],
          refetchType: "all",
        }),
        queryClient.invalidateQueries({
          queryKey: ["summary"],
          refetchType: "all",
        }),
      ]);
    },
  });
}

export function useDeleteTournament() {
  return useMutation({
    mutationFn: (id: string) => api.delete<void>(`/tournaments/${id}`),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ["tournaments"],
          refetchType: "all",
        }),
        queryClient.invalidateQueries({
          queryKey: ["summary"],
          refetchType: "all",
        }),
      ]);
    },
  });
}
