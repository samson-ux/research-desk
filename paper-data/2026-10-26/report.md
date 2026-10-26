# PAPER day report 2026-10-26

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Day P&L: $-0.78 (-0.080%)  |  equity $976.93 -> $976.15
Trades: 3  wins: 2  win rate: 67%
Rules version (day): 6  mode: LIVE-PAPER  job: B  jobs: ['A', 'B']  halted: False
Open positions at report time: 0

## Startup

- STARTUP: Job A started at 2026-10-26 08:22:01 CDT, after its entry window opened at 08:20 CT. No backfill of missed entry windows.
- STARTUP: Job B started at 2026-10-26 11:32:14 CDT, after its entry window opened at 11:25 CT. No backfill of missed entry windows.

## Stall / missed window (no backfill)

- STALL: 3.4 min gap (08:35–08:38 CT) missed_windows=['R8']
- STALL: 4.5 min gap (08:52–08:56 CT) missed_windows=[]
- STALL: 16.6 min gap (09:10–09:27 CT) missed_windows=[]
- STALL: 18.2 min gap (09:41–09:59 CT) missed_windows=[]
- missed_entry_window: True

## Trades

- 08:35:10->08:50:32  long OXY  rule=R8  pnl=$2.02  R=0.65  exit=TARGET  hold=15.0m
- 08:35:10->09:07:03  short INTC  rule=R8  pnl=$2.39  R=0.95  exit=TARGET  hold=31.0m
- 08:35:10->10:00:02  short VRT  rule=R8  pnl=$-5.19  R=-1.03  exit=STOP  hold=82.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 2 | -0.78 |

## Cumulative paper account

Sessions: 11  start $1000.00 -> $976.15  total P&L $-23.85 (-2.385%)
Cumulative trades: 50  wins: 18  win rate: 36%
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

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=18 wins=9 wr=50%  pnl=$-6.89  avgR=-0.0672  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-26']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.

## Session notes

Live VM session. Yahoo bars only. No broker orders.

- Job A process started 08:21 CT. Premarket finished before the R8 window. The engine's own startup stamp is 08:22:01 CT, one minute after the 08:20 trade start. R8 (08:35–08:40) had not opened yet.
- 08:35:10 CT: R8 evaluated all 20 watchlist names and entered long OXY, short INTC, short VRT. DELL was skipped because cash was $0.01. R6 and NR7 stayed disabled.
- STALL 08:35–08:38 CT (3.4 min) overlapped the still-open R8 window. Entries were already on the book from 08:35:10 and seen5 was set for every name, so nothing was backfilled.
- STALL 08:52–08:56 CT (4.5 min). No entry window open. OXY had already exited at target at 08:50:32.
- STALL 09:10–09:27 CT (16.6 min). No entry window open. Process resumed on its own and kept managing the open shorts.
- STALL 09:41–09:59 CT (18.2 min). No entry window open. On the 10:00:02 CT loop the engine filled the VRT stop from the 09:56 CT bar that traded through 199.33. Fill was the stop, not an invented price.
- After 10:00 the book was flat. Job A ran through 11:30 CT with no further stalls. Job B resumed that state at 11:31 CT (engine startup stamp 11:32:14 CT, after the 11:25 trade start because Job A holds the book until 11:30) and ran through 15:00 CT. Positions were already flat at the 14:55 CT flatten. No new stalls in the afternoon.
- Carried rules were left as-is: R8 enabled, risk_mult 1.25; R6 and NR7 stayed off. Finalize wrote no rule changes.
