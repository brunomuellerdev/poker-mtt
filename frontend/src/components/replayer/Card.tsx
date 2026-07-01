import { cn } from "@/lib/utils";

const RANK_MAP: Record<string, string> = { "10": "T" };

// card aspect ratio from the sprite art (~0.71 w/h)
const SIZES = { sm: "h-9", md: "h-12" };

export function Card({
  card,
  size = "md",
  faceDown = false,
}: {
  card?: string;
  size?: "sm" | "md";
  faceDown?: boolean;
}) {
  const h = SIZES[size];

  if (faceDown || !card) {
    return (
      <div
        className={cn(
          h,
          "aspect-[71/100] rounded border border-border/60",
          "bg-[repeating-linear-gradient(45deg,#1e3a5f,#1e3a5f_4px,#16263d_4px,#16263d_8px)]",
        )}
      />
    );
  }

  const rank = card.slice(0, -1);
  const suit = card.slice(-1).toLowerCase();
  const id = `card-${RANK_MAP[rank] ?? rank}${suit}`;

  return (
    <svg
      className={cn(h, "aspect-[71/100]")}
      viewBox="0 0 71 100"
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label={card}
    >
      <use href={`#${id}`} width="71" height="100" />
    </svg>
  );
}
