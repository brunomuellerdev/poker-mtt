import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMoney(value: string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const n = Number(value);
  return n.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function formatPct(value: string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${Number(value).toFixed(2)}%`;
}

export function formatDate(iso: string): string {
  // iso is YYYY-MM-DD; render as dd/mm/yyyy without timezone shifts
  const [y, m, d] = iso.split("-");
  return d && m && y ? `${d}/${m}/${y}` : iso;
}

export function profitClass(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "text-muted-foreground";
  const n = Number(value);
  if (n > 0) return "text-success";
  if (n < 0) return "text-destructive";
  return "text-muted-foreground";
}
