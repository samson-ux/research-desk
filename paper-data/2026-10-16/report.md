# PAPER day report 2026-10-16

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $+0.00 (+0.000%)  |  equity $1000.80 -> $1000.80
Trades: 0  wins: 0  win rate: 0%
Rules version (day): 4  mode: LIVE-PAPER  job: B  jobs: ['B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job B started at 2026-10-16 14:37:04 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: None min gap (startup–14:37 CT) missed_windows=['R6', 'R7', 'NR7']
- missed_entry_window: True

## Trades

None.

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 0 | 0 | 0.00 |
| R6 | True | 0 | 0 | 0.00 |
| R7 | True | 0 | 0 | 0.00 |
| NR7 | True | 0 | 0 | 0.00 |

## Cumulative paper account

Sessions: 5  start $1000.00 -> $1000.80  total P&L $+0.80 (+0.080%)
Cumulative trades: 8  wins: 3  win rate: 38%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4
- 2026-10-16: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.80  rules_v=4

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=2 wins=1 wr=50%  pnl=$0.43  avgR=0.5306  sessions=['2026-10-15']
- R7 EXPERIMENTAL: n=4 wins=1 wr=25%  pnl=$-2.48  avgR=-0.7279  sessions=['2026-10-15']
- R8: n=2 wins=1 wr=50%  pnl=$2.84  avgR=0.1748  sessions=['2026-10-15']
- NR7 EXPERIMENTAL: n=0 wins=0 wr=0%  pnl=$0.00  avgR=None  sessions=[]

Paper only.
