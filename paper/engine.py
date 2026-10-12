#!/usr/bin/env python3
"""
PAPER-ONLY intraday US-equities trading simulator. No broker, no orders, no accounts.
Every simulated fill uses a real Yahoo Finance 1-minute bar (close, or the stop/target level
only when that real bar actually traded through it). Slippage is applied on top (rules.json).

PAPER ONLY. No broker, no orders. Every fill is a real Yahoo 1-minute bar
(close, or a stop/target/breakout level only when that bar traded through it).

Job A trades 08:20–11:30 CT and leaves positions open.
Job B resumes that state, trades until 15:00 CT, and flattens at 14:55.

Active rules: R8 gap fade (08:35–08:40). EXPERIMENTAL (negative out-of-sample):
NR7 inside/NR7 breakout, R6 VWAP reclaim, R7 RVOL spike. Stats stay per rule.
No rule is tweaked before 8 closed trades.

Stall guard: a loop gap over 3 minutes logs WARNING and records state['stalls'].
Missed entry windows are never backfilled.
"""
import argparse, csv, json, logging, math, os, shutil, sys, time, traceback
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from yfdata import chart
import fetch_ctx
from session_guard import JOBS, combine_ct, late_start_warning, missed_windows_for_job

CT = ZoneInfo("America/Chicago"); ET = ZoneInfo("America/New_York")
TRADE_COLS = ["time_ct", "mode", "action", "ticker", "side", "price", "shares", "size_usd", "rule_id", "reason",
              "pnl_usd", "pnl_pct", "exit_reason", "entry_time_ct", "entry_price", "stop", "target", "r_multiple",
              "hold_min", "data_bar_ct", "bar_close_raw", "slippage_bps"]
CHANGE_COLS = ["time_ct", "rule_id", "param", "old_value", "new_value", "why"]


def hm(s):
    h, m = s.split(":"); return int(h), int(m)


def ct_of(ts):
    return datetime.fromtimestamp(ts, CT)


def ema(vals, n):
    if not vals: return []
    k = 2 / (n + 1); out = [vals[0]]
    for v in vals[1:]: out.append(v * k + out[-1] * (1 - k))
    return out


