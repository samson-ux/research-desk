# PAPER day report 2026-11-03

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $+1.65 (+0.168%)  |  equity $981.19 -> $982.83
Trades: 1  wins: 1  win rate: 100%
Rules version (day): 6  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job B started at 2026-11-03 11:30:53 CST, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 14.7 min gap (08:49–09:03 CT) missed_windows=[]
- STALL: 12.4 min gap (09:17–09:30 CT) missed_windows=[]
- STALL: 17.3 min gap (09:45–10:02 CT) missed_windows=[]
- STALL: 11.7 min gap (10:16–10:28 CT) missed_windows=[]
- STALL: 16.7 min gap (10:42–10:58 CT) missed_windows=[]
- STALL: 6.7 min gap (11:13–11:20 CT) missed_windows=[]
- STALL: 15.8 min gap (11:47–12:03 CT) missed_windows=[]
- STALL: 16.9 min gap (12:17–12:34 CT) missed_windows=[]
- STALL: 16.2 min gap (12:49–13:05 CT) missed_windows=[]
- STALL: 16.8 min gap (13:19–13:36 CT) missed_windows=[]
- STALL: 16.7 min gap (13:50–14:07 CT) missed_windows=[]
- STALL: 14.8 min gap (14:22–14:37 CT) missed_windows=[]
- missed_entry_window: False

## Trades

- 08:35:09->09:30:24  long OXY  rule=R8  pnl=$1.65  R=0.37  exit=TARGET  hold=45.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 1 | 1 | 1.65 |

## Cumulative paper account

Sessions: 17  start $1000.00 -> $982.83  total P&L $-17.17 (-1.717%)
Cumulative trades: 64  wins: 27  win rate: 42%
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

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=32 wins=18 wr=56%  pnl=$-0.21  avgR=-0.0173  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30', '2026-11-02', '2026-11-03']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
