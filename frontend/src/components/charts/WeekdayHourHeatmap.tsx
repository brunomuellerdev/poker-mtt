import type { EChartsOption } from "echarts";
import { useMemo } from "react";
import { Chart } from "@/components/Chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useHeatmap } from "@/hooks/useAnalytics";
import { WEEKDAY_LABELS, chartTheme } from "@/lib/chartTheme";
import { useFilterStore } from "@/stores/filterStore";

const HOURS = Array.from({ length: 24 }, (_, h) => String(h));

export function WeekdayHourHeatmap() {
  const filters = useFilterStore((s) => s.filters);
  const { data, isLoading } = useHeatmap(filters);

  const option = useMemo<EChartsOption>(() => {
    const rows = data ?? [];
    // ECharts heatmap data: [hourIndex, weekdayIndex, value]
    const cells = rows.map((r) => [
      r.hour,
      r.weekday - 1, // 1..7 -> 0..6
      Number(r.profit_base ?? 0),
    ]);
    const values = cells.map((c) => c[2]);
    const absMax = Math.max(1, ...values.map((v) => Math.abs(v)));

    return {
      grid: { left: 44, right: 16, top: 10, bottom: 60 },
      tooltip: {
        position: "top",
        backgroundColor: chartTheme.tooltipBg,
        borderColor: chartTheme.tooltipBorder,
        textStyle: { color: chartTheme.text },
        formatter: (p: unknown) => {
          const d = (p as { data: number[] }).data;
          return `${WEEKDAY_LABELS[d[1]]} ${d[0]}:00<br/>Profit: ${d[2].toFixed(2)}`;
        },
      },
      xAxis: {
        type: "category",
        data: HOURS,
        splitArea: { show: true },
        axisLabel: { color: chartTheme.muted, interval: 1 },
      },
      yAxis: {
        type: "category",
        data: WEEKDAY_LABELS,
        splitArea: { show: true },
        axisLabel: { color: chartTheme.muted },
      },
      visualMap: {
        min: -absMax,
        max: absMax,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 6,
        inRange: { color: [chartTheme.loss, "#1b2433", chartTheme.profit] },
        textStyle: { color: chartTheme.muted },
      },
      series: [
        {
          type: "heatmap",
          data: cells,
          emphasis: { itemStyle: { borderColor: chartTheme.text, borderWidth: 1 } },
        },
      ],
    };
  }, [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profit by Weekday × Hour</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (data?.length ?? 0) === 0 ? (
          <p className="text-sm text-muted-foreground">
            No data with start times yet.
          </p>
        ) : (
          <Chart option={option} height={320} />
        )}
      </CardContent>
    </Card>
  );
}
