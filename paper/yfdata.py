"""Yahoo Finance chart API helper (no key). Real data only."""
import time, random, requests, logging
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HOSTS = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]
_s = requests.Session(); _s.headers.update({"User-Agent": UA, "Accept": "application/json"})
log = logging.getLogger("yf")

def chart(sym, interval="1m", rng="1d", prepost=False, period1=None, period2=None, retries=4):
    params = {"interval": interval, "includePrePost": "true" if prepost else "false"}
    if period1: params.update(period1=int(period1), period2=int(period2))
    else: params["range"] = rng
    delay = 1.0
    last = None
    for i in range(retries):
        host = HOSTS[i % 2]
        try:
            r = _s.get(f"{host}/v8/finance/chart/{sym}", params=params, timeout=10)
            if r.status_code == 429 or r.status_code >= 500:
                last = f"HTTP {r.status_code}"; time.sleep(delay + random.random()); delay *= 2; continue
            r.raise_for_status()
            res = r.json()["chart"]["result"][0]
            ts = res.get("timestamp") or []
            q = res["indicators"]["quote"][0]
            bars = []
            for j, t in enumerate(ts):
                o, h, l, c, v = (q[k][j] for k in ("open", "high", "low", "close", "volume"))
                if None in (o, h, l, c): continue
                bars.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": v or 0})
            return {"meta": res["meta"], "bars": bars}
        except Exception as e:
            last = repr(e); time.sleep(delay); delay *= 2
    raise RuntimeError(f"fetch {sym} {interval} failed: {last}")
