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
    const raw = points.map((p, i) => ({
      x: i,
      y: Number(p.cumulative_base),
      date: p.date ?? String(i),
    }));

    // Augment with a synthetic point exactly at each zero-crossing so the
    // colour switches precisely at y = 0 (not at the next data vertex).
    const aug: { x: number; y: number; date: string | null }[] = [];
    for (let i = 0; i < raw.length; i++) {
      if (i > 0) {
        const a = raw[i - 1];
        const b = raw[i];
        if ((a.y < 0 && b.y > 0) || (a.y > 0 && b.y < 0)) {
          const t = a.y / (a.y - b.y);
          aug.push({ x: a.x + t * (b.x - a.x), y: 0, date: null });
        }
      }
      aug.push({ x: raw[i].x, y: raw[i].y, date: raw[i].date });
    }

    // Two overlaid series (no visualMap — it crashes line charts in echarts 6):
    // green carries the >= 0 portion, red the <= 0 portion. Both include the
    // zero-crossing points so the segments meet exactly at the axis.
    const green = aug.map((p) => [p.x, p.y >= 0 ? p.y : null]);
    const red = aug.map((p) => [p.x, p.y <= 0 ? p.y : null]);

    const labelByX = new Map<number, string>();
    for (const p of raw) labelByX.set(p.x, p.date);
    const maxX = Math.max(raw.length ? raw[raw.length - 1].x : 0, 1);

    return {
      grid: { left: 56, right: 16, top: 16, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: chartTheme.tooltipBg,
        borderColor: chartTheme.tooltipBorder,
        textStyle: { color: chartTheme.text },
        formatter: (params: unknown) => {
          const arr = params as Array<{ value: [number, number | null] }>;
          const real = arr.find((a) => a.value && a.value[1] !== null);
          if (!real) return "";
          const [x, y] = real.value;
          const label = labelByX.get(Math.round(x)) ?? "";
          const val = (y ?? 0).toLocaleString("en-US", {
            style: "currency",
            currency: "USD",
          });
          return `${label}<br/><b>${val}</b>`;
        },
      },
      xAxis: {
        type: "value",
        min: 0,
        max: maxX,
        ...axisCommon,
        axisLabel: {
          color: chartTheme.muted,
          hideOverlap: true,
          formatter: (val: number) =>
            Number.isInteger(val) ? (labelByX.get(val) ?? "") : "",
        },
      },
      yAxis: { type: "value", ...axisCommon },
      series: [
        {
          type: "line",
          name: "green",
          smooth: false,
          showSymbol: false,
          data: green,
          connectNulls: false,
          lineStyle: { color: chartTheme.profit, width: 2 },
          areaStyle: { color: chartTheme.profit, opacity: 0.18 },
        },
        {
          type: "line",
          name: "red",
          smooth: false,
          showSymbol: false,
          data: red,
          connectNulls: false,
          lineStyle: { color: chartTheme.loss, width: 2 },
          areaStyle: { color: chartTheme.loss, opacity: 0.18 },
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
