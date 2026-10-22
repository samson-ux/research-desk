# PAPER day report 2026-10-22

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $-5.16 (-0.526%)  |  equity $982.10 -> $976.93
Trades: 3  wins: 1  win rate: 33%
Rules version (day): 6  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job A started at 2026-10-22 10:18:03 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-22 11:31:10 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 4.9 min gap (08:38–08:42 CT) missed_windows=['R8']
- STALL: 78.7 min gap (supervisor–10:15 CT) missed_windows=[]
- STALL: 78.8 min gap (supervisor–10:15 CT) missed_windows=[]
- STALL: 79.3 min gap (supervisor–10:16 CT) missed_windows=[]
- STALL: 79.8 min gap (supervisor–10:16 CT) missed_windows=[]
- STALL: 80.3 min gap (supervisor–10:17 CT) missed_windows=[]
- STALL: None min gap (startup–10:18 CT) missed_windows=['R8']
- STALL: 81.2 min gap (08:56–10:18 CT) missed_windows=[]
- STALL: 50.4 min gap (10:30–11:20 CT) missed_windows=[]
- STALL: 31.6 min gap (14:01–14:33 CT) missed_windows=[]
- missed_entry_window: True

## Trades

- 08:35:09->08:37:09  long AFRM  rule=R8  pnl=$1.90  R=0.58  exit=TARGET  hold=3.0m
- 08:35:09->08:45:00  short CRWD  rule=R8  pnl=$-3.95  R=-1.05  exit=STOP  hold=9.0m
- 08:35:09->08:49:00  long NVDA  rule=R8  pnl=$-3.11  R=-1.06  exit=STOP  hold=14.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 1 | -5.16 |

## Cumulative paper account

Sessions: 9  start $1000.00 -> $976.93  total P&L $-23.07 (-2.307%)
Cumulative trades: 47  wins: 16  win rate: 34%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4
- 2026-10-16: $-4.22 (-0.421%)  trades=12 wins=4  end=$996.58  rules_v=5
- 2026-10-19: $+2.00 (+0.201%)  trades=8 wins=4  end=$998.58  rules_v=5
- 2026-10-20: $-4.13 (-0.413%)  trades=13 wins=4  end=$994.46  rules_v=5
- 2026-10-21: $-12.36 (-1.243%)  trades=3 wins=0  end=$982.10  rules_v=6
- 2026-10-22: $-5.16 (-0.526%)  trades=3 wins=1  end=$976.93  rules_v=6

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=15 wins=7 wr=47%  pnl=$-6.11  avgR=-0.1182  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
