import { CumulativeProfitChart } from "@/components/charts/CumulativeProfitChart";
import { MonthlyProfitChart } from "@/components/charts/MonthlyProfitChart";
import { RoiByCategoryChart } from "@/components/charts/RoiByCategoryChart";
import { WeekdayHourHeatmap } from "@/components/charts/WeekdayHourHeatmap";

export function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Analytics</h1>
      <CumulativeProfitChart />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <MonthlyProfitChart />
        <RoiByCategoryChart />
      </div>
      <WeekdayHourHeatmap />
    </div>
  );
}
