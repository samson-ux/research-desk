# PAPER day report 2026-10-29

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $-3.01 (-0.307%)  |  equity $979.50 -> $976.49
Trades: 3  wins: 1  win rate: 33%
Rules version (day): 6  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job A started at 2026-10-29 10:01:25 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job A started at 2026-10-29 10:41:57 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job A started at 2026-10-29 11:22:29 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-29 11:30:52 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-29 11:58:05 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-29 12:19:40 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-29 12:41:15 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-29 13:02:45 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-29 13:23:41 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-29 13:45:17 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-29 14:06:26 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 16.1 min gap (08:53–09:09 CT) missed_windows=[]
- STALL: None min gap (startup–10:01 CT) missed_windows=['R8']
- STALL: 38.3 min gap (09:23–10:01 CT) missed_windows=[]
- STALL: 3.7 min gap (10:15–10:19 CT) missed_windows=[]
- STALL: 8.8 min gap (10:33–10:41 CT) missed_windows=[]
- STALL: 3.2 min gap (10:55–10:59 CT) missed_windows=[]
- STALL: 9.3 min gap (11:13–11:22 CT) missed_windows=[]
- STALL: 11.2 min gap (11:46–11:58 CT) missed_windows=[]
- STALL: 7.6 min gap (12:12–12:19 CT) missed_windows=[]
- STALL: 7.6 min gap (12:33–12:41 CT) missed_windows=[]
- STALL: 7.5 min gap (12:55–13:02 CT) missed_windows=[]
- STALL: 6.9 min gap (13:16–13:23 CT) missed_windows=[]
- STALL: 7.6 min gap (13:37–13:45 CT) missed_windows=[]
- STALL: 7.2 min gap (13:59–14:06 CT) missed_windows=[]
- missed_entry_window: True

## Trades

- 08:35:10->08:36:09  long AFRM  rule=R8  pnl=$1.21  R=0.17  exit=TARGET  hold=2.0m
- 08:35:10->08:36:09  short CCL  rule=R8  pnl=$-1.48  R=-1.11  exit=STOP  hold=1.0m
- 08:35:10->14:55:35  long AMD  rule=R8  pnl=$-2.73  R=-0.44  exit=EOD_FLATTEN_1455  hold=380.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 1 | -3.01 |

## Cumulative paper account

Sessions: 14  start $1000.00 -> $976.49  total P&L $-23.51 (-2.351%)
Cumulative trades: 59  wins: 23  win rate: 39%
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
- 2026-10-28: $-2.41 (-0.245%)  trades=3 wins=1  end=$979.50  rules_v=6
- 2026-10-29: $-3.01 (-0.307%)  trades=3 wins=1  end=$976.49  rules_v=6

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=27 wins=14 wr=52%  pnl=$-6.55  avgR=-0.039  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
