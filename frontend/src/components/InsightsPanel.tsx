import {
  AlertTriangle,
  CheckCircle2,
  Info,
  TrendingDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useInsights } from "@/hooks/useAnalytics";
import { cn } from "@/lib/utils";
import { useFilterStore } from "@/stores/filterStore";
import type { InsightItem } from "@/types/api";

const STYLES: Record<
  InsightItem["severity"],
  { icon: typeof Info; ring: string; iconColor: string }
> = {
  positive: {
    icon: CheckCircle2,
    ring: "border-l-success",
    iconColor: "text-success",
  },
  negative: {
    icon: TrendingDown,
    ring: "border-l-destructive",
    iconColor: "text-destructive",
  },
  warning: {
    icon: AlertTriangle,
    ring: "border-l-warning",
    iconColor: "text-warning",
  },
  neutral: { icon: Info, ring: "border-l-border", iconColor: "text-muted-foreground" },
};

export function InsightsPanel() {
  const filters = useFilterStore((s) => s.filters);
  const { data, isLoading } = useInsights(filters);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Insights</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading && (
          <p className="text-sm text-muted-foreground">Analyzing…</p>
        )}
        {!isLoading && (data?.length ?? 0) === 0 && (
          <p className="text-sm text-muted-foreground">No insights yet.</p>
        )}
        {data?.map((i) => {
          const st = STYLES[i.severity];
          const Icon = st.icon;
          return (
            <div
              key={i.id}
              className={cn(
                "flex gap-3 rounded-md border border-border border-l-2 bg-card/50 p-3",
                st.ring,
              )}
            >
              <Icon className={cn("mt-0.5 h-4 w-4 shrink-0", st.iconColor)} />
              <div className="space-y-0.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium">{i.title}</span>
                  {i.reliability && (
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                      {i.reliability}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{i.detail}</p>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
