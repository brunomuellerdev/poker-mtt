import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CumulativeProfitChart } from "@/components/charts/CumulativeProfitChart";
import { useSummary } from "@/hooks/useTournaments";
import { useFilterStore } from "@/stores/filterStore";
import { formatMoney, formatPct, profitClass } from "@/lib/utils";

function Stat({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-semibold ${valueClass ?? ""}`}>
          {value}
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const filters = useFilterStore((s) => s.filters);
  const { data, isLoading } = useSummary(filters);

  if (isLoading) {
    return <p className="text-muted-foreground">Loading…</p>;
  }
  if (!data) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Tournaments" value={String(data.tournaments)} />
        <Stat
          label="Total Profit"
          value={formatMoney(data.total_profit_base)}
          valueClass={profitClass(data.total_profit_base)}
        />
        <Stat label="ROI" value={formatPct(data.roi_pct)} valueClass={profitClass(data.roi_pct)} />
        <Stat label="ABI" value={formatMoney(data.abi_base)} />
        <Stat label="ITM" value={formatPct(data.itm_pct)} />
        <Stat label="Final Table" value={formatPct(data.final_table_pct)} />
        <Stat label="Win %" value={formatPct(data.win_pct)} />
        <Stat
          label="Max Drawdown"
          value={formatMoney(data.max_drawdown_base)}
          valueClass="text-destructive"
        />
      </div>
      <CumulativeProfitChart />
    </div>
  );
}
