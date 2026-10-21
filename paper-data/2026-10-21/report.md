# PAPER day report 2026-10-21

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Interim report — this session is not finalized yet.

Day P&L: $-9.49 (-0.954%)  |  equity $994.46 -> $984.96
Trades: 2  wins: 0  win rate: 0%
Rules version (day): 6  mode: LIVE-PAPER  job: A  jobs: ['A']  halted: False
Open positions at report time: 1

## Startup

- STARTUP: Job A started at 2026-10-21 09:26:39 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 4.8 min gap (08:36–08:40 CT) missed_windows=['R8']
- STALL: None min gap (startup–09:26 CT) missed_windows=['R8']
- STALL: 31.8 min gap (08:54–09:26 CT) missed_windows=[]
- missed_entry_window: True

## Trades

- 08:35:09->08:41:09  short CRWD  rule=R8  pnl=$-4.42  R=-1.04  exit=STOP  hold=3.0m
- 08:35:09->08:48:58  short MSTR  rule=R8  pnl=$-5.61  R=-1.03  exit=STOP  hold=13.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 2 | 0 | -10.04 |

## Cumulative paper account

Sessions: 7  start $1000.00 -> $994.46  total P&L $-5.54 (-0.554%)
Cumulative trades: 41  wins: 15  win rate: 37%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4
- 2026-10-16: $-4.22 (-0.421%)  trades=12 wins=4  end=$996.58  rules_v=5
- 2026-10-19: $+2.00 (+0.201%)  trades=8 wins=4  end=$998.58  rules_v=5
- 2026-10-20: $-4.13 (-0.413%)  trades=13 wins=4  end=$994.46  rules_v=5

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=9 wins=6 wr=67%  pnl=$11.41  avgR=0.2776  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
