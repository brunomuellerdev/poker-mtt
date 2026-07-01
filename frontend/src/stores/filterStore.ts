import { create } from "zustand";
import type { TournamentFilters } from "@/types/api";

interface FilterState {
  filters: TournamentFilters;
  setFilters: (patch: Partial<TournamentFilters>) => void;
  reset: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  filters: {},
  setFilters: (patch) =>
    set((state) => ({ filters: { ...state.filters, ...patch } })),
  reset: () => set({ filters: {} }),
}));
