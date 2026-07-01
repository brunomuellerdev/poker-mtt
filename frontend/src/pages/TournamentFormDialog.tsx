import { type FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  useCreateTournament,
  useUpdateTournament,
} from "@/hooks/useTournaments";
import { ApiError } from "@/lib/api";
import { POKER_ROOMS } from "@/lib/pokerRooms";
import type {
  BettingStructure,
  BountyType,
  GameType,
  Speed,
  Tournament,
  TournamentCreate,
  TournamentType,
} from "@/types/api";

interface Props {
  open: boolean;
  onClose: () => void;
  // when provided, the dialog edits this tournament instead of creating one
  tournament?: Tournament | null;
}

const GAME_TYPES: GameType[] = ["holdem", "omaha", "omaha_hilo", "stud"];
const BETTING: BettingStructure[] = ["nl", "pl", "fl"];
const SPEEDS: Speed[] = ["regular", "turbo", "hyper", "deep"];
const TOURNAMENT_TYPES: { value: TournamentType; label: string }[] = [
  { value: "normal", label: "Normal" },
  { value: "satellite", label: "Satellite" },
  { value: "shootout", label: "Shootout" },
];
const BOUNTY_OPTIONS: { value: BountyType; label: string }[] = [
  { value: "none", label: "None" },
  { value: "knockout", label: "Knockout" },
  { value: "progressive", label: "Progressive Knockout" },
  { value: "mystery", label: "Mystery Bounty" },
];

const EMPTY: TournamentCreate = {
  date: new Date().toISOString().slice(0, 10),
  poker_room: "GGPoker",
  game_type: "holdem",
  betting_structure: "nl",
  speed: "regular",
  tournament_type: "normal",
  allows_rebuy: false,
  allows_reentry: false,
  allows_addon: false,
  bounty_type: "none",
  table_size: 9,
  buy_in: "",
  prize: "0",
  bounty: "0",
  entrants: 0,
  final_position: 0,
};

function toFormState(t: Tournament): TournamentCreate {
  return {
    date: t.date,
    start_time: t.start_time,
    poker_room: t.poker_room,
    tournament_name: t.tournament_name,
    game_type: t.game_type,
    betting_structure: t.betting_structure,
    speed: t.speed,
    tournament_type: t.tournament_type,
    allows_rebuy: t.allows_rebuy,
    allows_reentry: t.allows_reentry,
    allows_addon: t.allows_addon,
    bounty_type: t.bounty_type,
    table_size: t.table_size,
    final_table_size: t.final_table_size,
    currency: t.currency,
    fx_rate_to_base: t.fx_rate_to_base,
    buy_in: t.buy_in,
    addon_cost: t.addon_cost,
    guarantee: t.guarantee,
    prize: t.prize,
    bounty: t.bounty,
    rebuys: t.rebuys,
    reentries: t.reentries,
    add_ons: t.add_ons,
    entrants: t.entrants,
    final_position: t.final_position,
    duration_minutes: t.duration_minutes,
    notes: t.notes,
    tag_ids: t.tags.map((tag) => tag.id),
  };
}

