#!/usr/bin/env python3
"""America/Chicago session guard for the paper engine.

GitHub Actions cron is UTC and can fire late. The workflow schedules both the
CDT (UTC-5) and CST (UTC-6) instants that correspond to the Chicago clock.
This module rejects the off-season duplicate and weekends/NYSE holidays, and
warns when a job actually starts after its entry window has opened.
"""
from datetime import datetime, date, time
from pathlib import Path
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")

# All clock tuples are (hour, minute) in America/Chicago.
JOBS = {
    "A": {
        "nominal_start": (7, 50),
        "trade_start": (8, 20),
        "trade_end": (11, 30),
        # 07:40 rejects the CST-season duplicate of the CDT cron (~06:50 CT).
        "earliest": (7, 40),
        # 11:30 rejects a duplicate that was queued behind the real morning job.
        "latest": (11, 30),
    },
    "B": {
        "nominal_start": (11, 25),
        "trade_start": (11, 25),
        "trade_end": (15, 0),
        "flatten": (14, 55),
        "earliest": (11, 15),
        "latest": (15, 0),
    },
}


def load_holidays(path):
    hol = set()
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        hol.add(line.split()[0])
    return hol


def trading_day_reason(day, holidays):
    """Return '' if NYSE should be open, else a short skip reason."""
    if isinstance(day, datetime):
        day = day.date()
    if day.weekday() >= 5:
        return "weekend"
    if day.isoformat() in holidays:
        return "NYSE holiday"
    return ""


def _hm(dt):
    return (dt.hour, dt.minute)


def in_start_window(job, now_ct):
    """True when a live start at now_ct should run this job (not the other UTC offset)."""
    spec = JOBS[job]
    t = _hm(now_ct.astimezone(CT))
    if t < spec["earliest"]:
        h, m = spec["earliest"]
        return False, f"before Job {job} earliest start {h:02d}:{m:02d} CT"
    if t >= spec["latest"]:
        h, m = spec["latest"]
        return False, f"at or after Job {job} latest start {h:02d}:{m:02d} CT"
    return True, ""


def late_start_warning(job, now_ct):
    """Warning text when the job starts after its entry window opened, else None."""
    now_ct = now_ct.astimezone(CT)
    spec = JOBS[job]
    if _hm(now_ct) > spec["trade_start"]:
        h, m = spec["trade_start"]
        return (
            f"STARTUP: Job {job} started at {now_ct:%Y-%m-%d %H:%M:%S %Z}, "
            f"after its entry window opened at {h:02d}:{m:02d} CT. "
            "No backfill of missed entry windows."
        )
    return None


def missed_windows_for_job(job, rules, now_ct):
    """Enabled rules whose window overlaps this job and has fully closed.

    A window that ended before the job's own trade_start is not charged to
    this job (Job B must not flag the morning R8 window).
    """
    now_ct = now_ct.astimezone(CT)
    t = _hm(now_ct)
    spec = JOBS[job]
    job_start = spec["trade_start"]
    job_end = spec["trade_end"]
    missed = []
    for rid, rule in (rules or {}).items():
        if not isinstance(rule, dict) or not rule.get("enabled"):
            continue
        win = rule.get("window_ct")
        if not win or len(win) != 2:
            continue
        start = tuple(int(x) for x in win[0].split(":"))
        end = tuple(int(x) for x in win[1].split(":"))
        if end < job_start or start >= job_end:
            continue
        if t > end:
            missed.append(rid)
    return missed


def combine_ct(day, hm):
    return datetime.combine(day, time(hm[0], hm[1]), tzinfo=CT)


def guard_live_start(job, now_ct, holidays, done_marker):
    """Decide whether a live (non-replay) invocation should run.

    Returns (action, message) where action is 'run', 'skip'.
    """
    now_ct = now_ct.astimezone(CT)
    reason = trading_day_reason(now_ct.date(), holidays)
    if reason:
        return "skip", f"SKIP: {now_ct.date()} is a {reason}. No session."
    if done_marker and Path(done_marker).exists():
        return "skip", f"SKIP: Job {job} already finished ({done_marker})."
    ok, why = in_start_window(job, now_ct)
    if not ok:
        return "skip", f"SKIP: Chicago clock {now_ct:%H:%M} is {why}. Off-season cron or session closed."
    warn = late_start_warning(job, now_ct)
    if warn:
        return "run", warn
    return "run", f"OK: Job {job} starting at {now_ct:%H:%M} CT inside its window."
