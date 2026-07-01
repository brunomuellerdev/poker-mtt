"""Parse PokerStars No-Limit Hold'em hand histories into animation frames.

Scope: NLHE only (tournament — incl. bounty/PKO — and cash). A file may hold
many hands. Each hand is reduced to a list of *frames*: a full table snapshot
per step (pot, per-player stack/bet/state, visible board), so the frontend only
renders frame[i] and never reconstructs game state itself.

Pure module: no I/O, no DB. Amounts are Decimal (chips as integers, cash as $).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

_ZERO = Decimal("0")

# --- header --------------------------------------------------------------
# Tournament: "...: Tournament #TID, $a+$b(+$c) USD Hold'em No Limit - Level X
#              (sb/bb) - DATE [ET]"
# Cash:       "...:  Hold'em No Limit ($sb/$bb USD) - DATE [ET]"
_RE_HEADER_TOURNEY = re.compile(
    r"PokerStars Hand #(?P<hid>\d+): Tournament #(?P<tid>\d+), "
    r"(?P<buyin>[^ ]+) USD Hold'em No Limit - Level (?P<level>[^ ]+) "
    r"\((?P<sb>[\d.]+)/(?P<bb>[\d.]+)\) - "
    r"(?P<date>[\d/]+ [\d:]+) (?P<tz>\w+)"
)
_RE_HEADER_CASH = re.compile(
    r"PokerStars Hand #(?P<hid>\d+):\s+Hold'em No Limit "
    r"\(\$(?P<sb>[\d.]+)/\$(?P<bb>[\d.]+) USD\) - "
    r"(?P<date>[\d/]+ [\d:]+) (?P<tz>\w+)"
)
_RE_TABLE = re.compile(
    r"Table '(?P<name>.+)' (?P<max>\d+)-max Seat #(?P<button>\d+) is the button"
)
_RE_SEAT = re.compile(
    r"Seat (?P<seat>\d+): (?P<name>.+?) \((?P<stack>[\d,.$]+) in chips"
    r"(?:, \$(?P<bounty>[\d.]+) bounty)?\)"
)
_RE_DEALT = re.compile(r"Dealt to (?P<name>.+) \[(?P<cards>[^\]]+)\]")

# noise lines that are not actions
_NOISE = (
    " has timed out",
    " is sitting out",
    " has returned",
    " is disconnected",
    " is connected",
    " joins the table",
    " leaves the table",
    " was removed from the table",
    " has been disconnected",
    " will be allowed to play",
    " said,",
    " is sitting in",
    " sits out",
)

_STREET_MARKERS = {
    "*** HOLE CARDS ***": "preflop",
    "*** FLOP ***": "flop",
    "*** TURN ***": "turn",
    "*** RIVER ***": "river",
    "*** SHOW DOWN ***": "showdown",
    "*** FIRST FLOP ***": "flop",
}


def _num(raw: str) -> Decimal:
    return Decimal(raw.replace("$", "").replace(",", ""))


def _post_amount(rest: str) -> Decimal:
    """Amount from a 'posts ...' line. Handles the trailing 'and is all-in'
    suffix that appears when the post puts the player all-in (stack < ante/blind).
    """
    m = re.search(r"([\d,]+(?:\.\d+)?)(?:\s+and is all-in)?\s*$", rest)
    if not m:
        raise ValueError(f"no amount in post line: {rest!r}")
    return _num(m.group(1))


@dataclass
class PlayerState:
    seat: int
    name: str
    stack: Decimal
    bounty: Decimal | None = None
    street_bet: Decimal = _ZERO
    committed: Decimal = _ZERO
    folded: bool = False
    all_in: bool = False
    is_hero: bool = False
    is_button: bool = False
    cards: list[str] = field(default_factory=list)
    won: Decimal = _ZERO


@dataclass
class Frame:
    label: str
    street: str
    board: list[str]
    pot: Decimal
    players: list[dict]
    actor: str | None = None


@dataclass
class ParsedHand:
    hand_id: str
    variant: str  # "tournament" | "cash"
    is_chips: bool
    currency: str  # "$" for cash, "" for tournament chips
    tournament_id: str | None
    buyin: str | None
    level: str | None
    small_blind: Decimal
    big_blind: Decimal
    played_at: datetime | None
    table_name: str
    max_seats: int
    button_seat: int
    hero: str | None
    board: list[str]
    frames: list[Frame]
    total_pot: Decimal
    rake: Decimal


def split_hands(text: str) -> list[str]:
    """Split a file into raw per-hand blocks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks: list[str] = []
    current: list[str] = []
    for line in text.split("\n"):
        if line.startswith("PokerStars Hand #") and current:
            blocks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        tail = "\n".join(current).strip()
        if tail:
            blocks.append(tail)
    return [b for b in blocks if b.startswith("PokerStars Hand #")]


