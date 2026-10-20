# PAPER day report 2026-10-20

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $-4.13 (-0.413%)  |  equity $998.58 -> $994.46
Trades: 13  wins: 4  win rate: 31%
Rules version (day): 5  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job B started at 2026-10-20 11:30:35 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 6.0 min gap (08:37–08:42 CT) missed_windows=['R8', 'NR7']
- STALL: 6.4 min gap (08:56–09:03 CT) missed_windows=['R6', 'NR7']
- STALL: 7.7 min gap (09:44–09:52 CT) missed_windows=['R6', 'NR7']
- missed_entry_window: True

## Trades

- 08:35:09->08:43:18  long AMD  rule=R8  pnl=$-2.95  R=-1.06  exit=STOP  hold=7.0m
- 08:35:09->08:43:18  long MSTR  rule=R8  pnl=$4.54  R=1.60  exit=TARGET  hold=4.0m
- 08:35:09->08:43:18  short OXY  rule=R8  pnl=$2.35  R=1.10  exit=TARGET  hold=5.0m
- 08:44:07->08:47:07  long RTX  rule=NR7 EXPERIMENTAL  pnl=$3.12  R=1.89  exit=TARGET  hold=3.0m
- 08:48:08->08:50:07  long CVX  rule=NR7 EXPERIMENTAL  pnl=$-1.89  R=-1.10  exit=STOP  hold=2.0m
- 08:46:07->08:51:08  short SNOW  rule=NR7 EXPERIMENTAL  pnl=$-4.42  R=-1.08  exit=STOP  hold=5.0m
- 08:43:18->09:10:29  short MSFT  rule=NR7 EXPERIMENTAL  pnl=$-2.07  R=-1.09  exit=STOP  hold=28.0m
- 09:12:29->09:42:41  long MSTR  rule=NR7 EXPERIMENTAL  pnl=$11.72  R=1.97  exit=TARGET  hold=30.0m
- 09:42:41->10:13:21  long RIOT  rule=NR7 EXPERIMENTAL  pnl=$-8.35  R=-1.02  exit=STOP  hold=31.0m
- 10:20:20->10:21:20  long NVDA  rule=R6 EXPERIMENTAL  pnl=$-0.60  R=-1.33  exit=STOP  hold=1.0m
- 10:15:21->10:25:20  short UAL  rule=R6 EXPERIMENTAL  pnl=$-0.97  R=-1.22  exit=STOP  hold=10.0m
- 11:35:45->11:38:45  long PANW  rule=R6 EXPERIMENTAL  pnl=$-0.70  R=-1.33  exit=STOP  hold=3.0m
- 09:24:29->14:38:45  long SHOP  rule=NR7 EXPERIMENTAL  pnl=$-3.91  R=-1.05  exit=STOP  hold=314.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 2 | 3.95 |
| R6 | True | 3 | 0 | -2.27 |
| NR7 | True | 7 | 2 | -5.81 |

## Cumulative paper account

Sessions: 7  start $1000.00 -> $994.46  total P&L $-5.54 (-0.554%)
Cumulative trades: 41  wins: 15  win rate: 37%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4
- 2026-10-16: $-4.22 (-0.421%)  trades=12 wins=4  end=$996.58  rules_v=5
- 2026-10-19: $+2.00 (+0.201%)  trades=8 wins=4  end=$998.58  rules_v=5
- 2026-10-20: $-4.13 (-0.413%)  trades=13 wins=4  end=$994.46  rules_v=5

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=9 wins=6 wr=67%  pnl=$11.41  avgR=0.2776  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
