// Cloudflare Worker: henter et FPL-lag (picks) slik at nettsiden kan lese det.
// FPL sitt API tillater ikke kall direkte fra andre nettsider (CORS), så denne sender det videre.
// Bruk: GET https://<worker>/?entry=1234567
const ALLOWED = ['https://fredrikn89-create.github.io', 'http://localhost', 'http://127.0.0.1'];
const API = 'https://fantasy.premierleague.com/api/';

export default {
  async fetch(req) {
    const origin = req.headers.get('Origin') || '';
    const ok = ALLOWED.some(a => origin === a || origin.startsWith(a + ':'));
    const cors = {
      'Access-Control-Allow-Origin': ok ? origin : ALLOWED[0],
      'Vary': 'Origin',
      'Content-Type': 'application/json; charset=utf-8',
    };
    const out = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers: cors });
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    const id = new URL(req.url).searchParams.get('entry') || '';
    if (!/^\d{1,9}$/.test(id)) return out({ error: 'Ugyldig lag-ID' }, 400);
    const get = async path => fetch(API + path, {
      headers: { 'User-Agent': 'Mozilla/5.0 fpl-insights' },
      cf: { cacheTtl: 120, cacheEverything: true },
    });
    const er = await get(`entry/${id}/`);
    if (er.status === 404) return out({ error: 'Fant ikke laget' }, 404);
    if (!er.ok) return out({ error: 'FPL svarte ikke' }, 502);
    const entry = await er.json();
    for (let gw = entry.current_event; gw >= 1 && gw > entry.current_event - 3; gw--) {
      const pr = await get(`entry/${id}/event/${gw}/picks/`);
      if (!pr.ok) continue;
      const d = await pr.json();
      return out({
        gw,
        name: entry.name,
        picks: d.picks.map(p => ({ e: p.element, pos: p.position, c: p.is_captain, v: p.is_vice_captain })),
        value: (d.entry_history.value + d.entry_history.bank) / 10,
      });
    }
    return out({ error: 'Fant ingen lagvalg ennå' }, 404);
  },
};
