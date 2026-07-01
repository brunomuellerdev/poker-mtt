import { Pencil, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import {
  useCreateMarkedHand,
  useDeleteMarkedHand,
  useMarkedHands,
  useUpdateMarkedHand,
} from "@/hooks/useMarkedHands";
import { ApiError } from "@/lib/api";
import { POKER_ROOMS } from "@/lib/pokerRooms";
import { formatDate } from "@/lib/utils";
import type { MarkedHand, MarkedHandCreate } from "@/types/api";

const EMPTY: MarkedHandCreate = {
  hand_code: "",
  poker_room: "GGPoker",
  date: new Date().toISOString().slice(0, 10),
};

export function MarkedHandsPage() {
  const { data, isLoading } = useMarkedHands();
  const del = useDeleteMarkedHand();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<MarkedHand | null>(null);

  const rows = data ?? [];

  function openCreate() {
    setEditing(null);
    setOpen(true);
  }
  function openEdit(h: MarkedHand) {
    setEditing(h);
    setOpen(true);
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Marked Hands</h1>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" />
          Mark hand
        </Button>
      </div>

      <Card className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-border text-center text-muted-foreground">
            <tr>
              <th className="px-4 py-3 text-center font-medium">Hand code</th>
              <th className="px-4 py-3 text-center font-medium">Room</th>
              <th className="px-4 py-3 text-center font-medium">Date</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-muted-foreground">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-muted-foreground">
                  No marked hands yet.
                </td>
              </tr>
            )}
            {rows.map((h) => (
              <tr key={h.id} className="border-b border-border/50">
                <td className="px-4 py-3 text-center font-mono">{h.hand_code}</td>
                <td className="px-4 py-3 text-center">{h.poker_room}</td>
                <td className="px-4 py-3 text-center">{formatDate(h.date)}</td>
                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => openEdit(h)}
                    aria-label="Edit"
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => del.mutate(h.id)}
                    aria-label="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <MarkedHandDialog
        open={open}
        hand={editing}
        onClose={() => {
          setOpen(false);
          setEditing(null);
        }}
      />
    </div>
  );
}

function MarkedHandDialog({
  open,
  hand,
  onClose,
}: {
  open: boolean;
  hand: MarkedHand | null;
  onClose: () => void;
}) {
  const create = useCreateMarkedHand();
  const update = useUpdateMarkedHand();
  const [form, setForm] = useState<MarkedHandCreate>(EMPTY);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setForm(
        hand
          ? { hand_code: hand.hand_code, poker_room: hand.poker_room, date: hand.date }
          : EMPTY,
      );
      setError(null);
    }
  }, [open, hand]);

  if (!open) return null;

  function set<K extends keyof MarkedHandCreate>(k: K, v: MarkedHandCreate[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (hand) await update.mutateAsync({ id: hand.id, data: form });
      else await create.mutateAsync(form);
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to save");
    }
  }

  const pending = create.isPending || update.isPending;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border border-border bg-card p-5">
        <h2 className="mb-4 text-lg font-semibold">
          {hand ? "Edit marked hand" : "Mark hand"}
        </h2>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label>Hand code</Label>
            <Input
              value={form.hand_code}
              onChange={(e) => set("hand_code", e.target.value)}
              placeholder="#261297021889"
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label>Poker room</Label>
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
          </div>
          <div className="space-y-1.5">
            <Label>Date</Label>
            <Input
              type="date"
              value={form.date}
              onChange={(e) => set("date", e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
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
