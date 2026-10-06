# FPL Insights

Uoffisielt dashboard for Fantasy Premier League med egen xP-modell og lagbygger.
Data hentes fra [Fantasy Premier League](https://fantasy.premierleague.com) en gang i døgnet.
Ikke tilknyttet Premier League.

- `scripts/fetch_data.py` – henter data og skriver `data.json`
- `scripts/build.py` – setter data inn i `src/template.html` → `dist/index.html`
- `.github/workflows/update.yml` – kjører begge hver natt og publiserer via GitHub Pages