class Engine:
    def __init__(self, mode, session_date, outdir, job="A"):
        self.mode = mode  # "LIVE-PAPER" or "REPLAY"
        self.job = job
        self.sd = session_date
        self.out = outdir
        os.makedirs(outdir, exist_ok=True)
        self.p = {k: os.path.join(outdir, v) for k, v in dict(
            trades="trades.csv", state="state.json", journal="journal.xlsx", log="engine.log", changes="changes.csv",
            review="hourly_review.md", rules="rules.json", ctx="context.json").items()}
        if not os.path.exists(self.p["rules"]):
            shutil.copy(os.path.join(BASE, "rules.json"), self.p["rules"])
        self.log = logging.getLogger(f"paper.{mode}.{job}.{os.getpid()}.{id(self)}")
        self.log.setLevel(logging.INFO)
        self.log.propagate = False
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh = logging.FileHandler(self.p["log"]); fh.setFormatter(fmt); self.log.addHandler(fh)
        sh = logging.StreamHandler(sys.stdout); sh.setFormatter(fmt); self.log.addHandler(sh)
        if mode == "REPLAY":
            self.log.info("=== REPLAY — Yahoo bars, paper only, not a live session ===")
        self.rules = self.load_rules(first=True)
        for path, cols in ((self.p["trades"], TRADE_COLS), (self.p["changes"], CHANGE_COLS)):
            if not os.path.exists(path):
                with open(path, "w", newline="") as f: csv.writer(f).writerow(cols)
        if not os.path.exists(self.p["review"]):
            with open(self.p["review"], "w") as f:
                f.write(f"# Hourly reviews — {self.sd} ({'TEST REPLAY' if mode=='TEST-REPLAY' else 'LIVE PAPER'})\n\n"
                        "Automatic reviews at the times in rules.json `global.review_times_ct`; thresholds in rules.md / rules.json `review`.\n\n")
        g = self.rules["global"]
        self.state = {"session_date": str(self.sd), "mode": mode, "cash": g["budget_usd"], "equity": g["budget_usd"],
                      "realized_pnl": 0.0, "positions": {}, "closed": [], "entries": {}, "last_stop_ts": {},
                      "halted": False, "risk_scale": 1.0, "reviews_done": [], "no_trigger_reviews": {},
                      "hourly": [], "last_prices": {}, "errors": 0, "loops": 0, "started": datetime.now(CT).isoformat(),
                      "stalls": [], "missed_entry_window": False, "last_loop_ct": None,
                      "startup_warnings": [], "job": job, "jobs_seen": [], "yahoo_blocked": False,
                      "paper_only": True}
        self.pending = []   # confirmation setups (R2/R3)
        self.bars = {}      # sym -> list of bars (completed only)
        self.seen5 = {}     # (sym, rule) -> last evaluated bar/bucket
        self.last_journal = 0
        self.ctx = {}
        if os.path.exists(self.p["state"]):
            try:
                old = json.load(open(self.p["state"]))
                if old.get("session_date") == str(self.sd):
                    self.state.update(old)
                    self._restore_runtime()
                    self.log.info(f"Resumed state from state.json for job {job}")
            except Exception as e:
                self.log.error(f"could not resume state: {e}")
        if self.job not in (self.state.get("jobs_seen") or []):
            self.state.setdefault("jobs_seen", []).append(self.job)

    def _restore_runtime(self):
        self.pending = list(self.state.get("pending_setups") or [])
        self.seen5 = {}
        for key, ts in (self.state.get("seen5") or {}).items():
            if not isinstance(key, str) or "|" not in key:
                continue
            sym, rid = key.split("|", 1)
            self.seen5[(sym, rid)] = ts
        seen = list(self.state.get("jobs_seen") or [])
        if not seen or seen[-1] != self.job:
            seen.append(self.job)
        self.state["jobs_seen"] = seen
        self.state["job"] = self.job

    # ---------- config ----------
    def load_rules(self, first=False):
        try:
            r = json.load(open(self.p["rules"]))
            assert r.get("paper_only") is True
            self.rules = r
            return r
        except Exception as e:
            self.log.error(f"rules.json load failed ({e}); keeping previous rules")
            if first: raise
            return self.rules

    def symbols(self):
        return [w["ticker"] for w in self.rules["watchlist"]], self.rules["context_etfs"]

    def build_ctx(self):
        tick, etfs = self.symbols()
        fetch_ctx.build(sorted(set(tick + etfs)), self.sd, self.p["ctx"])
        self.ctx = json.load(open(self.p["ctx"]))["symbols"]
        self.log.info(f"context built for {len(self.ctx)} symbols")

    # ---------- data ----------
    def fetch_live(self, now_ts):
        tick, etfs = self.symbols()
        for s in tick + etfs:
            try:
                d = chart(s, "1m", "2d")
                self.bars[s] = [b for b in d["bars"] if b["t"] + 60 <= now_ts]
            except Exception as e:
                self.state["errors"] += 1
                self._note_yahoo(s, e)
                self.log.warning(f"fetch error {s}: {e} (keeping previous bars)")
            time.sleep(0.25)

    def _note_yahoo(self, sym, err):
        msg = str(err).lower()
        if any(tok in msg for tok in ("429", "401", "403", "forbidden", "blocked", "too many")):
            self.state["yahoo_blocked"] = True
            self.log.warning(f"YAHOO_BLOCKED {sym}: {err}")

    def load_replay(self):
        cache = os.path.join(self.out, "bars_cache.json")
        tick, etfs = self.symbols()
        if os.path.exists(cache):
            cached = json.load(open(cache))
            if cached.get("session_date") == str(self.sd) and cached.get("bars"):
                self.replay_all = cached["bars"]
                self.log.info(f"reused bars_cache.json ({len(self.replay_all)} symbols)")
                return
        self.replay_all = {}
        start = datetime.combine(self.sd - timedelta(days=4), datetime.min.time(), ET)
        end = datetime.combine(self.sd + timedelta(days=1), datetime.min.time(), ET)
        for s in tick + etfs:
            try:
                d = chart(s, "1m", period1=start.timestamp(), period2=end.timestamp())
                self.replay_all[s] = [b for b in d["bars"] if datetime.fromtimestamp(b["t"], ET).date() <= self.sd]
            except Exception as e:
                self.state["errors"] += 1
                self._note_yahoo(s, e)
                self.log.warning(f"replay fetch error {s}: {e}")
            time.sleep(0.3)
        tmp = cache + ".tmp"
        json.dump({"session_date": str(self.sd), "bars": self.replay_all}, open(tmp, "w"))
        os.replace(tmp, cache)
        if not any(self.replay_all.values()):
            self.state["yahoo_blocked"] = True
            self.log.warning("YAHOO_BLOCKED: replay loaded no bars")

    def set_replay_time(self, now_ts):
        for s, bl in self.replay_all.items():
            self.bars[s] = [b for b in bl if b["t"] + 60 <= now_ts]

    def session(self, s):
        return [b for b in self.bars.get(s, []) if datetime.fromtimestamp(b["t"], ET).date() == self.sd]

    @staticmethod
    def to5(bars, now_ts):
        out = {}
        for b in bars:
            k = b["t"] // 300 * 300
            if k + 300 > now_ts: continue
            if k not in out: out[k] = dict(t=k, o=b["o"], h=b["h"], l=b["l"], c=b["c"], v=b["v"])
            else:
                x = out[k]; x["h"] = max(x["h"], b["h"]); x["l"] = min(x["l"], b["l"]); x["c"] = b["c"]; x["v"] += b["v"]
        return [out[k] for k in sorted(out)]

    def ind(self, s, now_ts):
        """Indicators for symbol s: price, vwap, 5m bars (session), ema20 series (on all 5m), atr5."""
        sess = self.session(s)
        if not sess: return None
        pv = sum((b["h"] + b["l"] + b["c"]) / 3 * b["v"] for b in sess); vv = sum(b["v"] for b in sess)
        vwap = pv / vv if vv > 0 else None
        all5 = self.to5(self.bars[s], now_ts)
        e = ema([b["c"] for b in all5], 20)
        for b, x in zip(all5, e): b["ema20"] = x
        s5 = [b for b in all5 if datetime.fromtimestamp(b["t"], ET).date() == self.sd]
        self._stamp_vwap(sess, s5)
        tr = [max(all5[i]["h"] - all5[i]["l"], abs(all5[i]["h"] - all5[i-1]["c"]), abs(all5[i]["l"] - all5[i-1]["c"])) for i in range(1, len(all5))]
        atr5 = sum(tr[-14:]) / min(14, len(tr)) if tr else None
        last = sess[-1]
        return dict(price=last["c"], last=last, vwap=vwap, s5=s5, ema20=e[-1] if e else None, atr5=atr5, sess=sess)

    @staticmethod
    def _stamp_vwap(sess, s5):
        """Session VWAP as of the last 1-minute bar in each completed 5-minute bucket."""
        pv = vv = 0.0
        bucket = {}
        for b in sess:
            v = b["v"] or 0
            pv += (b["h"] + b["l"] + b["c"]) / 3 * v
            vv += v
            if vv > 0:
                bucket[b["t"] // 300 * 300] = pv / vv
        for b in s5:
            b["vwap"] = bucket.get(b["t"])

    # ---------- context ----------
    def etf_state(self, etf, I):
        x = I.get(etf); c = self.ctx.get(etf)
        if not x or not c or x["vwap"] is None: return None
        return dict(green=x["price"] > c["prev_close"], above_vwap=x["price"] > x["vwap"], red=x["price"] < c["prev_close"])

    def context_ok(self, s, side, I):
        cfg = self.rules["context"]; x = I[s]; w = self.wl(s)
        if x["vwap"] is None or x["ema20"] is None: return False, "no vwap/ema"
        sec = self.etf_state(w["sector"], I); spy = self.etf_state("SPY", I)
        if sec is None or spy is None: return False, "no sector data"
        if side == "long":
            ok = (not cfg["require_above_vwap"] or x["price"] > x["vwap"]) and \
                 (not cfg["require_above_ema20_5m"] or x["price"] > x["ema20"]) and \
                 (not cfg["require_sector_green"] or sec["green"]) and \
                 (not cfg["require_sector_above_vwap"] or sec["above_vwap"]) and \
                 (not cfg["require_spy_with_trade"] or spy["green"] or spy["above_vwap"])
        else:
            ok = (not cfg["require_above_vwap"] or x["price"] < x["vwap"]) and \
                 (not cfg["require_above_ema20_5m"] or x["price"] < x["ema20"]) and \
                 (not cfg["require_sector_green"] or sec["red"]) and \
                 (not cfg["require_sector_above_vwap"] or not sec["above_vwap"]) and \
                 (not cfg["require_spy_with_trade"] or spy["red"] or not spy["above_vwap"])
        desc = (f"px {x['price']:.2f} vwap {x['vwap']:.2f} ema20 {x['ema20']:.2f}; {w['sector']} "
                f"{'green' if sec['green'] else 'red'}/{'>' if sec['above_vwap'] else '<'}vwap; SPY {'green' if spy['green'] else 'red'}")
        return ok, desc

    def context_ok_v2(self, s, side, I):
        """rules_v2 context: VWAP + EMA20, loosened SPY flat band, sector VWAP, high-RVOL sector bypass."""
        x = I[s]
        w = self.wl(s)
        c = self.ctx.get(s) or {}
        if x["vwap"] is None or x["ema20"] is None:
            return False, "no vwap/ema"
        sec = I.get(w["sector"])
        spy = I.get("SPY")
        sec_c = self.ctx.get(w["sector"]) or {}
        spy_c = self.ctx.get("SPY") or {}
        if not sec or not spy or sec.get("vwap") is None or spy.get("vwap") is None:
            return False, "no sector data"
        if not sec_c.get("prev_close") or not spy_c.get("prev_close"):
            return False, "no prev close"
        sgn = 1 if side == "long" else -1
        if sgn * (x["price"] - x["vwap"]) <= 0 or sgn * (x["price"] - x["ema20"]) <= 0:
            return False, "price on wrong side of vwap/ema20"
        if sgn * (sec["price"] - sec["vwap"]) <= 0:
            return False, "sector on wrong side of its vwap"
        spc = (spy["price"] / spy_c["prev_close"] - 1) * 100
        secc = (sec["price"] / sec_c["prev_close"] - 1) * 100
        spy_ok = sgn * spc > 0.15 or abs(spc) <= 0.15 or sgn * (spy["price"] - spy["vwap"]) > 0
        tod = 0.0
        if x["s5"]:
            b = x["s5"][-1]
            slot = datetime.fromtimestamp(b["t"], ET).strftime("%H:%M")
            avg = (c.get("slot_vol14") or {}).get(slot)
            if avg:
                tod = b["v"] / avg
        sec_ok = sgn * secc >= 0 or (tod >= 2.0 and sgn * secc >= -0.25)
        desc = (f"v2 px {x['price']:.2f} vwap {x['vwap']:.2f} ema20 {x['ema20']:.2f}; "
                f"SPY chg {spc:.2f}%; {w['sector']} chg {secc:.2f}%; tod rvol {tod:.2f}")
        return bool(spy_ok and sec_ok), desc

    def wl(self, s):
        return next(w for w in self.rules["watchlist"] if w["ticker"] == s)

    def side_allowed(self, s, side, rule):
        g = self.rules["global"]; bias = self.wl(s).get("bias", "both")
        if side not in rule["sides"]: return False
        if side == "short" and not g.get("allow_shorts", False): return False
        return bias == "both" or bias == side

    @staticmethod
    def in_window(now_ct, win):
        a, b = hm(win[0]), hm(win[1]); t = (now_ct.hour, now_ct.minute)
        return a <= t <= b

    def _rule_window_bounds_ct(self, win):
        """Return (start, end) datetimes in America/Chicago for a rule window_ct on this session date."""
        a, b = hm(win[0]), hm(win[1])
        start = datetime.combine(self.sd, datetime.min.time(), CT).replace(hour=a[0], minute=a[1], second=0)
        # inclusive end minute (matches in_window); use :59 so overlap math is continuous
        end = datetime.combine(self.sd, datetime.min.time(), CT).replace(hour=b[0], minute=b[1], second=59)
        return start, end

    def _missed_windows_during(self, stall_start, stall_end):
        """Enabled rule ids whose entry window_ct overlaps [stall_start, stall_end) in CT."""
        missed = []
        for rid, r in (self.rules.get("rules") or {}).items():
            if not isinstance(r, dict) or not r.get("enabled"):
                continue
            win = r.get("window_ct")
            if not win or len(win) != 2:
                continue
            w0, w1 = self._rule_window_bounds_ct(win)
            if stall_start <= w1 and stall_end >= w0:
                missed.append(rid)
        return missed

    def detect_stall(self, now_ct):
        """Compare wall-clock to last loop; if gap > 3 min, log WARNING and record in state['stalls'].
        Does NOT backfill trades or invent fills for a missed entry window."""
        if now_ct.tzinfo is None:
            now_ct = now_ct.replace(tzinfo=CT)
        else:
            now_ct = now_ct.astimezone(CT)
        self.state.setdefault("stalls", [])
        self.state.setdefault("missed_entry_window", False)
        prev_s = self.state.get("last_loop_ct")
        self.state["last_loop_ct"] = now_ct.isoformat()
        if not prev_s:
            return None
        try:
            prev = datetime.fromisoformat(prev_s)
            if prev.tzinfo is None:
                prev = prev.replace(tzinfo=CT)
            else:
                prev = prev.astimezone(CT)
        except Exception:
            return None
        gap_sec = (now_ct - prev).total_seconds()
        if gap_sec <= 180:
            return None
        gap_min = gap_sec / 60.0
        n_min = int(round(gap_min))
        start_hm = prev.strftime("%H:%M")
        end_hm = now_ct.strftime("%H:%M")
        missed = self._missed_windows_during(prev, now_ct)
        rec = {"start": start_hm, "end": end_hm, "minutes": round(gap_min, 1), "missed_windows": missed}
        self.state["stalls"].append(rec)
        if missed:
            self.state["missed_entry_window"] = True
        self.log.warning(f"STALL detected: {n_min} min gap ({start_hm}–{end_hm} CT)")
        if missed:
            self.log.warning(f"STALL overlapped entry windows (no backfill): {missed}")
        return rec

    def vol5_ok(self, s, s5, b, mult):
        """5m bar volume vs the same time-of-day slot's 14-session average (U-shaped intraday volume adjusted)."""
        slot = datetime.fromtimestamp(b["t"], ET).strftime("%H:%M")
        avg = (self.ctx.get(s) or {}).get("slot_vol14", {}).get(slot)
        if avg: return b["v"] >= mult * avg, b["v"] / avg
        return self.vol_ok(s5, b, mult)

    @staticmethod
    def vol_ok(bars, b, mult, n=12, min_n=3):
        prior = [x["v"] for x in bars if x["t"] < b["t"]][-n:]
        if len(prior) < min_n: return False, 0
        avg = sum(prior) / len(prior)
        return (avg > 0 and b["v"] >= mult * avg), (b["v"] / avg if avg else 0)

    # ---------- signals ----------
    def signals(self, s, I, now_ts, now_ct):
        """Return list of candidate entries: dict(rule, side, stop, reason)."""
        R = self.rules["rules"]; x = I[s]; c = self.ctx.get(s); s5 = x["s5"]; out = []
        if not c or len(s5) < 1: return out
        price = x["price"]; sess = x["sess"]; atrd = c["atr14"]
        # R8 gap fade (v3 backtest winner). Evaluated once per ticker per day on the first completed 5m bar.
        r = R.get("R8")
        if r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and (s, "R8") not in self.seen5:
            orb = s5[0]; self.seen5[(s, "R8")] = orb["t"]
            g = orb["o"] / c["prev_close"] - 1; lo, hi = r["gap_min_pct"] / 100, r["gap_max_pct"] / 100
            if lo <= g <= hi and orb["c"] < orb["o"]:
                out.append(dict(rule="R8", side="short", stop=orb["h"] + r["stop_buffer_atr"] * atrd, target_px=c["prev_close"],
                                reason=f"gap fade: gap +{g*100:.2f}% (open {orb['o']:.2f} vs prev close {c['prev_close']:.2f}), first 5m bar red; target prev close"))
            if -hi <= g <= -lo and orb["c"] > orb["o"]:
                out.append(dict(rule="R8", side="long", stop=orb["l"] - r["stop_buffer_atr"] * atrd, target_px=c["prev_close"],
                                reason=f"gap fade: gap {g*100:.2f}% (open {orb['o']:.2f} vs prev close {c['prev_close']:.2f}), first 5m bar green; target prev close"))
        # NR7 / inside-day breakout (EXPERIMENTAL). First 1m bar that trades through the prior-day high/low
        # after the opening 5 minutes. Fill is the level (or the bar open if gapped through). No backfill.
        r = R.get("NR7")
        if r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and len(sess) >= 6:
            flags = set(c.get("flags") or [])
            if flags & {"NR7", "inside_day"}:
                last, prevb = sess[-1], sess[-2]
                if prevb["h"] <= c["prev_high"] < last["h"]:
                    out.append(dict(
                        rule="NR7", side="long", level=c["prev_high"], stop_dist=r["stop_atr_frac"] * atrd,
                        reason=(f"NR7/inside breakout long through prior high {c['prev_high']:.2f} "
                                f"flags={sorted(flags)} EXPERIMENTAL")))
                if prevb["l"] >= c["prev_low"] > last["l"]:
                    out.append(dict(
                        rule="NR7", side="short", level=c["prev_low"], stop_dist=r["stop_atr_frac"] * atrd,
                        reason=(f"NR7/inside breakout short through prior low {c['prev_low']:.2f} "
                                f"flags={sorted(flags)} EXPERIMENTAL")))
        # R1 ORB
        r = R.get("R1")
        if r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and len(sess) >= 6:
            orb = s5[0]; rvol = orb["v"] / c["avg_open5_vol14"] if c.get("avg_open5_vol14") else 0
            vok, vr = (self.vol_ok(sess, sess[-1], r["vol_mult"], n=10, min_n=3) if r.get("vol_mult", 0) > 0 else (True, 0))
            ext = r.get("max_extension_atr", 0.15) * atrd
            if rvol >= r["min_open_rvol"] and vok:
                if orb["c"] > orb["o"] and orb["h"] < price <= orb["h"] + ext:
                    out.append(dict(rule="R1", side="long", stop=price - r["stop_atr_frac"] * atrd,
                                    reason=f"ORB5 long: 1m close {price:.2f} > OR high {orb['h']:.2f}; open RVOL {rvol:.2f}; 1m vol x{vr:.1f}"))
                if orb["c"] < orb["o"] and orb["l"] > price >= orb["l"] - ext:
                    out.append(dict(rule="R1", side="short", stop=price + r["stop_atr_frac"] * atrd,
                                    reason=f"ORB5 short: 1m close {price:.2f} < OR low {orb['l']:.2f}; open RVOL {rvol:.2f}; 1m vol x{vr:.1f}"))
        if len(s5) < 2 or x["atr5"] is None: return out
        b, p = s5[-1], s5[-2]
        sup = max(x["vwap"], b["ema20"]); res = min(x["vwap"], b["ema20"])
        # R2 engulfing (sets pending confirmation)
        r = R.get("R2")
        if r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and self.seen5.get((s, "R2")) != b["t"]:
            self.seen5[(s, "R2")] = b["t"]
            vok, vr = self.vol5_ok(s, s5, b, r["vol_mult"])
            tol = r["touch_tol_pct"] / 100
            if vok and p["c"] < p["o"] and b["c"] > b["o"] and b["c"] >= p["o"] and b["o"] <= p["c"] \
                    and min(b["l"], p["l"]) <= sup * (1 + tol) and b["c"] > x["vwap"] and b["c"] > b["ema20"]:
                self.add_pending(s, "R2", "long", b["h"], min(b["l"], p["l"]) - r["stop_buffer_atr5"] * x["atr5"], now_ts, r,
                                 f"5m bull engulf {ct_of(b['t']):%H:%M} at VWAP/EMA20 zone, vol x{vr:.1f}")
            if vok and p["c"] > p["o"] and b["c"] < b["o"] and b["c"] <= p["o"] and b["o"] >= p["c"] \
                    and max(b["h"], p["h"]) >= res * (1 - tol) and b["c"] < x["vwap"] and b["c"] < b["ema20"]:
                self.add_pending(s, "R2", "short", b["l"], max(b["h"], p["h"]) + r["stop_buffer_atr5"] * x["atr5"], now_ts, r,
                                 f"5m bear engulf {ct_of(b['t']):%H:%M} at VWAP/EMA20 zone, vol x{vr:.1f}")
        # R3 hammer / shooting star
        r = R.get("R3")
        if r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and self.seen5.get((s, "R3")) != b["t"]:
            self.seen5[(s, "R3")] = b["t"]
            vok, vr = self.vol5_ok(s, s5, b, r["vol_mult"])
            body = abs(b["c"] - b["o"]); rng = b["h"] - b["l"]; lw = min(b["o"], b["c"]) - b["l"]; uw = b["h"] - max(b["o"], b["c"])
            tol = r["touch_tol_pct"] / 100; k = r["wick_body_ratio"]
            if vok and rng > 0.3 * x["atr5"] and body > 0:
                if lw >= k * body and uw <= body and b["l"] <= sup * (1 + tol) and b["c"] > x["vwap"] and b["c"] > b["ema20"]:
                    self.add_pending(s, "R3", "long", b["h"], b["l"] - r["stop_buffer_atr5"] * x["atr5"], now_ts, r,
                                     f"5m hammer {ct_of(b['t']):%H:%M} at VWAP/EMA20, vol x{vr:.1f}")
                if uw >= k * body and lw <= body and b["h"] >= res * (1 - tol) and b["c"] < x["vwap"] and b["c"] < b["ema20"]:
                    self.add_pending(s, "R3", "short", b["l"], b["h"] + r["stop_buffer_atr5"] * x["atr5"], now_ts, r,
                                     f"5m shooting star {ct_of(b['t']):%H:%M} at VWAP/EMA20, vol x{vr:.1f}")
        # R4 daily-pattern breakout of prior-day high/low
        r = R.get("R4"); flags = set(self.wl(s).get("daily_flags", []))
        if r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and self.seen5.get((s, "R4")) != b["t"]:
            self.seen5[(s, "R4")] = b["t"]
            vok, vr = self.vol5_ok(s, s5, b, r["vol_mult"])
            if vok and flags & set(r["long_flags"]) and p["c"] <= c["prev_high"] < b["c"] and price > c["prev_high"]:
                out.append(dict(rule="R4", side="long", stop=price - r["stop_atr_frac"] * atrd,
                                reason=f"5m close {b['c']:.2f} broke prior-day high {c['prev_high']:.2f} (daily {sorted(flags)}), vol x{vr:.1f}"))
            if vok and flags & set(r["short_flags"]) and p["c"] >= c["prev_low"] > b["c"] and price < c["prev_low"]:
                out.append(dict(rule="R4", side="short", stop=price + r["stop_atr_frac"] * atrd,
                                reason=f"5m close {b['c']:.2f} broke prior-day low {c['prev_low']:.2f} (daily {sorted(flags)}), vol x{vr:.1f}"))
        # R5 trend pullback to EMA20
        r = R.get("R5")
        if r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and len(s5) >= r["ema_slope_bars"] + 2 \
                and self.seen5.get((s, "R5")) != b["t"]:
            self.seen5[(s, "R5")] = b["t"]
            vok, vr = self.vol5_ok(s, s5, b, r["vol_mult"]); k = r["ema_slope_bars"]; e_then = s5[-1 - k]["ema20"]
            if vok and b["ema20"] > e_then and p["l"] <= p["ema20"] * 1.001 and p["c"] >= x["vwap"] and b["c"] > p["h"] and price > p["h"]:
                out.append(dict(rule="R5", side="long", stop=min(p["l"], b["l"]) - r["stop_buffer_atr5"] * x["atr5"],
                                reason=f"pullback to rising EMA20 ({p['ema20']:.2f}) then 5m close {b['c']:.2f} > pullback high {p['h']:.2f}, vol x{vr:.1f}"))
            if vok and b["ema20"] < e_then and p["h"] >= p["ema20"] * 0.999 and p["c"] <= x["vwap"] and b["c"] < p["l"] and price < p["l"]:
                out.append(dict(rule="R5", side="short", stop=max(p["h"], b["h"]) + r["stop_buffer_atr5"] * x["atr5"],
                                reason=f"rally to falling EMA20 ({p['ema20']:.2f}) then 5m close {b['c']:.2f} < pullback low {p['l']:.2f}, vol x{vr:.1f}"))
        # R6 VWAP reclaim (EXPERIMENTAL, rules_v2). Once per completed 5m bar.
        r = R.get("R6")
        if (r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and x["atr5"]
                and b.get("vwap") is not None and p.get("vwap") is not None
                and self.seen5.get((s, "R6")) != b["t"]):
            self.seen5[(s, "R6")] = b["t"]
            mult = r["vol_mult"]
            if (c.get("daily_rvol") or 0) >= 1.5:
                mult = r.get("vol_mult_high_rvol_name", mult)
            vok, vr = self.vol5_ok(s, s5, b, mult)
            if vok and p["c"] < p["vwap"] and b["c"] > b["vwap"]:
                out.append(dict(rule="R6", side="long", stop=b["c"] - r["stop_atr_frac_5m"] * x["atr5"],
                                reason=(f"VWAP reclaim long EXPERIMENTAL: prior 5m {p['c']:.2f} < vwap {p['vwap']:.2f}, "
                                        f"close {b['c']:.2f} > vwap {b['vwap']:.2f}, vol x{vr:.1f}")))
            if vok and p["c"] > p["vwap"] and b["c"] < b["vwap"]:
                out.append(dict(rule="R6", side="short", stop=b["c"] + r["stop_atr_frac_5m"] * x["atr5"],
                                reason=(f"VWAP reclaim short EXPERIMENTAL: prior 5m {p['c']:.2f} > vwap {p['vwap']:.2f}, "
                                        f"close {b['c']:.2f} < vwap {b['vwap']:.2f}, vol x{vr:.1f}")))
        # R7 RVOL spike continuation (EXPERIMENTAL, rules_v2).
        r = R.get("R7")
        spy = I.get("SPY")
        spy_c = self.ctx.get("SPY") or {}
        if (r and r["enabled"] and self.in_window(now_ct, r["window_ct"]) and self.seen5.get((s, "R7")) != b["t"]
                and spy and spy.get("vwap") is not None and spy_c.get("prev_close") and b["h"] > b["l"]):
            self.seen5[(s, "R7")] = b["t"]
            _ok, vr = self.vol5_ok(s, s5, b, r["spike_tod_rvol_min"])
            if vr >= r["spike_tod_rvol_min"]:
                posn = (b["c"] - b["l"]) / (b["h"] - b["l"])
                mid = (b["h"] + b["l"]) / 2
                spc = (spy["price"] / spy_c["prev_close"] - 1) * 100
                if posn >= r["close_range_pctile_long_min"] and (spc >= -0.15 or spy["price"] > spy["vwap"]):
                    out.append(dict(rule="R7", side="long", stop=max(mid, b["c"] - r["stop_daily_atr_frac"] * atrd),
                                    reason=(f"RVOL spike long EXPERIMENTAL: 5m vol x{vr:.1f}, close in top of range, "
                                            f"SPY chg {spc:.2f}%")))
                if posn <= r["close_range_pctile_short_max"] and (spc <= 0.15 or spy["price"] < spy["vwap"]):
                    out.append(dict(rule="R7", side="short", stop=min(mid, b["c"] + r["stop_daily_atr_frac"] * atrd),
                                    reason=(f"RVOL spike short EXPERIMENTAL: 5m vol x{vr:.1f}, close in bottom of range, "
                                            f"SPY chg {spc:.2f}%")))
        # pending confirmations (R2/R3)
        for pd in list(self.pending):
            if pd["sym"] != s: continue
            if now_ts > pd["expires"]: self.pending.remove(pd); continue
            if (pd["side"] == "long" and price > pd["trigger"]) or (pd["side"] == "short" and price < pd["trigger"]):
                out.append(dict(rule=pd["rule"], side=pd["side"], stop=pd["stop"],
                                reason=pd["reason"] + f"; confirmed: 1m close {price:.2f} {'>' if pd['side']=='long' else '<'} pattern {'high' if pd['side']=='long' else 'low'} {pd['trigger']:.2f}"))
                self.pending.remove(pd)
        return out

    def add_pending(self, s, rule, side, trigger, stop, now_ts, r, reason):
        if not self.side_allowed(s, side, r): return
        self.pending = [p for p in self.pending if not (p["sym"] == s and p["rule"] == rule)]
        self.pending.append(dict(sym=s, rule=rule, side=side, trigger=trigger, stop=stop, reason=reason,
                                 expires=now_ts + 60 * r["confirm_bars_1m"]))
        self.log.info(f"setup {rule} {side} {s}: {reason}; trigger {trigger:.2f} stop {stop:.2f}")

    # ---------- trading ----------
    def equity(self):
        eq = self.state["cash"]
        for s, pos in self.state["positions"].items():
            px = self.state["last_prices"].get(s, pos["entry_price"])
            if pos["side"] == "long": eq += pos["shares"] * px
            else: eq += pos["notional"] + (pos["entry_price"] - px) * pos["shares"]
        return eq

    def write_trade(self, row):
        row = {k: row.get(k, "") for k in TRADE_COLS}
        with open(self.p["trades"], "a", newline="") as f: csv.DictWriter(f, TRADE_COLS).writerow(row)

    def try_enter(self, s, sig, I, now_ts, now_ct):
        g = self.rules["global"]; st = self.state; r = self.rules["rules"][sig["rule"]]
        if s in st["positions"] or len(st["positions"]) >= g["max_positions"] or st["halted"]: return False
        if not self.in_window(now_ct, [g["entry_start_ct"], g["entry_cutoff_ct"]]): return False
        if not self.side_allowed(s, sig["side"], r): return False
        key = f"{s}|{sig['rule']}"
        if st["entries"].get(key, 0) >= r.get("max_entries", g["max_entries_per_ticker_per_rule"]): return False
        if now_ts - st["last_stop_ts"].get(s, 0) < 60 * g["cooldown_min_after_stop"]: return False
        if r.get("skip_context"):
            ok, cdesc = True, "context filter not used by this rule (matches backtest)"
        elif r.get("context_mode") == "v2":
            ok, cdesc = self.context_ok_v2(s, sig["side"], I)
        else:
            ok, cdesc = self.context_ok(s, sig["side"], I)
        if not ok:
            self.log.info(f"skip {sig['rule']} {sig['side']} {s}: context failed ({cdesc})"); return False
        bar = I[s]["last"]; slip = g["slippage_bps"] / 1e4
        if "level" in sig:
            lvl = sig["level"]
            if sig["side"] == "long":
                if bar["h"] < lvl:
                    self.log.info(f"skip {s} {sig['rule']}: 1m bar did not trade through {lvl:.4f}"); return False
                raw = max(lvl, bar["o"])
            else:
                if bar["l"] > lvl:
                    self.log.info(f"skip {s} {sig['rule']}: 1m bar did not trade through {lvl:.4f}"); return False
                raw = min(lvl, bar["o"])
        else:
            raw = bar["c"]
        px = raw * (1 + slip) if sig["side"] == "long" else raw * (1 - slip)
        if "stop_dist" in sig:
            dist = float(sig["stop_dist"])
        else:
            if (sig["side"] == "long" and sig["stop"] >= px) or (sig["side"] == "short" and sig["stop"] <= px):
                self.log.info(f"skip {s} {sig['rule']}: stop on wrong side"); return False
            dist = abs(px - sig["stop"])
        dist = max(dist, px * g["min_stop_pct"] / 100)
        stop = px - dist if sig["side"] == "long" else px + dist
        eq = self.equity()
        risk_usd = eq * g["risk_pct"] / 100 * r.get("risk_mult", 1.0) * st.get("risk_scale", 1.0)
        cap_usd = float(g.get("max_position_notional_usd", 350.0))
        pct_cap = g["budget_usd"] * g.get("max_position_notional_pct", 35.0) / 100.0
        cap = min(st["cash"], cap_usd, pct_cap)
        shares = min(risk_usd / dist, cap / px)
        shares = math.floor(shares * 1e4) / 1e4
        notional = shares * px
        if notional < 25: 
            self.log.info(f"skip {s} {sig['rule']}: size ${notional:.2f} too small (cash ${st['cash']:.2f})"); return False
        if "target_px" in sig:
            target = sig["target_px"]
            if (sig["side"] == "long" and target <= px) or (sig["side"] == "short" and target >= px):
                self.log.info(f"skip {s} {sig['rule']}: price already through target {target:.2f}"); return False
        else:
            target = px + r["target_r"] * dist if sig["side"] == "long" else px - r["target_r"] * dist
        st["cash"] -= notional
        pos = dict(ticker=s, side=sig["side"], rule=sig["rule"], entry_ts=bar["t"] + 60, entry_time_ct=f"{now_ct:%H:%M:%S}",
                   entry_price=px, shares=shares, notional=notional, stop=stop, target=target, risk_per_share=dist,
                   time_stop_min=r["time_stop_min"], last_checked=bar["t"], reason=sig["reason"])
        st["positions"][s] = pos; st["entries"][key] = st["entries"].get(key, 0) + 1
        self.write_trade(dict(time_ct=f"{now_ct:%Y-%m-%d %H:%M:%S}", mode=self.mode, action="BUY" if sig["side"] == "long" else "SELL_SHORT",
                              ticker=s, side=sig["side"], price=round(px, 4), shares=shares, size_usd=round(notional, 2),
                              rule_id=sig["rule"], reason=sig["reason"] + " | ctx: " + cdesc, stop=round(stop, 4), target=round(target, 4),
                              data_bar_ct=f"{ct_of(bar['t']):%H:%M}", bar_close_raw=raw, slippage_bps=g["slippage_bps"]))
        self.log.info(f"ENTER {sig['side']} {s} {sig['rule']} {shares}@{px:.4f} (${notional:.2f}) stop {stop:.4f} tgt {target:.4f} :: {sig['reason']}")
        if "level" in sig:
            if sig["side"] == "long" and bar["l"] <= stop:
                self.exit_pos(s, min(stop, bar["o"]), "STOP", bar, now_ct)
            elif sig["side"] == "short" and bar["h"] >= stop:
                self.exit_pos(s, max(stop, bar["o"]), "STOP", bar, now_ct)
        self.rebuild_journal(force=True)
        return True

    def exit_pos(self, s, fill_raw, reason, bar, now_ct):
        g = self.rules["global"]; st = self.state; pos = st["positions"].pop(s); slip = g["slippage_bps"] / 1e4
        if pos["side"] == "long":
            px = fill_raw * (1 - slip); pnl = (px - pos["entry_price"]) * pos["shares"]; st["cash"] += pos["shares"] * px
        else:
            px = fill_raw * (1 + slip); pnl = (pos["entry_price"] - px) * pos["shares"]; st["cash"] += pos["notional"] + pnl
        st["realized_pnl"] += pnl
        rmult = pnl / (pos["risk_per_share"] * pos["shares"]) if pos["shares"] else 0
        hold = (bar["t"] + 60 - pos["entry_ts"]) / 60
        rec = dict(ticker=s, side=pos["side"], rule=pos["rule"], pnl=pnl, r=rmult, reason=reason, hold_min=hold,
                   entry_time=pos["entry_time_ct"], exit_time=f"{now_ct:%H:%M:%S}", entry=pos["entry_price"], exit=px,
                   shares=pos["shares"], notional=pos["notional"])
        st["closed"].append(rec)
        if reason == "STOP": st["last_stop_ts"][s] = bar["t"] + 60
        self.write_trade(dict(time_ct=f"{now_ct:%Y-%m-%d %H:%M:%S}", mode=self.mode, action="SELL" if pos["side"] == "long" else "BUY_COVER",
                              ticker=s, side=pos["side"], price=round(px, 4), shares=pos["shares"], size_usd=round(pos["shares"] * px, 2),
                              rule_id=pos["rule"], reason=pos["reason"], pnl_usd=round(pnl, 2), pnl_pct=round(pnl / pos["notional"] * 100, 3),
                              exit_reason=reason, entry_time_ct=pos["entry_time_ct"], entry_price=round(pos["entry_price"], 4),
                              stop=round(pos["stop"], 4), target=round(pos["target"], 4), r_multiple=round(rmult, 2), hold_min=round(hold, 1),
                              data_bar_ct=f"{ct_of(bar['t']):%H:%M}", bar_close_raw=fill_raw, slippage_bps=g["slippage_bps"]))
        self.log.info(f"EXIT {pos['side']} {s} {pos['rule']} {reason} @ {px:.4f} pnl ${pnl:.2f} ({rmult:.2f}R)")
        self.rebuild_journal(force=True)

    def manage(self, now_ts, now_ct):
        g = self.rules["global"]; fl = hm(g["flatten_ct"])
        for s in list(self.state["positions"]):
            pos = self.state["positions"][s]
            new = [b for b in self.session(s) if b["t"] > pos["last_checked"]]
            for b in new:
                pos["last_checked"] = b["t"]; bct = ct_of(b["t"] + 60)
                if pos["side"] == "long":
                    if b["l"] <= pos["stop"]: self.exit_pos(s, min(pos["stop"], b["o"]), "STOP", b, now_ct); break
                    if b["h"] >= pos["target"]: self.exit_pos(s, max(pos["target"], b["o"]), "TARGET", b, now_ct); break
                else:
                    if b["h"] >= pos["stop"]: self.exit_pos(s, max(pos["stop"], b["o"]), "STOP", b, now_ct); break
                    if b["l"] <= pos["target"]: self.exit_pos(s, min(pos["target"], b["o"]), "TARGET", b, now_ct); break
                if b["t"] + 60 - pos["entry_ts"] >= pos["time_stop_min"] * 60:
                    self.exit_pos(s, b["c"], "TIME_STOP", b, now_ct); break
                if (bct.hour, bct.minute) >= fl:
                    self.exit_pos(s, b["c"], "EOD_FLATTEN_1455", b, now_ct); break
        if (now_ct.hour, now_ct.minute) >= fl:
            for s in list(self.state["positions"]):
                sess = self.session(s)
                if sess: self.exit_pos(s, sess[-1]["c"], "EOD_FLATTEN_1455", sess[-1], now_ct)

    # ---------- hourly review / self-tweak ----------
    def review(self, label, now_ct):
        rv = self.rules["review"]; R = self.rules["rules"]; st = self.state; changes = []
        closed = st["closed"]; g = self.rules["global"]
        lines = [f"## Review {label} CT ({now_ct:%Y-%m-%d %H:%M})", "",
                 f"Equity ${self.equity():.2f} | cash ${st['cash']:.2f} | realized ${st['realized_pnl']:.2f} | open {len(st['positions'])} | closed trades {len(closed)}", "",
                 "| rule | trades | wins | win% | P&L $ | avg R | stops<=5min | time-stops |", "|---|---|---|---|---|---|---|---|"]
        for rid, r in R.items():
            t = [c for c in closed if c["rule"] == rid]; n = len(t); w = sum(1 for c in t if c["pnl"] > 0)
            pnl = sum(c["pnl"] for c in t); wr = w / n if n else 0
            stops = [c for c in t if c["reason"] == "STOP"]; quick = [c for c in stops if c["hold_min"] <= rv["quickstop_min"]]
            ts = [c for c in t if c["reason"] == "TIME_STOP"]
            lines.append(f"| {rid} | {n} | {w} | {wr*100:.0f}% | {pnl:.2f} | {(sum(c['r'] for c in t)/n if n else 0):.2f} | {len(quick)}/{len(stops)} | {len(ts)} |")
            entered = sum(v for k, v in st["entries"].items() if k.endswith("|" + rid))
            if not r["enabled"]: continue
            mt = rv.get("min_trades_for_change", 8)
            if n < mt:
                lines.append(f"  - {rid}: {n} closed trades < {mt} minimum -> no tweak of any kind (8-closed-trade minimum)")
                continue
            def chg(param, new, why):
                old = r.get(param); r[param] = new; changes.append((rid, param, old, new, why))
            # T1 drop
            if n >= max(rv["drop_min_trades"], mt) and wr < rv["drop_max_winrate"] and pnl < 0:
                chg("enabled", False, f"T1: {n} trades, win rate {wr:.0%} < {rv['drop_max_winrate']:.0%} and P&L ${pnl:.2f} < 0"); continue
            # T2 quick stops -> widen stop + stricter volume
            if n >= max(rv["drop_min_trades"], mt) and len(quick) >= rv["quickstop_min_events"] and len(quick) > rv["quickstop_frac"] * len(stops):
                if "stop_atr_frac" in r:
                    base = r.setdefault("_base_stop_atr_frac", r["stop_atr_frac"])
                    new = round(min(r["stop_atr_frac"] * rv["widen_stop_factor"], base * rv["max_stop_widen_total"]), 4)
                    if new > r["stop_atr_frac"]: chg("stop_atr_frac", new, f"T2: {len(quick)}/{len(stops)} stops hit within {rv['quickstop_min']} min -> widen stop")
                elif "stop_buffer_atr5" in r:
                    new = round(min(r["stop_buffer_atr5"] + 0.15, 0.5), 3)
                    if new > r["stop_buffer_atr5"]: chg("stop_buffer_atr5", new, f"T2: {len(quick)}/{len(stops)} stops within {rv['quickstop_min']} min -> wider buffer")
                nv = round(min(r["vol_mult"] + rv["vol_mult_step"], rv["vol_mult_max"]), 2)
                if nv > r["vol_mult"]: chg("vol_mult", nv, "T2: quick stops -> require stronger volume confirmation")
                continue
            # T4 promote
            if n >= max(rv["promote_min_trades"], mt) and wr >= rv["promote_min_winrate"] and pnl > 0:
                nr = round(min(r.get("risk_mult", 1.0) + rv["risk_mult_step"], rv["risk_mult_max"]), 2)
                if nr > r.get("risk_mult", 1.0): chg("risk_mult", nr, f"T4: {n} trades, win {wr:.0%} >= {rv['promote_min_winrate']:.0%}, P&L ${pnl:.2f} > 0 -> more risk")
                continue
            # T5 time-stop tuning
            if n >= mt and len(ts) >= rv["timestop_min_events"]:
                avg = sum(c["pnl"] for c in ts) / len(ts)
                if avg > 0: nt = int(min(r["time_stop_min"] * rv["timestop_extend"], rv["timestop_max"]))
                else: nt = int(max(r["time_stop_min"] * rv["timestop_shrink"], rv["timestop_min"]))
                if nt != r["time_stop_min"]:
                    chg("time_stop_min", nt, f"T5: {len(ts)} time-stop exits avg P&L ${avg:.2f} -> {'extend' if avg>0 else 'shorten'} time stop")
                continue
            # T3 loosen if never triggered
            if entered == 0:
                c = st["no_trigger_reviews"].get(rid, 0) + 1; st["no_trigger_reviews"][rid] = c
                if c >= rv["loosen_after_reviews_without_trigger"] and "vol_mult" in r:
                    nv = round(max(r["vol_mult"] - rv["vol_mult_step"], rv["vol_mult_min"]), 2)
                    if nv < r["vol_mult"]:
                        chg("vol_mult", nv, f"T3: no entries in {c} consecutive reviews -> loosen volume filter (floor {rv['vol_mult_min']})")
                        st["no_trigger_reviews"][rid] = 0
            else:
                st["no_trigger_reviews"][rid] = 0
        # T6 portfolio de-risk
        dd = (self.equity() - g["budget_usd"]) / g["budget_usd"] * 100
        if dd <= -rv["portfolio_derisk_pct"] and st.get("risk_scale", 1.0) > 0.5:
            changes.append(("ALL", "risk_scale", st.get("risk_scale", 1.0), 0.5, f"T6: day P&L {dd:.2f}% <= -{rv['portfolio_derisk_pct']}% -> halve risk"))
            st["risk_scale"] = 0.5
        if changes:
            self.rules["version"] = self.rules.get("version", 1) + 1
            tmp = self.p["rules"] + ".tmp"; json.dump(self.rules, open(tmp, "w"), indent=2); os.replace(tmp, self.p["rules"])
            with open(self.p["changes"], "a", newline="") as f:
                wtr = csv.writer(f)
                for c in changes: wtr.writerow([f"{now_ct:%Y-%m-%d %H:%M}", *c])
        lines += ["", "Changes: " + ("none" if not changes else ""), *[f"- {c[0]} {c[1]}: {c[2]} -> {c[3]} ({c[4]})" for c in changes], "", ""]
        with open(self.p["review"], "a") as f: f.write("\n".join(lines))
        st["hourly"].append(dict(time=f"{now_ct:%H:%M}", equity=round(self.equity(), 2), cash=round(st["cash"], 2),
                                 realized=round(st["realized_pnl"], 2), open=len(st["positions"]), trades=len(closed), changes=len(changes)))
        self.log.info(f"review {label}: {len(changes)} changes")
        self.rebuild_journal(force=True)

    # ---------- journal ----------
    def rebuild_journal(self, force=False):
        if not force and time.time() - self.last_journal < 60 * self.rules["global"].get("journal_rebuild_min", 5):
            return
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font
            wb = Workbook(); ws = wb.active; ws.title = "Trades"
            with open(self.p["trades"]) as f: rows = list(csv.reader(f))
            for r in rows:
                ws.append([float(v) if v.replace('.', '', 1).replace('-', '', 1).isdigit() else v for v in r])
            if self.mode == "REPLAY": ws.insert_rows(1); ws["A1"] = "REPLAY — Yahoo bars, paper only, not a live session"
            o = wb.create_sheet("Open"); o.append(["ticker", "side", "rule", "entry_time_ct", "entry", "shares", "notional", "stop", "target", "last", "unrealized_usd"])
            for s, p in self.state["positions"].items():
                last = self.state["last_prices"].get(s, p["entry_price"])
                u = (last - p["entry_price"]) * p["shares"] * (1 if p["side"] == "long" else -1)
                o.append([s, p["side"], p["rule"], p["entry_time_ct"], round(p["entry_price"], 4), p["shares"], round(p["notional"], 2),
                          round(p["stop"], 4), round(p["target"], 4), last, round(u, 2)])
            rs = wb.create_sheet("Rules"); rs.append(["id", "name", "enabled", "params", "trades", "wins", "win_rate", "pnl_usd", "avg_R"])
            for rid, r in self.rules["rules"].items():
                t = [c for c in self.state["closed"] if c["rule"] == rid]; n = len(t); w = sum(1 for c in t if c["pnl"] > 0)
                params = {k: v for k, v in r.items() if k not in ("name", "enabled")}
                rs.append([rid, r["name"], r["enabled"], json.dumps(params), n, w, round(w / n, 3) if n else None,
                           round(sum(c["pnl"] for c in t), 2), round(sum(c["r"] for c in t) / n, 2) if n else None])
            ch = wb.create_sheet("Changes")
            with open(self.p["changes"]) as f:
                for r in csv.reader(f): ch.append(r)
            h = wb.create_sheet("Hourly"); h.append(["time_ct", "equity", "cash", "realized", "open", "closed_trades", "rule_changes"])
            for x in self.state["hourly"]: h.append([x["time"], x["equity"], x["cash"], x["realized"], x["open"], x["trades"], x["changes"]])
            sm = wb.create_sheet("Summary"); cl = self.state["closed"]; wins = [c for c in cl if c["pnl"] > 0]
            eq = self.equity(); g = self.rules["global"]
            for k, v in [("MODE", self.mode + (" (replay, paper only)" if self.mode == "REPLAY" else " (paper only, no real money)")),
                         ("session_date", str(self.sd)), ("updated_ct", datetime.now(CT).strftime("%Y-%m-%d %H:%M:%S")),
                         ("starting_budget", g["budget_usd"]), ("equity", round(eq, 2)), ("cash", round(self.state["cash"], 2)),
                         ("realized_pnl", round(self.state["realized_pnl"], 2)), ("unrealized_pnl", round(eq - g["budget_usd"] - self.state["realized_pnl"], 2)),
                         ("day_return_pct", round((eq / g["budget_usd"] - 1) * 100, 3)), ("closed_trades", len(cl)), ("wins", len(wins)),
                         ("win_rate", round(len(wins) / len(cl), 3) if cl else None), ("total_R", round(sum(c["r"] for c in cl), 2)),
                         ("open_positions", len(self.state["positions"])), ("halted", self.state["halted"]),
                         ("rules_version", self.rules.get("version")), ("data_source", "Yahoo Finance chart API 1m bars"),
                         ("fill_model", f"latest completed 1m close +/- {g['slippage_bps']} bps; stops/targets at level (or bar open if gapped through) +/- slippage")]:
                sm.append([k, v])
            for wsx in wb.worksheets:
                for c in wsx[1]: c.font = Font(bold=True)
            tmp = self.p["journal"] + ".tmp.xlsx"; wb.save(tmp); os.replace(tmp, self.p["journal"])
            self.last_journal = time.time()
        except Exception as e:
            self.log.error(f"journal rebuild failed: {e}\n{traceback.format_exc()}")

    def save_state(self):
        st = self.state; st["equity"] = round(self.equity(), 4); st["last_update"] = datetime.now(CT).isoformat()
        st["pending_setups"] = self.pending
        st["seen5"] = {f"{sym}|{rid}": ts for (sym, rid), ts in self.seen5.items()}
        st["job"] = self.job
        st["paper_only"] = True
        tmp = self.p["state"] + ".tmp"; json.dump(st, open(tmp, "w"), indent=1, default=str); os.replace(tmp, self.p["state"])

    def note_startup(self, now_ct):
        """Warn once if this live job starts after its entry window. Never backfills."""
        msg = late_start_warning(self.job, now_ct)
        if not msg:
            self.log.info(f"startup OK: Job {self.job} at {now_ct:%H:%M:%S %Z}")
            return
        self.log.warning(msg)
        notes = self.state.setdefault("startup_warnings", [])
        if msg not in notes:
            notes.append(msg)
        missed = missed_windows_for_job(self.job, self.rules.get("rules"), now_ct)
        if missed:
            self.state["missed_entry_window"] = True
            rec = {"start": "startup", "end": now_ct.strftime("%H:%M"), "minutes": None,
                   "missed_windows": missed, "startup": True}
            stalls = self.state.setdefault("stalls", [])
            if not any(s.get("startup") and s.get("missed_windows") == missed for s in stalls):
                stalls.append(rec)
            self.log.warning(f"STARTUP missed entry windows already closed (no backfill): {missed}")

    # ---------- one loop ----------
    def step(self, now_ts):
        now_ct = ct_of(now_ts); g = self.rules["global"]
        self.load_rules()
        tick, etfs = self.symbols()
        I = {}
        for s in tick + etfs:
            try:
                x = self.ind(s, now_ts)
                if x: I[s] = x; self.state["last_prices"][s] = x["price"]
            except Exception as e:
                self.log.warning(f"indicator error {s}: {e}")
        self.manage(now_ts, now_ct)
        eq = self.equity()
        if (eq - g["budget_usd"]) / g["budget_usd"] * 100 <= -g["daily_loss_halt_pct"] and not self.state["halted"]:
            self.state["halted"] = True; self.log.warning(f"daily loss halt: equity ${eq:.2f}")
        if self.in_window(now_ct, [g["entry_start_ct"], g["entry_cutoff_ct"]]):
            for s in tick:
                if s not in I: continue
                try:
                    for sig in self.signals(s, I, now_ts, now_ct):
                        if self.try_enter(s, sig, I, now_ts, now_ct): break
                except Exception as e:
                    self.log.error(f"signal error {s}: {e}\n{traceback.format_exc()}")
        for rt in g["review_times_ct"]:
            if rt not in self.state["reviews_done"] and (now_ct.hour, now_ct.minute) >= hm(rt):
                self.state["reviews_done"].append(rt)
                if (now_ct.hour, now_ct.minute) <= (hm(rt)[0], hm(rt)[1] + 5): self.review(rt, now_ct)
        self.state["loops"] += 1
        self.save_state()
        self.rebuild_journal()


def _ensure_ctx(eng, replay):
    if replay and os.path.exists(eng.p["ctx"]):
        try:
            ctx = json.load(open(eng.p["ctx"]))
            if ctx.get("session_date") == str(eng.sd) and ctx.get("symbols"):
                eng.ctx = ctx["symbols"]
                eng.log.info(f"reused context.json ({len(eng.ctx)} symbols)")
                return
        except Exception as e:
            eng.log.warning(f"context reuse failed: {e}")
    attempts = 1 if replay else 5
    last = None
    for _ in range(attempts):
        try:
            eng.build_ctx()
            return
        except Exception as e:
            last = e
            eng.log.error(f"ctx build failed: {e}")
            if not replay:
                time.sleep(20)
    if replay:
        raise RuntimeError(f"context build failed: {last}")


def _flatten_remaining(eng, now_ts):
    now_ct = ct_of(now_ts)
    for s in list(eng.state["positions"]):
        sess = eng.session(s)
        if sess:
            eng.exit_pos(s, sess[-1]["c"], "EOD_FLATTEN_FINAL", sess[-1], now_ct)


def run_session(job, session_date, outdir, replay=False):
    """Run one paper job. Job A does not flatten. Job B flattens and is the session end."""
    mode = "REPLAY" if replay else "LIVE-PAPER"
    eng = Engine(mode, session_date, outdir, job=job)
    eng.log.info(f"=== {mode} JOB {job} pid={os.getpid()} session {session_date} (paper only, no orders) ===")
    enabled = [rid for rid, rule in eng.rules["rules"].items() if isinstance(rule, dict) and rule.get("enabled")]
    eng.log.info("enabled rules: " + ", ".join(enabled))
    _ensure_ctx(eng, replay)
    spec = JOBS[job]
    trade_start = combine_ct(session_date, spec["trade_start"])
    trade_end = combine_ct(session_date, spec["trade_end"])

    if replay:
        eng.load_replay()
        if job == "B" and eng.state.get("next_replay_ts"):
            t = float(eng.state["next_replay_ts"])
        else:
            t = trade_start.timestamp()
        end = trade_end.timestamp()
        while t <= end:
            eng.set_replay_time(t)
            eng.detect_stall(ct_of(t))
            eng.step(t)
            t += 60
        if job == "B":
            _flatten_remaining(eng, t)
        eng.state["next_replay_ts"] = t
        eng.state[f"job_{job.lower()}_complete"] = True
        eng.save_state()
        eng.rebuild_journal(force=True)
        eng.log.info(f"=== JOB {job} END equity ${eng.equity():.2f} realized ${eng.state['realized_pnl']:.2f} open {len(eng.state['positions'])} ===")
        return eng

    now = datetime.now(CT)
    eng.note_startup(now)
    eng.save_state()
    while datetime.now(CT) < trade_start:
        now_ct = datetime.now(CT)
        eng.detect_stall(now_ct)
        eng.log.info(f"waiting until {trade_start:%H:%M} CT; now {now_ct:%H:%M:%S}")
        eng.save_state()
        time.sleep(min(60, max(1, (trade_start - datetime.now(CT)).total_seconds())))
    while datetime.now(CT) < trade_end:
        t0 = time.time()
        try:
            now_ct = datetime.now(CT)
            eng.detect_stall(now_ct)
            eng.fetch_live(time.time())
            eng.step(time.time())
            eng.log.info(
                f"loop {eng.state['loops']} ok: equity ${eng.equity():.2f} cash ${eng.state['cash']:.2f} "
                f"open {list(eng.state['positions'])} pending {len(eng.pending)} ({time.time()-t0:.1f}s)"
            )
        except Exception as e:
            eng.state["errors"] += 1
            eng.log.error(f"loop error: {e}\n{traceback.format_exc()}")
        time.sleep(max(5, eng.rules["global"]["poll_seconds"] - (time.time() - t0)))
    if job == "B":
        try:
            eng.fetch_live(time.time())
            eng.step(time.time())
            _flatten_remaining(eng, time.time())
        except Exception as e:
            eng.log.error(f"final flatten error: {e}")
    eng.state[f"job_{job.lower()}_complete"] = True
    eng.save_state()
    eng.rebuild_journal(force=True)
    eng.log.info(f"=== JOB {job} END equity ${eng.equity():.2f} realized ${eng.state['realized_pnl']:.2f} open {len(eng.state['positions'])} ===")
    return eng


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="PAPER-ONLY intraday engine (Yahoo bars, no orders)")
    ap.add_argument("--job", choices=("A", "B"), default="A")
    ap.add_argument("--date", help="session date YYYY-MM-DD (default: today CT)")
    ap.add_argument("--outdir", help="day output directory")
    ap.add_argument("--replay", action="store_true", help="replay --date from Yahoo 1-minute bars")
    args = ap.parse_args()
    sd = date.fromisoformat(args.date) if args.date else datetime.now(CT).date()
    out = args.outdir or os.path.join(BASE, "sessions", sd.isoformat())
    run_session(args.job, sd, out, replay=args.replay)
