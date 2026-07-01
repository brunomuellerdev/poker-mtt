import {
  ChevronLeft,
  ChevronRight,
  Pause,
  Play,
  Star,
  Trash2,
  Upload,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Card as CardEl } from "@/components/replayer/Card";
import { PokerTable } from "@/components/replayer/PokerTable";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  fetchMarkedHandReplay,
  useCreateMarkedHand,
  useDeleteMarkedHand,
  useMarkedHands,
} from "@/hooks/useMarkedHands";
import { ApiError, api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { MarkedHand, ParsedHand, ParseHandsResponse } from "@/types/api";

const normalizeCode = (code: string) => code.replace(/^#/, "").trim();

interface Row {
  id: string;
  heroCards: string[];
  board: string[];
  parsed: ParsedHand | null; // in-memory frames (imported)
  marked: MarkedHand | null; // DB record if marked
}

export function HandReplayerPage() {
  const [imported, setImported] = useState<ParsedHand[]>([]);
  const [replayCache, setReplayCache] = useState<Record<string, ParsedHand>>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [unit, setUnit] = useState<"bb" | "abs">("bb");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: marked } = useMarkedHands();
  const createMark = useCreateMarkedHand();
  const deleteMark = useDeleteMarkedHand();

  // marked (with replay) keyed by normalized hand id
  const markedByCode = useMemo(() => {
    const m = new Map<string, MarkedHand>();
    for (const h of marked ?? []) {
      if (h.has_replay) m.set(normalizeCode(h.hand_code), h);
    }
    return m;
  }, [marked]);

  // merged display list: imported (memory) + persisted marked not imported
  const rows = useMemo<Row[]>(() => {
    const out: Row[] = [];
    const seen = new Set<string>();
    for (const h of imported) {
      out.push({
        id: h.hand_id,
        heroCards: h.hero_cards,
        board: h.board,
        parsed: h,
        marked: markedByCode.get(h.hand_id) ?? null,
      });
      seen.add(h.hand_id);
    }
    for (const m of markedByCode.values()) {
      const id = normalizeCode(m.hand_code);
      if (!seen.has(id)) {
        out.push({
          id,
          heroCards: m.hero_cards ?? [],
          board: m.board ?? [],
          parsed: null,
          marked: m,
        });
      }
    }
    return out;
  }, [imported, markedByCode]);

  const selectedRow = rows.find((r) => r.id === selectedId) ?? null;
  const hand: ParsedHand | null =
    (selectedRow?.parsed ?? (selectedId ? replayCache[selectedId] : null)) ??
    null;
  const frames = hand?.frames ?? [];
  const frame = frames[step];

  // fetch replay for a persisted marked hand that has no in-memory frames
  useEffect(() => {
    if (!selectedRow || selectedRow.parsed || !selectedRow.marked) return;
    if (replayCache[selectedRow.id]) return;
    let cancelled = false;
    fetchMarkedHandReplay(selectedRow.marked.id).then((rep) => {
      if (!cancelled && rep) {
        setReplayCache((c) => ({ ...c, [selectedRow.id]: rep }));
      }
    });
    return () => {
      cancelled = true;
    };
  }, [selectedRow, replayCache]);

  // autoplay
  useEffect(() => {
    if (!playing || !hand) return;
    if (step >= frames.length - 1) {
      setPlaying(false);
      return;
    }
    const t = setTimeout(() => setStep((s) => s + 1), 1100);
    return () => clearTimeout(t);
  }, [playing, step, frames.length, hand]);

  // default selection: first row
  useEffect(() => {
    if (!selectedId && rows.length > 0) setSelectedId(rows[0].id);
  }, [rows, selectedId]);

  async function onFiles(files: FileList) {
    setError(null);
    setLoading(true);
    try {
      const collected: ParsedHand[] = [];
      for (const file of Array.from(files)) {
        const res = await api.upload<ParseHandsResponse>("/hands/parse", file);
        collected.push(...res.hands);
      }
      setImported((prev) => {
        const seen = new Set(prev.map((h) => h.hand_id));
        const merged = [...prev];
        for (const h of collected) {
          if (!seen.has(h.hand_id)) {
            merged.push(h);
            seen.add(h.hand_id);
          }
        }
        return merged;
      });
      setSelectedId((cur) => cur ?? collected[0]?.hand_id ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not parse file");
    } finally {
      setLoading(false);
    }
  }

  function selectHand(id: string) {
    setSelectedId(id);
    setStep(0);
    setPlaying(false);
  }

  function toggleMark(row: Row) {
    if (row.marked) {
      deleteMark.mutate(row.marked.id);
    } else if (row.parsed) {
      createMark.mutate({
        hand_code: `#${row.id}`,
        poker_room: "PokerStars",
        date: (row.parsed.played_at ?? new Date().toISOString()).slice(0, 10),
        replay: row.parsed,
      });
    }
  }

  function removeHand(row: Row) {
    setImported((prev) => prev.filter((h) => h.hand_id !== row.id));
    if (row.marked) deleteMark.mutate(row.marked.id); // remove persisted copy too
    if (selectedId === row.id) {
      const rest = rows.filter((r) => r.id !== row.id);
      setSelectedId(rest[0]?.id ?? null);
      setStep(0);
    }
  }

  function removeUnmarked() {
    setImported((prev) => prev.filter((h) => markedByCode.has(h.hand_id)));
    setSelectedId((cur) => (cur && markedByCode.has(cur) ? cur : null));
  }

  const unmarkedCount = imported.filter(
    (h) => !markedByCode.has(h.hand_id),
  ).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Hand Replayer</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setUnit((u) => (u === "bb" ? "abs" : "bb"))}
            className={cn(
              "flex items-center gap-2 rounded-md border border-border px-3 text-sm transition-colors",
              "hover:bg-secondary",
            )}
            title="Toggle Big Blinds / absolute value"
          >
            <span
              className={cn(
                "relative inline-flex h-4 w-7 items-center rounded-full transition-colors",
                unit === "bb" ? "bg-primary" : "bg-muted",
              )}
            >
              <span
                className={cn(
                  "inline-block h-3 w-3 rounded-full bg-white transition-transform",
                  unit === "bb" ? "translate-x-3.5" : "translate-x-0.5",
                )}
              />
            </span>
            {unit === "bb" ? "BB" : "Value"}
          </button>
          {unmarkedCount > 0 && (
            <Button variant="outline" onClick={removeUnmarked}>
              <Trash2 className="h-4 w-4" />
              Delete unmarked ({unmarkedCount})
            </Button>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".txt"
            multiple
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.length) onFiles(e.target.files);
              e.target.value = "";
            }}
          />
          <Button onClick={() => fileRef.current?.click()} disabled={loading}>
            <Upload className="h-4 w-4" />
            {loading ? "Parsing…" : "Import files"}
          </Button>
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {rows.length === 0 && !loading ? (
        <Card className="flex flex-col items-center justify-center gap-2 py-16 text-center">
          <Upload className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Import PokerStars .txt hand histories. Marked hands are saved and
            stay here.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
          {/* left: hand list */}
          <Card className="max-h-[75vh] divide-y divide-border/50 overflow-y-auto p-0">
            {rows.map((row) => {
              const isMarked = Boolean(row.marked);
              const isActive = row.id === selectedId;
              return (
                <div
                  key={row.id}
                  className={cn(
                    "flex cursor-pointer items-center gap-2 px-3 py-2 transition-colors",
                    isActive
                      ? "bg-secondary"
                      : isMarked
                        ? "bg-amber-500/10 hover:bg-amber-500/15"
                        : "hover:bg-secondary/60",
                  )}
                  onClick={() => selectHand(row.id)}
                >
                  <div className="flex gap-0.5">
                    {row.heroCards.length > 0 ? (
                      row.heroCards.map((c, i) => (
                        <CardEl key={i} card={c} size="sm" />
                      ))
                    ) : (
                      <>
                        <CardEl faceDown size="sm" />
                        <CardEl faceDown size="sm" />
                      </>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs font-medium">
                      {row.board.join(" ") || "Preflop"}
                    </p>
                    <p className="truncate text-[11px] text-muted-foreground">
                      #{row.id}
                    </p>
                  </div>
                  <button
                    type="button"
                    aria-label={isMarked ? "Unmark" : "Mark"}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleMark(row);
                    }}
                    className="shrink-0 p-1"
                  >
                    <Star
                      className={cn(
                        "h-4 w-4",
                        isMarked
                          ? "fill-amber-400 text-amber-400"
                          : "text-muted-foreground",
                      )}
                    />
                  </button>
                  <button
                    type="button"
                    aria-label="Remove"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeHand(row);
                    }}
                    className="shrink-0 p-1 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              );
            })}
          </Card>

          {/* right: replayer */}
          {hand && frame ? (
            <Card className="space-y-4 bg-background/40 p-4">
              <PokerTable hand={hand} frame={frame} unit={unit} />
              <div className="text-center text-sm font-medium">{frame.label}</div>
              <div className="flex items-center justify-center gap-3">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    setPlaying(false);
                    setStep((s) => Math.max(0, s - 1));
                  }}
                  disabled={step === 0}
                  aria-label="Previous"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  size="icon"
                  onClick={() => {
                    if (step >= frames.length - 1) setStep(0);
                    setPlaying((p) => !p);
                  }}
                  aria-label={playing ? "Pause" : "Play"}
                >
                  {playing ? (
                    <Pause className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    setPlaying(false);
                    setStep((s) => Math.min(frames.length - 1, s + 1));
                  }}
                  disabled={step >= frames.length - 1}
                  aria-label="Next"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <input
                type="range"
                min={0}
                max={frames.length - 1}
                value={step}
                onChange={(e) => {
                  setPlaying(false);
                  setStep(Number(e.target.value));
                }}
                className="w-full accent-primary"
              />
              <div className="text-center text-xs text-muted-foreground">
                Step {step + 1} / {frames.length}
              </div>
            </Card>
          ) : (
            <Card className="flex items-center justify-center py-16 text-sm text-muted-foreground">
              Select a hand to replay.
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
