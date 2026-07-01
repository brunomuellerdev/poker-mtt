// Hex approximations of the dark-theme HSL tokens in index.css.
// ECharts renders to canvas and can't read CSS variables directly, so the
// palette is mirrored here. Keep in sync with index.css if tokens change.
export const chartTheme = {
  text: "#e7edf5",
  muted: "#8b98ad",
  grid: "#232b3a",
  axis: "#2c3547",
  profit: "#2eb872", // success / positive
  loss: "#d13a3a", // destructive / negative
  primary: "#2eb872",
  accent: "#3b82f6",
  tooltipBg: "#0f1623",
  tooltipBorder: "#232b3a",
};

export const WEEKDAY_LABELS = [
  "Mon",
  "Tue",
  "Wed",
  "Thu",
  "Fri",
  "Sat",
  "Sun",
];

export const axisCommon = {
  axisLine: { lineStyle: { color: chartTheme.axis } },
  axisLabel: { color: chartTheme.muted },
  splitLine: { lineStyle: { color: chartTheme.grid } },
};
