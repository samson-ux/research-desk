# PAPER day report 2026-10-28

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $-2.41 (-0.246%)  |  equity $981.91 -> $979.50
Trades: 3  wins: 1  win rate: 33%
Rules version (day): 6  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job A started at 2026-10-28 09:02:07 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job A started at 2026-10-28 09:34:16 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-28 11:30:44 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: None min gap (startup–09:02 CT) missed_windows=['R8']
- STALL: 11.1 min gap (08:51–09:02 CT) missed_windows=[]
- STALL: 18.1 min gap (09:16–09:34 CT) missed_windows=[]
- missed_entry_window: True

## Trades

- 08:35:09->08:48:11  short CAT  rule=R8  pnl=$4.11  R=0.76  exit=TARGET  hold=13.0m
- 08:35:09->09:05:17  short ARM  rule=R8  pnl=$-3.62  R=-1.04  exit=STOP  hold=31.0m
- 08:35:09->13:37:54  short AMD  rule=R8  pnl=$-2.89  R=-1.06  exit=STOP  hold=302.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 1 | -2.41 |

## Cumulative paper account

Sessions: 13  start $1000.00 -> $979.50  total P&L $-20.50 (-2.050%)
Cumulative trades: 56  wins: 22  win rate: 39%
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

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=24 wins=13 wr=54%  pnl=$-3.54  avgR=0.0139  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-26', '2026-10-27', '2026-10-28']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
