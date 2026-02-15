# BTB v1 — Research & Tracking Backbone (Executable Spec)

## Goal
Build a pro-grade, agent-friendly betting research backbone:
- Multi-season NBA (5–10 years) regular season + playoffs
- Odds + props across books (incl AU) with raw + normalized storage
- Stats + play-by-play ingestion
- Clean Python APIs + Typer CLI
- Tables for bets/CLV/limits/recommendations scaffolding (logic later)

## Repo layout (locked)
- Repo: BTB
- Package: btb (src/btb)

## CLI
- Root: `btb`
- Phase1 group: `btb phase1 ...` (ingest + research views)

## v1 Data Sources (minimum)
- Odds: The Odds API (main markets; AU books)
- Props: Secondary props-heavy provider (TBD) – stubbed adapter OK
- Stats: Stable NBA stats provider (balldontlie or similar)
- PBP: Stable play-by-play feed (stub OK initially)

## DB
- SQLite v1, schema owned by btb/db/schema.py
- Always store provider raw payloads in raw_provider_* tables

## Core tables (v1)
- leagues, seasons, teams, players
- games (with playoff context fields)
- stats_player_game
- play_by_play_events
- books
- odds_markets
- props_markets
- raw_provider_odds / raw_provider_props / raw_provider_stats / raw_provider_pbp
- bets, clv_observations, limits_snapshots (scaffolding)

## Degraded mode
Every ingest command must:
- Not crash the CLI
- Return structured summary with reason codes on failure

## Tests (minimum)
- schema create_all works
- fixture parsing inserts odds/stats rows
- research query returns expected keys
