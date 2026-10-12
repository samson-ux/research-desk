#!/usr/bin/env python3
"""Premarket watchlist refresh (v2 procedure) -> writes rules.json from rules_v3.json. Real Yahoo data only, paper only.
Keeps the 12 backtested core names; adds up to 8 liquid names (px>$10, 20d avg vol>2M) ranked by |premarket gap|
(prefer 0.8-3.5%, the gap-fade band), prior-day RVOL and daily flags. Total 15-20."""
import json, time, sys
from datetime import datetime
from zoneinfo import ZoneInfo
from yfdata import chart
ET = ZoneInfo("America/New_York"); CT = ZoneInfo("America/Chicago")
SECT = {"XLK":"AAPL MSFT ORCL CRM ADBE PLTR SNOW CRWD PANW SHOP DELL ANET".split(),"SMH":"NVDA AMD AVGO INTC MU QCOM TXN AMAT LRCX ARM SMCI MRVL".split(),
 "XLF":"JPM BAC C WFC GS MS SCHW COIN HOOD SOFI PYPL AFRM".split(),"XLE":"XOM CVX OXY SLB COP HAL DVN".split(),
 "XLV":"UNH LLY JNJ PFE MRK ABBV CVS AMGN GILD".split(),"XLY":"AMZN TSLA HD LOW NKE SBUX MCD TGT ABNB UBER RIVN F GM CCL DKNG RBLX".split(),
 "XLI":"BA CAT GE DE UPS FDX RTX LMT DAL UAL AAL VRT".split(),"QQQ":"META GOOGL NFLX MSTR MARA RIOT".split()}
SEC = {t: e for e, ts in SECT.items() for t in ts}
r = json.load(open("rules_v3.json")); core = [w["ticker"] for w in r["watchlist"]]
today = datetime.now(ET).date(); rows = []
for s in SEC:
    try:
        b = [x for x in chart(s, "1d", "3mo")["bars"] if datetime.fromtimestamp(x["t"], ET).date() < today]
        y, p = b[-1], b[-2]; av20 = sum(x["v"] for x in b[-21:-1]) / 20
        if y["c"] < 10 or av20 < 2e6: continue
        flags = []
        if y["h"] < p["h"] and y["l"] > p["l"]: flags.append("inside_day")
        if y["h"]-y["l"] <= min(x["h"]-x["l"] for x in b[-7:]): flags.append("NR7")
        pm = [x for x in chart(s, "1m", "1d", prepost=True)["bars"] if datetime.fromtimestamp(x["t"], ET).date() == today]
        gap = (pm[-1]["c"] / y["c"] - 1) * 100 if pm else None
        rows.append(dict(s=s, sec=SEC[s], prev_close=y["c"], rvol=y["v"]/av20, gap=gap, pm_prints=len(pm), flags=flags))
    except Exception as e:
        print("skip", s, e, file=sys.stderr)
    time.sleep(0.25)
def score(x):
    g = abs(x["gap"] or 0); band = 2.0 if 0.8 <= g <= 3.5 else 0.0
    return band + min(g, 3.5) / 3.5 + min(x["rvol"], 3) / 3 + 0.25 * len(x["flags"])
extra = [x for x in sorted(rows, key=score, reverse=True) if x["s"] not in core and x["pm_prints"] > 0]
seen_sec = {}; add = []
for x in extra:                       # one name per theme where possible
    if seen_sec.get(x["sec"], 0) >= 2: continue
    seen_sec[x["sec"]] = seen_sec.get(x["sec"], 0) + 1; add.append(x)
    if len(core) + len(add) >= 20: break
R = {x["s"]: x for x in rows}
wl = [dict(ticker=t, sector=next(w["sector"] for w in r["watchlist"] if w["ticker"] == t), bias="both",
           daily_flags=R.get(t, {}).get("flags", []), pm_gap_pct=round(R[t]["gap"], 2) if t in R and R[t]["gap"] is not None else None, core=True) for t in core]
wl += [dict(ticker=x["s"], sector=x["sec"] if x["sec"] != "XLV" else "SPY", bias="both", daily_flags=x["flags"],
            pm_gap_pct=round(x["gap"], 2) if x["gap"] is not None else None, core=False) for x in add]
r["watchlist"] = wl; r["watchlist_refreshed_ct"] = datetime.now(CT).isoformat(timespec="seconds")
r["session_date"] = str(today)
json.dump(r, open("rules.json.tmp", "w"), indent=2)
import os; os.replace("rules.json.tmp", "rules.json")
json.dump(rows, open("premarket_screen.json", "w"), indent=1)
print(f"watchlist {len(wl)}:", [(w["ticker"], w["pm_gap_pct"]) for w in wl])
