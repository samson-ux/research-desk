# PAPER day report 2026-10-16

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $-4.22 (-0.421%)  |  equity $1000.80 -> $996.58
Trades: 12  wins: 4  win rate: 33%
Rules version (day): 5  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job B started at 2026-10-16 11:30:17 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Trades

- 08:36:06->08:36:06  short CRWD  rule=NR7 EXPERIMENTAL  pnl=$-4.24  R=-1.04  exit=STOP  hold=0.0m
- 08:35:06->09:53:06  short TSLA  rule=R8  pnl=$3.55  R=0.78  exit=TARGET  hold=78.0m
- 10:20:06->10:22:07  short NVDA  rule=R7 EXPERIMENTAL  pnl=$-0.70  R=-1.33  exit=STOP  hold=2.0m
- 09:12:06->10:36:06  long UAL  rule=NR7 EXPERIMENTAL  pnl=$-3.38  R=-1.05  exit=STOP  hold=83.0m
- 10:35:06->10:36:06  short CRWD  rule=R7 EXPERIMENTAL  pnl=$-0.74  R=-1.26  exit=STOP  hold=1.0m
- 10:30:06->10:37:06  short MSFT  rule=R7 EXPERIMENTAL  pnl=$-0.70  R=-1.33  exit=STOP  hold=7.0m
- 10:55:07->11:03:06  short MSTR  rule=R7 EXPERIMENTAL  pnl=$3.06  R=1.89  exit=TARGET  hold=8.0m
- 11:00:07->11:03:06  short SHOP  rule=R7 EXPERIMENTAL  pnl=$1.34  R=1.80  exit=TARGET  hold=4.0m
- 10:55:07->11:08:06  short PANW  rule=R7 EXPERIMENTAL  pnl=$-0.97  R=-1.22  exit=STOP  hold=12.0m
- 11:50:24->12:04:24  short UAL  rule=R7 EXPERIMENTAL  pnl=$1.63  R=1.81  exit=TARGET  hold=14.0m
- 12:20:24->12:29:24  short AMD  rule=R7 EXPERIMENTAL  pnl=$-1.44  R=-1.14  exit=STOP  hold=9.0m
- 12:05:24->12:31:24  short TSLA  rule=R7 EXPERIMENTAL  pnl=$-1.64  R=-1.12  exit=STOP  hold=26.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 1 | 1 | 3.55 |
| R6 | True | 0 | 0 | 0.00 |
| R7 | True | 9 | 3 | -0.15 |
| NR7 | True | 2 | 0 | -7.62 |

## Cumulative paper account

Sessions: 5  start $1000.00 -> $996.58  total P&L $-3.42 (-0.342%)
Cumulative trades: 20  wins: 7  win rate: 35%
- 2026-10-08: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-09: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=3
- 2026-10-12: $+0.00 (+0.000%)  trades=0 wins=0  end=$1000.00  rules_v=4
- 2026-10-15: $+0.80 (+0.080%)  trades=8 wins=3  end=$1000.80  rules_v=4
- 2026-10-16: $-4.22 (-0.421%)  trades=12 wins=4  end=$996.58  rules_v=5

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=2 wins=1 wr=50%  pnl=$0.43  avgR=0.5306  sessions=['2026-10-15']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=3 wins=2 wr=67%  pnl=$6.40  avgR=0.377  sessions=['2026-10-15', '2026-10-16']
- NR7 EXPERIMENTAL: n=2 wins=0 wr=0%  pnl=$-7.62  avgR=-1.0488  sessions=['2026-10-16']

Paper only.
