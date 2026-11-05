# PAPER day report 2026-11-05

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $+1.88 (+0.191%)  |  equity $982.83 -> $984.71
Trades: 3  wins: 2  win rate: 67%
Rules version (day): 6  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job B started at 2026-11-05 11:34:50 CST, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 3.9 min gap (08:31–08:34 CT) missed_windows=[]
- STALL: 16.9 min gap (08:48–09:05 CT) missed_windows=[]
- STALL: 35.4 min gap (09:19–09:55 CT) missed_windows=[]
- STALL: 27.0 min gap (10:18–10:45 CT) missed_windows=[]
- STALL: 10.7 min gap (10:59–11:09 CT) missed_windows=[]
- STALL: 9.9 min gap (11:24–11:34 CT) missed_windows=[]
- STALL: 20.1 min gap (12:03–12:23 CT) missed_windows=[]
- STALL: 25.2 min gap (12:38–13:04 CT) missed_windows=[]
- STALL: 30.9 min gap (13:18–13:49 CT) missed_windows=[]
- STALL: 15.6 min gap (14:04–14:19 CT) missed_windows=[]
- STALL: 15.9 min gap (14:33–14:49 CT) missed_windows=[]
- missed_entry_window: False

## Trades

- 08:35:03->08:37:04  short UBER  rule=R8  pnl=$0.42  R=0.07  exit=TARGET  hold=2.0m
- 08:35:03->08:45:03  short OXY  rule=R8  pnl=$-2.71  R=-1.07  exit=STOP  hold=10.0m
- 08:35:03->08:47:03  short AMZN  rule=R8  pnl=$4.17  R=1.03  exit=TARGET  hold=12.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 2 | 1.88 |

## Cumulative paper account

Sessions: 19  start $1000.00 -> $984.71  total P&L $-15.29 (-1.529%)
Cumulative trades: 67  wins: 29  win rate: 43%
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
- 2026-10-30: $-2.20 (-0.226%)  trades=1 wins=0  end=$974.29  rules_v=6
- 2026-11-02: $+6.90 (+0.708%)  trades=3 wins=3  end=$981.19  rules_v=6
- 2026-11-03: $+1.65 (+0.168%)  trades=1 wins=1  end=$982.83  rules_v=6
- 2026-11-04: $+0.00 (+0.000%)  trades=0 wins=0  end=$982.83  rules_v=6
- 2026-11-05: $+1.88 (+0.191%)  trades=3 wins=2  end=$984.71  rules_v=6

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=35 wins=20 wr=57%  pnl=$1.67  avgR=-0.015  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30', '2026-11-02', '2026-11-03', '2026-11-05']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
