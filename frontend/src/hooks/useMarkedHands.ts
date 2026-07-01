import { useMutation, useQuery } from "@tanstack/react-query";
import { queryClient } from "@/lib/queryClient";
import { api } from "@/lib/api";
import type { MarkedHand, MarkedHandCreate, ParsedHand } from "@/types/api";

const KEY = ["marked-hands"];

export function useMarkedHands() {
  return useQuery({
    queryKey: KEY,
    queryFn: () => api.get<MarkedHand[]>("/marked-hands"),
  });
}

export function useCreateMarkedHand() {
  return useMutation({
    mutationFn: (data: MarkedHandCreate) =>
      api.post<MarkedHand>("/marked-hands", data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateMarkedHand() {
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MarkedHandCreate> }) =>
      api.patch<MarkedHand>(`/marked-hands/${id}`, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteMarkedHand() {
  return useMutation({
    mutationFn: (id: string) => api.delete<void>(`/marked-hands/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}

interface MarkedHandReplay {
  id: string;
  hand_code: string;
  replay: ParsedHand | null;
}

export async function fetchMarkedHandReplay(id: string): Promise<ParsedHand | null> {
  const r = await api.get<MarkedHandReplay>(`/marked-hands/${id}/replay`);
  return r.replay;
}
