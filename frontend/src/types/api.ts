export type GameType = "holdem" | "omaha" | "omaha_hilo" | "stud";
export type BettingStructure = "nl" | "pl" | "fl";
export type Speed = "regular" | "turbo" | "hyper" | "deep";
export type TournamentType = "normal" | "satellite" | "shootout";
export type BountyType = "none" | "knockout" | "progressive" | "mystery";
export type EmotionalState =
  | "excellent"
  | "good"
  | "neutral"
  | "tired"
  | "tilt"
  | "frustrated"
  | "distracted";

export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

export interface AccessToken {
  access_token: string;
  token_type: string;
}

export interface Tag {
  id: string;
  name: string;
}

export interface Tournament {
  id: string;
  date: string;
  start_time: string | null;
  poker_room: string;
  tournament_name: string | null;
  game_type: GameType;
  betting_structure: BettingStructure;
  speed: Speed;
  tournament_type: TournamentType;
  allows_rebuy: boolean;
  allows_reentry: boolean;
  allows_addon: boolean;
  bounty_type: BountyType;
  table_size: number;
  final_table_size: number;
  currency: string;
  fx_rate_to_base: string;
  buy_in: string;
  addon_cost: string;
  guarantee: string | null;
  prize: string;
  bounty: string;
  rebuys: number;
  reentries: number;
  add_ons: number;
  entrants: number;
  final_position: number;
  duration_minutes: number | null;
  notes: string | null;
  total_cost: string;
  total_winnings: string;
  profit_native: string;
  profit_base: string;
  itm: boolean;
  winner: boolean;
  final_table: boolean;
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

export interface TournamentCreate {
  date: string;
  poker_room: string;
  game_type: GameType;
  betting_structure: BettingStructure;
  speed?: Speed;
  tournament_type?: TournamentType;
  allows_rebuy?: boolean;
  allows_reentry?: boolean;
  allows_addon?: boolean;
  bounty_type?: BountyType;
  table_size?: number;
  final_table_size?: number | null;
  start_time?: string | null;
  tournament_name?: string | null;
  currency?: string;
  fx_rate_to_base?: string;
  buy_in: string;
  addon_cost?: string;
  guarantee?: string | null;
  prize?: string;
  bounty?: string;
  rebuys?: number;
  reentries?: number;
  add_ons?: number;
  entrants: number;
  final_position: number;
  duration_minutes?: number | null;
  notes?: string | null;
  tag_ids?: string[];
}

export interface Page<T> {
  items: T[];
  next_offset: number | null;
  has_more: boolean;
}

export interface TournamentFilters {
  date_from?: string;
  date_to?: string;
  poker_room?: string;
  tournament_type?: TournamentType;
  speed?: Speed;
  bounty_type?: BountyType;
  buy_in_min?: string;
  buy_in_max?: string;
  itm?: boolean;
}

export interface Summary {
  tournaments: number;
  total_buyins_base: string | null;
  total_prize_base: string | null;
  total_bounty_base: string | null;
  total_profit_base: string | null;
  roi_pct: string | null;
  abi_base: string | null;
  itm_pct: string | null;
  final_table_pct: string | null;
  win_pct: string | null;
  largest_prize_base: string | null;
  largest_profit_base: string | null;
  largest_loss_base: string | null;
  max_drawdown_base: string | null;
  max_upswing_base: string | null;
  longest_win_streak: number;
  longest_loss_streak: number;
}

export interface CumulativePoint {
  date: string;
  cumulative_base: string;
}

export interface SeriesPoint {
  period: string;
  tournaments: number;
  profit_base: string | null;
  roi_pct: string | null;
}

export interface BreakdownRow {
  key: string;
  tournaments: number;
  profit_base: string | null;
  roi_pct: string | null;
  itm_pct: string | null;
  final_table_pct: string | null;
  win_pct: string | null;
}

export interface HeatmapCell {
  weekday: number;
  hour: number;
  tournaments: number;
  profit_base: string | null;
  roi_pct: string | null;
}

export interface IndicatorRow {
  indicator: string;
  value: string | null;
  classification: string | null;
}


export interface MarkedHand {
  id: string;
  hand_code: string;
  poker_room: string;
  date: string;
  hero_cards: string[] | null;
  board: string[] | null;
  has_replay: boolean;
}

export interface MarkedHandCreate {
  hand_code: string;
  poker_room: string;
  date: string;
  replay?: ParsedHand;
}

export interface FramePlayer {
  seat: number;
  name: string;
  stack: string;
  bounty: string | null;
  street_bet: string;
  committed: string;
  folded: boolean;
  all_in: boolean;
  is_hero: boolean;
  is_button: boolean;
  cards: string[];
  won: string;
}

export interface HandFrame {
  label: string;
  actor: string | null;
  street: string;
  board: string[];
  pot: string;
  players: FramePlayer[];
}

export interface ParsedHand {
  hand_id: string;
  variant: string;
  is_chips: boolean;
  currency: string;
  tournament_id: string | null;
  buyin: string | null;
  level: string | null;
  small_blind: string;
  big_blind: string;
  played_at: string | null;
  table_name: string;
  max_seats: number;
  button_seat: number;
  hero: string | null;
  hero_cards: string[];
  board: string[];
  total_pot: string;
  rake: string;
  frames: HandFrame[];
}

export interface ParseHandsResponse {
  hands: ParsedHand[];
}
