# PAPER day report 2026-10-19

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Interim report — this session is not finalized yet.

Day P&L: $+1.29 (+0.129%)  |  equity $996.58 -> $997.87
Trades: 6  wins: 3  win rate: 50%
Rules version (day): 5  mode: LIVE-PAPER  job: A  jobs: ['A']  halted: False
Open positions at report time: 1

## Stall / missed window (no backfill)

- STALL: 8.6 min gap (08:36–08:44 CT) missed_windows=['R8', 'NR7']
- STALL: 42.6 min gap (09:26–10:09 CT) missed_windows=['R6', 'NR7']
- missed_entry_window: True

## Trades

- 08:35:09->08:36:09  short AFRM  rule=R8  pnl=$0.10  R=0.03  exit=TARGET  hold=1.0m
- 08:35:09->08:55:48  short CRWD  rule=R8  pnl=$4.79  R=0.76  exit=TARGET  hold=20.0m
- 09:15:57->09:16:57  long ANET  rule=R6 EXPERIMENTAL  pnl=$-0.90  R=-1.24  exit=STOP  hold=1.0m
- 08:35:09->09:25:56  short NVDA  rule=R8  pnl=$-3.82  R=-1.05  exit=STOP  hold=51.0m
- 10:30:34->10:38:35  long CRWD  rule=R6 EXPERIMENTAL  pnl=$0.87  R=1.67  exit=TARGET  hold=8.0m
- 10:25:34->11:03:35  long MSFT  rule=R6 EXPERIMENTAL  pnl=$-0.70  R=-1.33  exit=STOP  hold=38.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 2 | 1.07 |
| R6 | True | 3 | 1 | -0.73 |
| NR7 | True | 0 | 0 | 0.00 |

## Cumulative paper account

Sessions: 5  start $1000.00 -> $996.58  total P&L $-3.42 (-0.342%)
Cumulative trades: 20  wins: 7  win rate: 35%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4
- 2026-10-16: $-4.22 (-0.421%)  trades=12 wins=4  end=$996.58  rules_v=5

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=2 wins=1 wr=50%  pnl=$0.43  avgR=0.5306  sessions=['2026-10-15']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=3 wins=2 wr=67%  pnl=$6.40  avgR=0.377  sessions=['2026-10-15', '2026-10-16']
- NR7 EXPERIMENTAL: n=2 wins=0 wr=0%  pnl=$-7.62  avgR=-1.0488  sessions=['2026-10-16']

Paper only.
