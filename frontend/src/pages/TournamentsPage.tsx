import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useDeleteTournament,
  useTournaments,
} from "@/hooks/useTournaments";
import { cn, formatDate, formatMoney, profitClass } from "@/lib/utils";
import { useFilterStore } from "@/stores/filterStore";
import type { Tournament } from "@/types/api";
import { TournamentFormDialog } from "./TournamentFormDialog";

const BOUNTY_LABELS: Record<string, string> = {
  knockout: "Knockout",
  progressive: "PKO",
  mystery: "Mystery Bounty",
};

// Badges shown in the list: tournament type (if not Normal), active entry flags,
// and bounty type. Freezeout (no flags, normal, no bounty) shows a single tag.
function structureTags(t: Tournament): string[] {
  const tags: string[] = [];
  if (t.tournament_type === "satellite") tags.push("Satellite");
  if (t.tournament_type === "shootout") tags.push("Shootout");
  if (t.allows_rebuy) tags.push("Rebuy");
  if (t.allows_reentry) tags.push("Re-entry");
  if (t.allows_addon) tags.push("Add-on");
  if (t.bounty_type !== "none") tags.push(BOUNTY_LABELS[t.bounty_type]);
  if (tags.length === 0) tags.push("Freezeout");
  return tags;
}

export function TournamentsPage() {
  const { filters, setFilters } = useFilterStore();
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Tournament | null>(null);
  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useTournaments(filters);
  const del = useDeleteTournament();

  const rows = data?.pages.flatMap((p) => p.items) ?? [];

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }

  function openEdit(t: Tournament) {
    setEditing(t);
    setFormOpen(true);
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Tournaments</h1>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" />
          Add tournament
        </Button>
      </div>

      <Card className="flex flex-wrap gap-3 p-4">
        <Input
          placeholder="Poker room"
          className="max-w-[180px]"
          value={filters.poker_room ?? ""}
          onChange={(e) => setFilters({ poker_room: e.target.value || undefined })}
        />
        <Input
          type="number"
          placeholder="Buy-in min"
          className="max-w-[130px]"
          value={filters.buy_in_min ?? ""}
          onChange={(e) => setFilters({ buy_in_min: e.target.value || undefined })}
        />
        <Input
          type="number"
          placeholder="Buy-in max"
          className="max-w-[130px]"
          value={filters.buy_in_max ?? ""}
          onChange={(e) => setFilters({ buy_in_max: e.target.value || undefined })}
        />
      </Card>

      <Card className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-border text-center text-muted-foreground">
            <tr>
              <th className="px-4 py-3 text-center font-medium">Tournament</th>
              <th className="px-4 py-3 text-center font-medium">Date</th>
              <th className="px-4 py-3 text-center font-medium">Room</th>
              <th className="px-4 py-3 text-center font-medium">Buy-in</th>
              <th className="px-4 py-3 text-center font-medium">Tags</th>
              <th className="px-4 py-3 text-center font-medium">Pos</th>
              <th className="px-4 py-3 text-center font-medium">Result</th>
              <th className="px-4 py-3 text-center font-medium">Profit</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-muted-foreground">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-muted-foreground">
                  No tournaments yet.
                </td>
              </tr>
            )}
            {rows.map((t) => (
              <tr key={t.id} className="border-b border-border/50">
                <td className="px-4 py-3 text-center">
                  {t.tournament_name ?? "—"}
                </td>
                <td className="px-4 py-3 text-center">{formatDate(t.date)}</td>
                <td className="px-4 py-3 text-center">{t.poker_room}</td>
                <td className="px-4 py-3 text-center">
                  {formatMoney(t.buy_in)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap justify-center gap-1">
                    {structureTags(t).map((tag) => (
                      <Badge key={tag}>{tag}</Badge>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  {t.status === "registered"
                    ? "—"
                    : `${t.final_position}/${t.entrants}`}
                </td>
                <td className="px-4 py-3 text-center">
                  {t.status === "registered" ? (
                    <Badge variant="registered">Registered</Badge>
                  ) : t.winner ? (
                    <Badge variant="success">Win</Badge>
                  ) : t.final_table ? (
                    <Badge variant="warning">FT</Badge>
                  ) : t.itm ? (
                    <Badge>ITM</Badge>
                  ) : (
                    <Badge variant="destructive">OTM</Badge>
                  )}
                </td>
                <td
                  className={cn(
                    "px-4 py-3 text-center font-medium",
                    t.status !== "registered" && profitClass(t.profit_base),
                  )}
                >
                  {t.status === "registered" ? "—" : formatMoney(t.profit_base)}
                </td>
                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => openEdit(t)}
                    aria-label="Edit"
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => del.mutate(t.id)}
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

      {hasNextPage && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
          >
            {isFetchingNextPage ? "Loading…" : "Load more"}
          </Button>
        </div>
      )}

      <TournamentFormDialog
        open={formOpen}
        tournament={editing}
        onClose={() => {
          setFormOpen(false);
          setEditing(null);
        }}
      />
    </div>
  );
}