def parse_hands(text: str) -> list[ParsedHand]:
    return [parse_hand(b) for b in split_hands(text)]


class _Builder:
    """Replays one hand's action stream into frames with running state."""

    def __init__(self, players: dict[str, PlayerState]):
        self.players = players
        self.board: list[str] = []
        self.street = "preflop"
        self.frames: list[Frame] = []

    @property
    def pot(self) -> Decimal:
        return sum((p.committed for p in self.players.values()), _ZERO)

    def snapshot(self, label: str, actor: str | None = None) -> None:
        self.frames.append(
            Frame(
                label=label,
                street=self.street,
                board=list(self.board),
                pot=self.pot,
                actor=actor,
                players=[
                    {
                        "seat": p.seat,
                        "name": p.name,
                        "stack": str(p.stack),
                        "bounty": str(p.bounty) if p.bounty is not None else None,
                        "street_bet": str(p.street_bet),
                        "committed": str(p.committed),
                        "folded": p.folded,
                        "all_in": p.all_in,
                        "is_hero": p.is_hero,
                        "is_button": p.is_button,
                        "cards": list(p.cards),
                        "won": str(p.won),
                    }
                    for p in sorted(self.players.values(), key=lambda x: x.seat)
                ],
            )
        )

    def commit(self, name: str, amount: Decimal) -> None:
        p = self.players[name]
        p.stack -= amount
        p.street_bet += amount
        p.committed += amount
        if p.stack <= _ZERO:
            p.stack = _ZERO
            p.all_in = True

    def raise_to(self, name: str, to_total: Decimal) -> None:
        # `to_total` is this player's total street bet after the raise
        p = self.players[name]
        delta = to_total - p.street_bet
        self.commit(name, delta)

    def new_street(self, street: str, board: list[str]) -> None:
        self.street = street
        for p in self.players.values():
            p.street_bet = _ZERO
        if board:
            self.board = board


def _split_name_action(line: str) -> tuple[str, str] | None:
    """A player line is 'NAME: rest'. Names may contain spaces and '$' but not
    ': ' — split on the first ': '."""
    idx = line.find(": ")
    if idx == -1:
        return None
    return line[:idx], line[idx + 2 :]


