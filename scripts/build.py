#!/usr/bin/env python3
"""Setter data.json inn i src/template.html og skriver dist/index.html."""
import json, os
from datetime import datetime
from zoneinfo import ZoneInfo

MONTHS = ["januar","februar","mars","april","mai","juni","juli","august",
          "september","oktober","november","desember"]
now = datetime.now(ZoneInfo("Europe/Oslo"))
stamp = f"{now.day}. {MONTHS[now.month-1]} {now.year} kl. {now:%H:%M}"

data = json.load(open("data.json", encoding="utf-8"))
html = open("src/template.html", encoding="utf-8").read()
html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
html = html.replace("__UPDATED__", stamp)
os.makedirs("dist", exist_ok=True)
open("dist/index.html", "w", encoding="utf-8").write(html)
open("dist/.nojekyll", "w").close()
print("Bygget dist/index.html –", stamp)
