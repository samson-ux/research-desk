# PAPER day report 2026-11-09

No broker. No orders. No real money. Prices are Yahoo chart bars only.

Interim report — this session is not finalized yet.

Day P&L: $-0.83 (-0.084%)  |  equity $982.59 -> $981.77
Trades: 3  wins: 2  win rate: 67%
Rules version (day): 6  mode: LIVE-PAPER  job: A  jobs: ['A']  halted: False
Open positions at report time: 0

## Stall / missed window (no backfill)

- STALL: 5.9 min gap (09:16–09:21 CT) missed_windows=[]
- missed_entry_window: False

## Trades

- 08:35:09->08:40:09  short SHOP  rule=R8  pnl=$1.69  R=0.43  exit=TARGET  hold=4.0m
- 08:35:09->08:40:09  short CRWD  rule=R8  pnl=$2.27  R=0.58  exit=TARGET  hold=4.0m
- 08:35:09->08:53:09  short PANW  rule=R8  pnl=$-4.79  R=-1.04  exit=STOP  hold=17.0m

## Per-rule this session

| rule | experimental | trades | wins | P&L |
|---|---|---|---|---|
| R8 | False | 3 | 2 | -0.83 |

## Cumulative paper account

Sessions: 20  start $1000.00 -> $982.59  total P&L $-17.41 (-1.741%)
Cumulative trades: 70  wins: 30  win rate: 43%
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
- 2026-11-06: $-2.11 (-0.215%)  trades=3 wins=1  end=$982.59  rules_v=6

## Per-rule cumulative (separate buckets)

- R6 EXPERIMENTAL: n=8 wins=2 wr=25%  pnl=$-2.56  avgR=-0.4665  sessions=['2026-10-15', '2026-10-19', '2026-10-20']
- R7 EXPERIMENTAL: n=13 wins=4 wr=31%  pnl=$-2.63  avgR=-0.3701  sessions=['2026-10-15', '2026-10-16']
- R8: n=38 wins=21 wr=55%  pnl=$-0.45  avgR=-0.0292  sessions=['2026-10-15', '2026-10-16', '2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-26', '2026-10-27', '2026-10-28', '2026-10-29', '2026-10-30', '2026-11-02', '2026-11-03', '2026-11-05', '2026-11-06']
- NR7 EXPERIMENTAL: n=11 wins=3 wr=27%  pnl=$-11.77  avgR=-0.3096  sessions=['2026-10-16', '2026-10-19', '2026-10-20']

Paper only.
