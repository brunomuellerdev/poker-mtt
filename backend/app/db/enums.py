import enum


class GameType(enum.StrEnum):
    HOLDEM = "holdem"
    OMAHA = "omaha"
    OMAHA_HILO = "omaha_hilo"
    STUD = "stud"


class BettingStructure(enum.StrEnum):
    NL = "nl"
    PL = "pl"
    FL = "fl"


class EmotionalState(enum.StrEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    TIRED = "tired"
    TILT = "tilt"
    FRUSTRATED = "frustrated"
    DISTRACTED = "distracted"


# Orthogonal axes — replace the overlapping `format` / `tournament_type` enums
class Speed(enum.StrEnum):
    REGULAR = "regular"
    TURBO = "turbo"
    HYPER = "hyper"
    DEEP = "deep"


class TournamentType(enum.StrEnum):
    NORMAL = "normal"
    SATELLITE = "satellite"
    SHOOTOUT = "shootout"


class BountyType(enum.StrEnum):
    NONE = "none"
    KNOCKOUT = "knockout"
    PROGRESSIVE = "progressive"  # PKO
    MYSTERY = "mystery"
