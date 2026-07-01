import type { EChartsOption } from "echarts";
import { useMemo, useState } from "react";
import { Chart } from "@/components/Chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { useBreakdown } from "@/hooks/useAnalytics";
import { axisCommon, chartTheme } from "@/lib/chartTheme";
import { useFilterStore } from "@/stores/filterStore";

const DIMENSIONS = [
  { value: "buy_in", label: "Buy-in" },
  { value: "room", label: "Poker room" },
  { value: "speed", label: "Speed" },
  { value: "tournament_type", label: "Tournament type" },
  { value: "bounty_type", label: "Bounty type" },
];

export function RoiByCategoryChart() {
  const filters = useFilterStore((s) => s.filters);
  const [dimension, setDimension] = useState("buy_in");
  const { data, isLoading } = useBreakdown(dimension, filters);

  const option = useMemo<EChartsOption>(() => {
    const rows = data ?? [];
    return {
      grid: { left: 56, right: 16, top: 16, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: chartTheme.tooltipBg,
        borderColor: chartTheme.tooltipBorder,
        textStyle: { color: chartTheme.text },
        valueFormatter: (v) => `${Number(v).toFixed(2)}%`,
      },
      xAxis: { type: "category", data: rows.map((r) => r.key), ...axisCommon },
      yAxis: {
        type: "value",
        ...axisCommon,
        axisLabel: { formatter: "{value}%", color: chartTheme.muted },
      },
      series: [
        {
          type: "bar",
          name: "ROI",
          data: rows.map((r) => {
            const v = Number(r.roi_pct ?? 0);
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
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>ROI by Category</CardTitle>
        <Select
          className="h-8 w-40 text-xs"
          value={dimension}
          onChange={(e) => setDimension(e.target.value)}
        >
          {DIMENSIONS.map((d) => (
            <option key={d.value} value={d.value}>
              {d.label}
            </option>
          ))}
        </Select>
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
