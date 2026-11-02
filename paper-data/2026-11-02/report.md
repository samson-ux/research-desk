# PAPER day report 2026-11-02

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $+6.90 (+0.708%)  |  equity $974.29 -> $981.19
Trades: 3  wins: 3  win rate: 100%
Rules version (day): 6  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job B started at 2026-11-02 11:30:27 CST, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 10.6 min gap (08:59–09:09 CT) missed_windows=[]
- STALL: 6.5 min gap (09:23–09:30 CT) missed_windows=[]
- STALL: 39.9 min gap (09:45–10:25 CT) missed_windows=[]
- STALL: 36.0 min gap (10:48–11:24 CT) missed_windows=[]
- STALL: 28.0 min gap (11:44–12:12 CT) missed_windows=[]
- STALL: 33.7 min gap (12:27–13:01 CT) missed_windows=[]
- STALL: 46.1 min gap (13:27–14:13 CT) missed_windows=[]
- STALL: 4.0 min gap (14:44–14:49 CT) missed_windows=[]
- missed_entry_window: False

## Trades

- 08:35:09->08:36:10  short CAT  rule=R8  pnl=$0.07  R=0.01  exit=TARGET  hold=1.0m
- 08:35:09->08:39:09  short AMD  rule=R8  pnl=$2.28  R=0.57  exit=TARGET  hold=3.0m
- 08:35:09->09:17:44  long COIN  rule=R8  pnl=$4.55  R=0.63  exit=TARGET  hold=36.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 3 | 6.90 |

## Cumulative paper account

Sessions: 16  start $1000.00 -> $981.19  total P&L $-18.81 (-1.881%)
Cumulative trades: 63  wins: 26  win rate: 41%
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

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=31 wins=17 wr=55%  pnl=$-1.85  avgR=-0.0297  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30', '2026-11-02']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
