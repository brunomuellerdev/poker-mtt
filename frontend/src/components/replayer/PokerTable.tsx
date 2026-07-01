import { Card } from "@/components/replayer/Card";
import { cn } from "@/lib/utils";
import type { HandFrame, ParsedHand } from "@/types/api";

function fmtValue(
  value: string,
  unit: "bb" | "abs",
  bb: number,
  isChips: boolean,
  currency: string,
): string {
  if (unit === "bb" && bb > 0) {
    return `${(Number(value) / bb).toFixed(1)} BB`;
  }
  const n = Number(value);
  if (isChips) return n.toLocaleString("en-US");
  return `${currency}${n.toFixed(2)}`;
}

// Seat positions around an oval, by index of the seated players (0..n-1).
function seatPos(index: number, count: number): { top: string; left: string } {
  // start at bottom-center (hero area) and go clockwise
  const angle = Math.PI / 2 + (index / count) * 2 * Math.PI;
  const top = 50 + 42 * Math.sin(angle);
  const left = 50 + 46 * Math.cos(angle);
  return { top: `${top}%`, left: `${left}%` };
}

export function PokerTable({
  hand,
  frame,
  unit = "bb",
}: {
  hand: ParsedHand;
  frame: HandFrame;
  unit?: "bb" | "abs";
}) {
  const isChips = hand.is_chips;
  const cur = hand.currency;
  const bb = Number(hand.big_blind);
  const money = (v: string) => fmtValue(v, unit, bb, isChips, cur);
  // order players so the hero sits at the bottom (index 0)
  const heroIdx = frame.players.findIndex((p) => p.is_hero);
  const ordered =
    heroIdx >= 0
      ? [...frame.players.slice(heroIdx), ...frame.players.slice(0, heroIdx)]
      : frame.players;

  return (
    <div className="relative mx-auto aspect-[16/10] w-full max-w-3xl">
      {/* felt */}
      <div className="absolute inset-[8%] rounded-[50%] border-4 border-[#0c2a1a] bg-[radial-gradient(ellipse_at_center,#15573a,#0e3a26)] shadow-inner" />

      {/* center: board + pot */}
      <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2">
        <div className="flex gap-1">
          {frame.board.length === 0 && (
            <span className="text-xs text-emerald-200/50">Preflop</span>
          )}
          {frame.board.map((c, i) => (
            <Card key={`${c}-${i}`} card={c} size="sm" />
          ))}
        </div>
        <div className="rounded-full bg-black/40 px-3 py-1 text-sm font-medium text-emerald-100">
          Pot {money(frame.pot)}
        </div>
      </div>

      {/* seats */}
      {ordered.map((p, i) => {
        const pos = seatPos(i, ordered.length);
        const bet = Number(p.street_bet);
        const isActor = frame.actor === p.name;
        // chip position: along the line from the seat toward the center
        const chipTop = 50 + (parseFloat(pos.top) - 50) * 0.62;
        const chipLeft = 50 + (parseFloat(pos.left) - 50) * 0.62;
        return (
          <div key={p.seat}>
            {bet > 0 && (
              <div
                className="absolute z-10 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
                style={{ top: `${chipTop}%`, left: `${chipLeft}%` }}
              >
                <div className="h-5 w-5 rounded-full border-2 border-amber-200/80 bg-gradient-to-b from-amber-400 to-amber-600 shadow" />
                <span className="mt-0.5 rounded bg-black/60 px-1 text-[10px] font-medium text-amber-100">
                  {money(p.street_bet)}
                </span>
              </div>
            )}
            <div
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{ top: pos.top, left: pos.left }}
            >
              <div
                className={cn(
                  "flex w-32 flex-col items-center gap-1 rounded-lg border bg-card/95 p-2 text-center transition-all",
                  p.folded ? "opacity-40" : "opacity-100",
                  Number(p.won) > 0 && "border-success ring-1 ring-success",
                  isActor
                    ? "border-primary shadow-[0_0_0_2px] shadow-primary ring-2 ring-primary"
                    : "border-border",
                )}
              >
                <div className="flex gap-0.5">
                  {p.cards.length > 0 ? (
                    p.cards.map((c, idx) => <Card key={idx} card={c} size="sm" />)
                  ) : (
                    <>
                      <Card faceDown size="sm" />
                      <Card faceDown size="sm" />
                    </>
                  )}
                </div>
                <div className="flex w-full items-center justify-center gap-1">
                  <span className="truncate text-xs font-medium">{p.name}</span>
                  {p.is_button && (
                    <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-white text-[9px] font-bold text-black">
                      D
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-muted-foreground">
                  {money(p.stack)}
                  {p.all_in && (
                    <span className="ml-1 font-semibold text-amber-400">
                      ALL-IN
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
