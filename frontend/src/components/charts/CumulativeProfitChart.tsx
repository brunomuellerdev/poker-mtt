import type { EChartsOption } from "echarts";
import { useMemo } from "react";
import { Chart } from "@/components/Chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCumulative } from "@/hooks/useAnalytics";
import { axisCommon, chartTheme } from "@/lib/chartTheme";
import { useFilterStore } from "@/stores/filterStore";

export function CumulativeProfitChart() {
  const filters = useFilterStore((s) => s.filters);
  const { data, isLoading } = useCumulative(filters);

  const option = useMemo<EChartsOption>(() => {
    const points = data ?? [];
    const last = points.length ? Number(points[points.length - 1].cumulative_base) : 0;
    const color = last >= 0 ? chartTheme.profit : chartTheme.loss;
    return {
      grid: { left: 56, right: 16, top: 16, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: chartTheme.tooltipBg,
        borderColor: chartTheme.tooltipBorder,
        textStyle: { color: chartTheme.text },
      },
      xAxis: {
        type: "category",
        data: points.map((p, i) => p.date ?? String(i)),
        ...axisCommon,
        axisLabel: { color: chartTheme.muted, hideOverlap: true },
      },
      yAxis: { type: "value", ...axisCommon },
      series: [
        {
          type: "line",
          smooth: true,
          showSymbol: false,
          data: points.map((p) => Number(p.cumulative_base)),
          lineStyle: { color, width: 2 },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: `${color}55` },
                { offset: 1, color: `${color}00` },
              ],
            },
          },
        },
      ],
    };
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cumulative Profit</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (data?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">No data yet.</p>
        ) : (
          <Chart option={option} height={300} />
        )}
      </CardContent>
    </Card>
  );
}