def parse_hand(block: str) -> ParsedHand:
    lines = [ln for ln in block.split("\n") if ln.strip()]
    header = lines[0]

    variant = "tournament" if "Tournament #" in header else "cash"
    is_chips = variant == "tournament"
    currency = "" if is_chips else "$"

    if variant == "tournament":
        m = _RE_HEADER_TOURNEY.match(header)
    else:
        m = _RE_HEADER_CASH.match(header)
    if not m:
        raise ValueError(f"Unrecognized header: {header[:80]}")

    g = m.groupdict()
    hand_id = g["hid"]
    tournament_id = g.get("tid")
    buyin = g.get("buyin")
    level = g.get("level")
    small_blind = _num(g["sb"])
    big_blind = _num(g["bb"])
    try:
        played_at = datetime.strptime(g["date"], "%Y/%m/%d %H:%M:%S")
    except ValueError:
        played_at = None

    tm = _RE_TABLE.search(block)
    table_name = tm.group("name") if tm else ""
    max_seats = int(tm.group("max")) if tm else 0
    button_seat = int(tm.group("button")) if tm else 0

    # seats
    players: dict[str, PlayerState] = {}
    hero: str | None = None
    i = 1
    while i < len(lines):
        sm = _RE_SEAT.match(lines[i])
        if sm:
            seat = int(sm.group("seat"))
            name = sm.group("name")
            players[name] = PlayerState(
                seat=seat,
                name=name,
                stack=_num(sm.group("stack")),
                bounty=_num(sm.group("bounty")) if sm.group("bounty") else None,
                is_button=(seat == button_seat),
            )
        elif lines[i].startswith(("Seat", "Table", "PokerStars")):
            pass
        i += 1

    b = _Builder(players)

    # walk the body: posts -> streets/actions -> showdown -> collects
    in_summary = False
    for ln in lines[1:]:
        if ln.startswith("*** SUMMARY ***"):
            in_summary = True
            continue

        # street markers
        matched_street = None
        for marker, street in _STREET_MARKERS.items():
            if ln.startswith(marker):
                matched_street = street
                # board cards may follow in brackets (flop/turn/river)
                cards = re.findall(r"\[([^\]]+)\]", ln)
                board_cards = list(b.board)
                if cards:
                    # last bracket holds the newly revealed card(s) for turn/river,
                    # full board for flop
                    flat: list[str] = []
                    for c in cards:
                        flat.extend(c.split())
                    board_cards = flat if street == "flop" else b.board + [flat[-1]]
                if matched_street != "preflop":
                    b.new_street(street, board_cards)
                    if street in ("flop", "turn", "river"):
                        b.snapshot(f"{street.title()}: {' '.join(b.board)}")
                else:
                    b.street = "preflop"
                break
        if matched_street is not None:
            continue

        # Dealt to hero
        dm = _RE_DEALT.match(ln)
        if dm:
            name = dm.group("name")
            if name in players:
                players[name].cards = dm.group("cards").split()
                players[name].is_hero = True
                hero = name
            continue

        if in_summary:
            continue  # summary section: handled separately below

        # noise
        if any(tok in ln for tok in _NOISE):
            continue

        # uncalled bet returned
        um = re.match(r"Uncalled bet \(([\d,.$]+)\) returned to (.+)", ln)
        if um:
            amount = _num(um.group(1))
            name = um.group(2)
            if name in players:
                p = players[name]
                p.stack += amount
                p.street_bet -= amount
                p.committed -= amount
                if p.all_in and amount > 0:
                    p.all_in = False
            continue

        # collected from pot
        cm = re.match(r"(.+) collected ([\d,.$]+) from (?:the )?(?:main |side )?pot", ln)
        if cm and not in_summary:
            name, amount = cm.group(1), _num(cm.group(2))
            if name in players:
                players[name].won += amount
                b.snapshot(f"{name} wins {currency}{_fmt(amount, is_chips)}", actor=name)
            continue

        # player actions
        na = _split_name_action(ln)
        if not na:
            continue
        name, rest = na
        if name not in players:
            continue
        p = players[name]
        all_in = "and is all-in" in rest

        if rest.startswith("posts the ante"):
            amt = _post_amount(rest)
            p.stack -= amt
            p.committed += amt  # ante is dead money: pot only, not street_bet
            if p.stack <= _ZERO:
                p.stack = _ZERO
                p.all_in = True
        elif rest.startswith(
            ("posts small blind", "posts big blind", "posts small & big blinds")
        ):
            b.commit(name, _post_amount(rest))
        elif rest.startswith("folds"):
            p.folded = True
            b.snapshot(f"{name} folds", actor=name)
        elif rest.startswith("checks"):
            b.snapshot(f"{name} checks", actor=name)
        elif rest.startswith("calls"):
            amt = _num(re.search(r"calls ([\d,.$]+)", rest).group(1))
            b.commit(name, amt)
            b.snapshot(f"{name} calls {currency}{_fmt(amt, is_chips)}", actor=name)
        elif rest.startswith("bets"):
            amt = _num(re.search(r"bets ([\d,.$]+)", rest).group(1))
            b.commit(name, amt)
            tag = " all-in" if all_in else ""
            b.snapshot(f"{name} bets {currency}{_fmt(amt, is_chips)}{tag}", actor=name)
        elif rest.startswith("raises"):
            to_total = _num(re.search(r"raises [\d,.$]+ to ([\d,.$]+)", rest).group(1))
            b.raise_to(name, to_total)
            tag = " all-in" if all_in else ""
            b.snapshot(f"{name} raises to {currency}{_fmt(to_total, is_chips)}{tag}", actor=name)
        elif rest.startswith("shows"):
            cm2 = re.search(r"shows \[([^\]]+)\]", rest)
            if cm2:
                p.cards = cm2.group(1).split()
                b.snapshot(f"{name} shows {' '.join(p.cards)}", actor=name)
        # mucks / doesn't show / other -> ignore

    # insert an initial frame (blinds posted, hole cards) at the front
    # by snapshotting current pre-action state is tricky after the fact; instead
    # we reconstruct: the first action frames already reflect posts. Prepend a
    # "hole cards" frame using the first frame's pot if present.
    if b.frames:
        first = b.frames[0]
        b.frames.insert(
            0,
            Frame(
                label="Blinds posted — hole cards dealt",
                street="preflop",
                board=[],
                pot=first.pot
                if first.street == "preflop"
                else _ZERO,
                players=first.players,
            ),
        )

    # summary: rake, total pot, finishers
    total_pot = _ZERO
    rake = _ZERO
    sm = re.search(r"Total pot ([\d,.$]+).*?\| Rake ([\d,.$]+)", block)
    if sm:
        total_pot = _num(sm.group(1))
        rake = _num(sm.group(2))

    board: list[str] = b.board
    bm = re.search(r"Board \[([^\]]+)\]", block)
    if bm:
        board = bm.group(1).split()

    return ParsedHand(
        hand_id=hand_id,
        variant=variant,
        is_chips=is_chips,
        currency=currency,
        tournament_id=tournament_id,
        buyin=buyin,
        level=level,
        small_blind=small_blind,
        big_blind=big_blind,
        played_at=played_at,
        table_name=table_name,
        max_seats=max_seats,
        button_seat=button_seat,
        hero=hero,
        board=board,
        frames=b.frames,
        total_pot=total_pot,
        rake=rake,
    )


def _fmt(v: Decimal, is_chips: bool) -> str:
    if is_chips:
        return f"{int(v):,}"
    return f"{v:.2f}"


def hand_to_dict(h: ParsedHand) -> dict:
    hero_cards: list[str] = []
    if h.frames:
        for p in h.frames[0].players:
            if p["is_hero"]:
                hero_cards = list(p["cards"])
                break
    return {
        "hand_id": h.hand_id,
        "variant": h.variant,
        "is_chips": h.is_chips,
        "currency": h.currency,
        "tournament_id": h.tournament_id,
        "buyin": h.buyin,
        "level": h.level,
        "small_blind": str(h.small_blind),
        "big_blind": str(h.big_blind),
        "played_at": h.played_at.isoformat() if h.played_at else None,
        "table_name": h.table_name,
        "max_seats": h.max_seats,
        "button_seat": h.button_seat,
        "hero": h.hero,
        "hero_cards": hero_cards,
        "board": h.board,
        "total_pot": str(h.total_pot),
        "rake": str(h.rake),
        "frames": [
            {
                "label": f.label,
                "street": f.street,
                "board": f.board,
                "pot": str(f.pot),
                "actor": f.actor,
                "players": f.players,
            }
            for f in h.frames
        ],
    }
