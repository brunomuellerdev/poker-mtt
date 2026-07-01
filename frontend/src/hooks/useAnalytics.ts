import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  BreakdownRow,
  CumulativePoint,
  HeatmapCell,
  IndicatorRow,
  SeriesPoint,
  TournamentFilters,
} from "@/types/api";

function toQuery(f: TournamentFilters): Record<string, string> {
  const q: Record<string, string> = {};
  for (const [k, v] of Object.entries(f)) {
    if (v !== undefined && v !== null && v !== "") q[k] = String(v);
  }
  return q;
}

export function useCumulative(filters: TournamentFilters) {
  return useQuery({
    queryKey: ["analytics", "cumulative", filters],
    queryFn: () =>
      api.get<CumulativePoint[]>("/analytics/timeseries/cumulative", toQuery(filters)),
  });
}

export function useMonthly(filters: TournamentFilters) {
  return useQuery({
    queryKey: ["analytics", "monthly", filters],
    queryFn: () =>
      api.get<SeriesPoint[]>("/analytics/timeseries/monthly", toQuery(filters)),
  });
}

export function useBreakdown(by: string, filters: TournamentFilters) {
  return useQuery({
    queryKey: ["analytics", "breakdown", by, filters],
    queryFn: () =>
      api.get<BreakdownRow[]>("/analytics/breakdown", { ...toQuery(filters), by }),
  });
}

export function useHeatmap(filters: TournamentFilters) {
  return useQuery({
    queryKey: ["analytics", "heatmap", filters],
    queryFn: () => api.get<HeatmapCell[]>("/analytics/heatmap", toQuery(filters)),
  });
}

export function useIndicators(filters: TournamentFilters) {
  return useQuery({
    queryKey: ["analytics", "indicators", filters],
    queryFn: () => api.get<IndicatorRow[]>("/analytics/indicators", toQuery(filters)),
  });
}

