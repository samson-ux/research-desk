# PAPER day report 2026-10-15

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $+0.80 (+0.080%)  |  equity $1000.00 -> $1000.80
Trades: 8  wins: 3  win rate: 38%
Rules version (day): 4  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job A started at 2026-10-15 08:24:26 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-15 11:31:05 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 5.4 min gap (09:58–10:03 CT) missed_windows=['R6', 'R7', 'NR7']
- missed_entry_window: True

## Trades

- 08:35:33->08:41:33  long AFRM  rule=R8  pnl=$3.38  R=0.43  exit=TARGET  hold=6.0m
- 08:50:33->08:51:33  short AMD  rule=R6 EXPERIMENTAL  pnl=$-0.99  R=-1.18  exit=STOP  hold=1.0m
- 08:50:33->08:55:33  short NVDA  rule=R6 EXPERIMENTAL  pnl=$1.42  R=2.24  exit=TARGET  hold=5.0m
- 10:05:55->10:20:55  short XOM  rule=R7 EXPERIMENTAL  pnl=$-0.70  R=-1.33  exit=STOP  hold=15.0m
- 12:50:16->13:09:13  long AFRM  rule=R7 EXPERIMENTAL  pnl=$-1.58  R=-1.11  exit=STOP  hold=20.0m
- 13:25:19->13:26:16  short OXY  rule=R7 EXPERIMENTAL  pnl=$-0.70  R=-1.27  exit=STOP  hold=1.0m
- 12:35:19->13:35:22  long UAL  rule=R7 EXPERIMENTAL  pnl=$0.50  R=0.80  exit=TIME_STOP  hold=60.0m
- 08:35:33->14:55:12  long CRWD  rule=R8  pnl=$-0.54  R=-0.08  exit=EOD_FLATTEN_1455  hold=380.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 2 | 1 | 2.84 |
| R6 | True | 2 | 1 | 0.43 |
| R7 | True | 4 | 1 | -2.48 |
| NR7 | True | 0 | 0 | 0.00 |

## Cumulative paper account

Sessions: 4  start $1000.00 -> $1000.80  total P&L $+0.80 (+0.080%)
Cumulative trades: 8  wins: 3  win rate: 38%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=2 wins=1 wr=50%  pnl=$0.43  avgR=0.5306  sessions=['2026-10-15']
- R7 EXPERIMENTAL: n=4 wins=1 wr=25%  pnl=$-2.48  avgR=-0.7279  sessions=['2026-10-15']
- R8: n=2 wins=1 wr=50%  pnl=$2.84  avgR=0.1748  sessions=['2026-10-15']
- NR7 EXPERIMENTAL: n=0 wins=0 wr=0%  pnl=$0.00  avgR=None  sessions=[]

Paper only.
