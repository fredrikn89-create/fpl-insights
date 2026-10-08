#!/usr/bin/env python3
"""Henter data fra Fantasy Premier League sitt offentlige API og skriver data.json.

Bruker kun standardbiblioteket. Kjøres én gang i døgnet, med pause mellom kallene.
"""
import json, sys, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

BASE = "https://fantasy.premierleague.com/api/"
UA = "FPL-Insights/1.0 (uoffisiell hobbyside; henter data en gang i døgnet)"
DELAY = 0.3
DECAY = 0.8          # nyere kamper teller mer: vekt = 0.8^(antall runder siden)
HORIZON = 6          # antall kommende runder i kampprogrammet


def get(path):
    for attempt in range(4):
        try:
            req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt * 2)
    raise RuntimeError("unreachable")


def main(out="data.json"):
    b = get("bootstrap-static/")
    events = b["events"]
    finished = [e["id"] for e in events if e.get("finished")]
    cur = max(finished) if finished else 0
    nxt = next((e for e in events if e.get("is_next")), None)
    if nxt is None:
        raise SystemExit("Fant ingen kommende runde (sesongen ferdig?)")
    last = next((e for e in events if e["id"] == cur), {}) if cur else {}

    teams = [[t["id"], t["name"], t["short_name"]] for t in b["teams"]]

    fixtures = get("fixtures/?future=1")
    fx = sorted(
        ([f["event"], f["team_h"], f["team_a"], f["team_h_difficulty"], f["team_a_difficulty"]]
         for f in fixtures
         if f.get("event") and nxt["id"] <= f["event"] < nxt["id"] + HORIZON),
        key=lambda r: (r[0], r[1]))

    def num(x, nd=2):
        return round(float(x), nd) if x not in (None, "") else 0

    players, dct, rw, l5, pc = [], {}, {}, {}, {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    pool = [e for e in b["elements"]
            if e["minutes"] >= 90 or float(e["selected_by_percent"]) >= 2]
    pool.sort(key=lambda e: e["id"])
    for n, e in enumerate(pool, 1):
        players.append([
            e["id"], e["web_name"], e["team"], e["element_type"], e["now_cost"],
            e["total_points"], e["event_points"], num(e["form"], 1),
            num(e["selected_by_percent"], 1), e["minutes"], e["starts"],
            e["goals_scored"], e["assists"], e["clean_sheets"], e["goals_conceded"],
            e["bonus"], e["saves"], e["defensive_contribution"],
            num(e["expected_goals"]), num(e["expected_assists"]),
            num(e["expected_goals_conceded"]), e["status"],
            e["chance_of_playing_next_round"], e["transfers_in_event"],
            e["transfers_out_event"], num(e["ep_next"], 1), e["penalties_order"],
        ])
        if cur == 0:
            continue
        time.sleep(DELAY)
        hist = get(f"element-summary/{e['id']}/")["history"]
        thr = 10 if e["element_type"] == 2 else 12
        played = hit = last5 = 0
        wm = wxg = wxa = wb = ws = wst = wsum = 0.0
        for m in hist:
            if m["round"] > cur:
                continue
            w = DECAY ** (cur - m["round"])
            wsum += w
            if m["minutes"] > 0:
                played += 1
                if m["round"] > cur - 5:
                    last5 += 1
                if m["defensive_contribution"] >= thr:
                    hit += 1
            wm += w * m["minutes"]
            wxg += w * float(m["expected_goals"] or 0)
            wxa += w * float(m["expected_assists"] or 0)
            wb += w * m["bonus"]
            ws += w * m["saves"]
            wst += w * m["starts"]
        l5[str(e["id"])] = last5
        # prisendring (i tideler av £m): totalt siden sesongstart, og siden for 30 dager siden
        start = e["now_cost"] - e["cost_change_start"]
        ref = start
        for m in hist:
            ko = m.get("kickoff_time")
            if ko and datetime.fromisoformat(ko.replace("Z", "+00:00")) <= cutoff:
                ref = m["value"]
        pc[str(e["id"])] = [e["cost_change_start"], e["now_cost"] - ref]
        if e["element_type"] != 1:
            dct[str(e["id"])] = [hit, played]
        rw[str(e["id"])] = [round(wm, 1), round(wxg, 3), round(wxa, 3),
                            round(wb, 2), round(ws, 2), round(wst, 2), round(wsum, 2)]
        if n % 50 == 0:
            print(f"  {n}/{len(pool)} spillere", file=sys.stderr)

    data = {
        "gw": cur,
        "next": {"id": nxt["id"], "deadline": nxt["deadline_time"]},
        "avg": last.get("average_entry_score") or 0,
        "highest": last.get("highest_score") or 0,
        "teams": teams, "fx": fx, "players": players, "dct": dct, "rw": rw, "l5": l5, "pc": pc,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"OK: GW{cur}, {len(players)} spillere, {len(fx)} kamper", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:])
