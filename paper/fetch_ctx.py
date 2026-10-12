"""Pre-open context: daily stats (ATR14, prior H/L/C, flags) + 14-day avg first-5m volume for each symbol. Writes context.json."""
import json, time, sys
from datetime import datetime, date
from zoneinfo import ZoneInfo
from yfdata import chart
ET = ZoneInfo("America/New_York")

def daily_flags(b):
    """Prior-session pattern flags from completed daily bars (last bar is the prior session)."""
    flags = []
    if len(b) < 2:
        return flags
    y, p = b[-1], b[-2]
    if y["h"] < p["h"] and y["l"] > p["l"]:
        flags.append("inside_day")
    if len(b) >= 7:
        rng = lambda x: x["h"] - x["l"]
        if rng(y) <= min(rng(x) for x in b[-7:]):
            flags.append("NR7")
    if len(b) >= 20 and y["c"] >= max(x["c"] for x in b[-20:]):
        flags.append("20d_high_close")
    if len(b) >= 20 and y["c"] <= min(x["c"] for x in b[-20:]):
        flags.append("20d_low_close")
    return flags


def daily_ctx(sym, session_date):
    d = chart(sym, "1d", "6mo")
    b = [x for x in d["bars"] if datetime.fromtimestamp(x["t"], ET).date() < session_date]
    tr = [max(b[i]['h']-b[i]['l'], abs(b[i]['h']-b[i-1]['c']), abs(b[i]['l']-b[i-1]['c'])) for i in range(1, len(b))]
    y = b[-1]
    avg_vol20 = sum(x["v"] for x in b[-20:]) / 20
    return {"atr14": sum(tr[-14:])/14, "prev_close": y["c"], "prev_high": y["h"], "prev_low": y["l"],
            "prev_date": str(datetime.fromtimestamp(y["t"], ET).date()),
            "avg_vol20": avg_vol20,
            "daily_rvol": (y["v"] / avg_vol20) if avg_vol20 else 0.0,
            "flags": daily_flags(b)}

def slot_vols(sym, session_date):
    """Average 5-min volume per time-of-day slot (ET HH:MM) over the prior 14 sessions (time-of-day RVOL baseline)."""
    d = chart(sym, "5m", "1mo")
    by = {}
    for x in d["bars"]:
        dt = datetime.fromtimestamp(x["t"], ET)
        if dt.date() < session_date:
            by.setdefault(dt.date(), {})[dt.strftime("%H:%M")] = x["v"]
    days = sorted(by)[-14:]
    slots = {}
    for dd in days:
        for k, v in by[dd].items():
            if v: slots.setdefault(k, []).append(v)
    return {k: sum(v)/len(v) for k, v in slots.items() if len(v) >= 5}

def build(symbols, session_date, out="context.json"):
    ctx = {}
    for s in symbols:
        try:
            c = daily_ctx(s, session_date); time.sleep(0.3)
            c["slot_vol14"] = slot_vols(s, session_date); time.sleep(0.3)
            c["avg_open5_vol14"] = c["slot_vol14"].get("09:30")
            ctx[s] = c
        except Exception as e:
            print("ctx err", s, e, file=sys.stderr)
    json.dump({"session_date": str(session_date), "built": datetime.now(ET).isoformat(), "symbols": ctx}, open(out, "w"), indent=1)
    return ctx

if __name__ == "__main__":
    sd = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(ET).date()
    out = sys.argv[2] if len(sys.argv) > 2 else "context.json"
    rules = json.load(open("rules.json"))
    syms = [w["ticker"] for w in rules["watchlist"]] + rules["context_etfs"]
    build(sorted(set(syms)), sd, out)
    print("ok", out)
