# PAPER day report 2026-10-27

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $+5.76 (+0.590%)  |  equity $976.15 -> $981.91
Trades: 3  wins: 3  win rate: 100%
Rules version (day): 6  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job A started at 2026-10-27 08:22:52 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job A started at 2026-10-27 09:33:02 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job A started at 2026-10-27 10:21:40 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job A started at 2026-10-27 11:03:34 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job A started at 2026-10-27 11:29:02 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-27 11:32:59 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-27 12:09:58 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-27 12:52:14 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-27 13:33:30 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-27 14:14:50 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-27 14:44:32 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: None min gap (startup–09:33 CT) missed_windows=['R8']
- STALL: 27.2 min gap (09:05–09:33 CT) missed_windows=[]
- STALL: 33.1 min gap (09:47–10:20 CT) missed_windows=[]
- STALL: 3.5 min gap (10:34–10:38 CT) missed_windows=[]
- STALL: 24.6 min gap (10:38–11:02 CT) missed_windows=[]
- STALL: 12.5 min gap (11:16–11:29 CT) missed_windows=[]
- STALL: 3.9 min gap (11:29–11:32 CT) missed_windows=[]
- STALL: 25.2 min gap (11:43–12:09 CT) missed_windows=[]
- STALL: 27.4 min gap (12:23–12:51 CT) missed_windows=[]
- STALL: 27.5 min gap (13:05–13:32 CT) missed_windows=[]
- STALL: 28.3 min gap (13:46–14:14 CT) missed_windows=[]
- STALL: 15.7 min gap (14:28–14:44 CT) missed_windows=[]
- missed_entry_window: True

## Trades

- 08:35:02->08:36:02  short AAL  rule=R8  pnl=$0.90  R=0.21  exit=TARGET  hold=1.0m
- 08:35:02->08:37:02  short UAL  rule=R8  pnl=$2.04  R=0.43  exit=TARGET  hold=2.0m
- 08:35:02->08:55:02  short NVDA  rule=R8  pnl=$2.82  R=2.24  exit=TARGET  hold=20.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 3 | 5.76 |

## Cumulative paper account

Sessions: 12  start $1000.00 -> $981.91  total P&L $-18.09 (-1.809%)
Cumulative trades: 53  wins: 21  win rate: 40%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4
- 2026-10-16: $-4.22 (-0.421%)  trades=12 wins=4  end=$996.58  rules_v=5
- 2026-10-19: $+2.00 (+0.201%)  trades=8 wins=4  end=$998.58  rules_v=5
- 2026-10-20: $-4.13 (-0.413%)  trades=13 wins=4  end=$994.46  rules_v=5
- 2026-10-21: $-12.36 (-1.243%)  trades=3 wins=0  end=$982.10  rules_v=6
- 2026-10-22: $-5.16 (-0.526%)  trades=3 wins=1  end=$976.93  rules_v=6
- 2026-10-23: $+0.00 (+0.000%)  trades=0 wins=0  end=$976.93  rules_v=6
- 2026-10-26: $-0.78 (-0.080%)  trades=3 wins=2  end=$976.15  rules_v=6
- 2026-10-27: $+5.76 (+0.590%)  trades=3 wins=3  end=$981.91  rules_v=6

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=21 wins=12 wr=57%  pnl=$-1.13  avgR=0.0798  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-26', '2026-10-27']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
