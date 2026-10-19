# PAPER day report 2026-10-19

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $+2.00 (+0.201%)  |  equity $996.58 -> $998.58
Trades: 8  wins: 4  win rate: 50%
Rules version (day): 5  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job B started at 2026-10-19 11:30:50 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

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
- 08:44:58->14:55:00  short JNJ  rule=NR7 EXPERIMENTAL  pnl=$-0.35  R=-0.19  exit=EOD_FLATTEN_1455  hold=370.0m
- 13:27:59->14:55:00  short COIN  rule=NR7 EXPERIMENTAL  pnl=$2.01  R=0.36  exit=EOD_FLATTEN_1455  hold=87.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 2 | 1.07 |
| R6 | True | 3 | 1 | -0.73 |
| NR7 | True | 2 | 1 | 1.66 |

## Cumulative paper account

Sessions: 6  start $1000.00 -> $998.58  total P&L $-1.42 (-0.142%)
Cumulative trades: 28  wins: 11  win rate: 39%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4
- 2026-10-16: $-4.22 (-0.421%)  trades=12 wins=4  end=$996.58  rules_v=5
- 2026-10-19: $+2.00 (+0.201%)  trades=8 wins=4  end=$998.58  rules_v=5

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=5 wins=2 wr=40%  pnl=$-0.30  avgR=0.031  sessions=['2026-10-15', '2026-10-19']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=6 wins=4 wr=67%  pnl=$7.47  avgR=0.1448  sessions=['2026-10-15', '2026-10-16', '2026-10-19']
- NR7 EXPERIMENTAL: n=4 wins=1 wr=25%  pnl=$-5.96  avgR=-0.4815  sessions=['2026-10-16', '2026-10-19']

Paper only.
