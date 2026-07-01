import type { EChartsOption } from "echarts";
import { useMemo } from "react";
import { Chart } from "@/components/Chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMonthly } from "@/hooks/useAnalytics";
import { axisCommon, chartTheme } from "@/lib/chartTheme";
import { useFilterStore } from "@/stores/filterStore";

export function MonthlyProfitChart() {
  const filters = useFilterStore((s) => s.filters);
  const { data, isLoading } = useMonthly(filters);

  const option = useMemo<EChartsOption>(() => {
    const rows = data ?? [];
    return {
      grid: { left: 56, right: 16, top: 16, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: chartTheme.tooltipBg,
        borderColor: chartTheme.tooltipBorder,
        textStyle: { color: chartTheme.text },
      },
      xAxis: { type: "category", data: rows.map((r) => r.period), ...axisCommon },
      yAxis: { type: "value", ...axisCommon },
      series: [
        {
          type: "bar",
          data: rows.map((r) => {
            const v = Number(r.profit_base ?? 0);
            return {
              value: v,
              itemStyle: {
                color: v >= 0 ? chartTheme.profit : chartTheme.loss,
                borderRadius: [3, 3, 0, 0],
              },
            };
          }),
        },
      ],
    };
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly Profit</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (data?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">No data yet.</p>
        ) : (
          <Chart option={option} height={280} />
        )}
      </CardContent>
    </Card>
  );
}