export function TournamentFormDialog({ open, onClose, tournament }: Props) {
  const create = useCreateTournament();
  const update = useUpdateTournament();
  const isEdit = Boolean(tournament);
  const [form, setForm] = useState<TournamentCreate>(EMPTY);
  const [error, setError] = useState<string | null>(null);

  // sync form when the dialog opens (the component stays mounted across opens)
  useEffect(() => {
    if (open) {
      setForm(tournament ? toFormState(tournament) : EMPTY);
      setError(null);
    }
  }, [open, tournament]);

  if (!open) return null;

  function set<K extends keyof TournamentCreate>(
    key: K,
    value: TournamentCreate[K],
  ) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (tournament) {
        await update.mutateAsync({ id: tournament.id, data: form });
      } else {
        await create.mutateAsync(form);
      }
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to save");
    }
  }

  const pending = create.isPending || update.isPending;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-border bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">
          {isEdit ? "Edit tournament" : "Add tournament"}
        </h2>
        <form onSubmit={onSubmit} className="grid grid-cols-2 gap-4">
          <Field label="Date">
            <Input
              type="date"
              value={form.date}
              onChange={(e) => set("date", e.target.value)}
              required
            />
          </Field>
          <Field label="Start time">
            <Input
              type="time"
              value={(form.start_time ?? "").slice(0, 5)}
              onChange={(e) => set("start_time", e.target.value || null)}
            />
          </Field>
          <Field label="Poker room">
            <Select
              value={form.poker_room}
              onChange={(e) => set("poker_room", e.target.value)}
              required
            >
              {POKER_ROOMS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Tournament name">
            <Input
              value={form.tournament_name ?? ""}
              onChange={(e) => set("tournament_name", e.target.value || null)}
            />
          </Field>
          <Field label="Game type">
            <Select
              value={form.game_type}
              onChange={(e) => set("game_type", e.target.value as GameType)}
            >
              {GAME_TYPES.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Betting">
            <Select
              value={form.betting_structure}
              onChange={(e) =>
                set("betting_structure", e.target.value as BettingStructure)
              }
            >
              {BETTING.map((b) => (
                <option key={b} value={b}>
                  {b.toUpperCase()}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Speed">
            <Select
              value={form.speed}
              onChange={(e) => set("speed", e.target.value as Speed)}
            >
              {SPEEDS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Tournament type">
            <Select
              value={form.tournament_type}
              onChange={(e) =>
                set("tournament_type", e.target.value as TournamentType)
              }
            >
              {TOURNAMENT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
          </Field>
          <div className="col-span-2 space-y-1.5">
            <Label>Entry options</Label>
            <div className="flex flex-wrap gap-4 pt-1">
              <Checkbox
                label="Rebuy"
                checked={form.allows_rebuy ?? false}
                onChange={(v) => set("allows_rebuy", v)}
              />
              <Checkbox
                label="Re-entry"
                checked={form.allows_reentry ?? false}
                onChange={(v) => set("allows_reentry", v)}
              />
              <Checkbox
                label="Add-on"
                checked={form.allows_addon ?? false}
                onChange={(v) => set("allows_addon", v)}
              />
            </div>
          </div>
          <Field label="Bounty type">
            <Select
              value={form.bounty_type}
              onChange={(e) => set("bounty_type", e.target.value as BountyType)}
            >
              {BOUNTY_OPTIONS.map((b) => (
                <option key={b.value} value={b.value}>
                  {b.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Table size">
            <Input
              type="number"
              value={form.table_size}
              onChange={(e) => set("table_size", Number(e.target.value))}
            />
          </Field>
          <Field label="Buy-in">
            <Input
              type="number"
              step="0.01"
              value={form.buy_in}
              onChange={(e) => set("buy_in", e.target.value)}
              required
            />
          </Field>
          <Field label="Prize">
            <Input
              type="number"
              step="0.01"
              value={form.prize ?? "0"}
              onChange={(e) => set("prize", e.target.value)}
            />
          </Field>
          <Field label="Bounty">
            <Input
              type="number"
              step="0.01"
              value={form.bounty ?? "0"}
              onChange={(e) => set("bounty", e.target.value)}
            />
          </Field>
          <Field label="Rebuys">
            <Input
              type="number"
              value={form.rebuys ?? 0}
              onChange={(e) => set("rebuys", Number(e.target.value))}
            />
          </Field>
          <Field label="Re-entries">
            <Input
              type="number"
              value={form.reentries ?? 0}
              onChange={(e) => set("reentries", Number(e.target.value))}
            />
          </Field>
          <Field label="Add-on cost">
            <Input
              type="number"
              step="0.01"
              value={form.addon_cost ?? "0"}
              onChange={(e) => set("addon_cost", e.target.value)}
            />
          </Field>
          <Field label="Entrants">
            <Input
              type="number"
              value={form.entrants}
              onChange={(e) => set("entrants", Number(e.target.value))}
              required
            />
          </Field>
          <Field label="Final position">
            <Input
              type="number"
              value={form.final_position}
              onChange={(e) => set("final_position", Number(e.target.value))}
              required
            />
          </Field>

          {error && (
            <p className="col-span-2 text-sm text-destructive">{error}</p>
          )}

          <div className="col-span-2 mt-2 flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={pending}>
              {pending ? "Saving…" : "Save"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Checkbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 rounded border-input accent-primary"
      />
      {label}
    </label>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
    </div>
  );
}
