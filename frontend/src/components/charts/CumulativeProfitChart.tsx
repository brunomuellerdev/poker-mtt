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

    // Build the series on a numeric x-axis, inserting a synthetic point at the
    // exact zero-crossing between two points of opposite sign, so the colour
    // switches precisely at y = 0 (not at the next data vertex).
    const series: [number, number][] = [];
    const labelByX = new Map<number, string>();
    for (let i = 0; i < raw.length; i++) {
      if (i > 0) {
        const a = raw[i - 1];
        const b = raw[i];
        if ((a.y < 0 && b.y > 0) || (a.y > 0 && b.y < 0)) {
          const t = a.y / (a.y - b.y); // fraction a→b where the line hits 0
          series.push([a.x + t * (b.x - a.x), 0]);
        }
      }
      series.push([raw[i].x, raw[i].y]);
      labelByX.set(raw[i].x, raw[i].date);
    }

    const lastX = raw.length ? raw[raw.length - 1].x : 0;
    const maxX = Math.max(lastX, 1);

    return {
      grid: { left: 56, right: 16, top: 16, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: chartTheme.tooltipBg,
        borderColor: chartTheme.tooltipBorder,
        textStyle: { color: chartTheme.text },
        formatter: (params: unknown) => {
          const arr = params as Array<{ value: [number, number] }>;
          if (!arr.length) return "";
          const [x, y] = arr[0].value;
          const label = labelByX.get(Math.round(x)) ?? "";
          const val = y.toLocaleString("en-US", {
            style: "currency",
            currency: "USD",
          });
          return `${label}<br/><b>${val}</b>`;
        },
      },
      // colour segments by the y value: green at/above zero, red below
      visualMap: {
        show: false,
        type: "piecewise",
        dimension: 1,
        seriesIndex: 0,
        pieces: [
          { gte: 0, color: chartTheme.profit },
          { lt: 0, color: chartTheme.loss },
        ],
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
          smooth: false,
          showSymbol: false,
          data: series,
          lineStyle: { width: 2 },
          areaStyle: { opacity: 0.18 },
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
