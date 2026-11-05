#!/usr/bin/env python3
"""Builds the legal pages (GitHub Pages, like Fermento) from one fragment per page and language:
legal/src/<page>/<lang>.html → legal/docs/<page>.html with a language switcher.
Run: python3 legal/build.py   (German is the master text; missing languages are reported.)"""
import html, os, sys

here = os.path.dirname(os.path.abspath(__file__))
LANGS = [("de", "Deutsch"), ("en", "English"), ("nl", "Nederlands"), ("fr", "Français"), ("es", "Español"), ("it", "Italiano")]
PAGES = {
    "impressum": {"de": "Impressum", "en": "Legal notice", "nl": "Colofon", "fr": "Mentions légales", "es": "Aviso legal", "it": "Note legali"},
    "privacy": {"de": "Datenschutzerklärung", "en": "Privacy Policy", "nl": "Privacyverklaring", "fr": "Politique de confidentialité", "es": "Política de privacidad", "it": "Informativa sulla privacy"},
    "terms": {"de": "Nutzungsbedingungen", "en": "Terms of Use", "nl": "Gebruiksvoorwaarden", "fr": "Conditions d’utilisation", "es": "Condiciones de uso", "it": "Condizioni d’uso"},
    "support": {"de": "Hilfe & Kontakt", "en": "Help & contact", "nl": "Hulp & contact", "fr": "Aide & contact", "es": "Ayuda y contacto", "it": "Aiuto e contatti"},
}

STYLE = """
  :root { --bg: #F2F2F7; --card: #FFFFFF; --ink: #1C1C1E; --muted: rgba(60,60,67,.62); --line: rgba(60,60,67,.18); --accent: #1F7A3D; --on-accent: #FFFFFF; }
  @media (prefers-color-scheme: dark) { :root { --bg: #000000; --card: #1C1C1E; --ink: #F2F2F7; --muted: rgba(235,235,245,.6); --line: rgba(84,84,88,.6); --accent: #4CC274; --on-accent: #000000; } }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 760px; margin: 0 auto; padding: 32px 20px 80px; line-height: 1.6; color: var(--ink); background: var(--bg); -webkit-text-size-adjust: 100%; }
  header.brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 15px; margin-bottom: 20px; }
  header.brand a { color: var(--ink); text-decoration: none; }
  header.brand .dot { width: 26px; height: 26px; border-radius: 7px; background: var(--accent); display: inline-block; }
  h1 { font-size: 28px; line-height: 1.2; margin: 0 0 4px; letter-spacing: -0.01em; }
  h2 { font-size: 19px; margin-top: 34px; }
  h3 { font-size: 16px; margin: 22px 0 4px; }
  p, li, address { font-size: 16px; }
  .updated { color: var(--muted); font-size: 14px; margin: 0 0 24px; }
  .summary { background: var(--card); border-radius: 16px; padding: 16px 18px; }
  a { color: var(--accent); }
  address { font-style: normal; }
  table { width: 100%; border-collapse: collapse; background: var(--card); border-radius: 14px; overflow: hidden; font-size: 14px; display: block; overflow-x: auto; }
  th, td { text-align: left; vertical-align: top; padding: 10px 12px; border-bottom: 1px solid var(--line); }
  th { font-weight: 600; }
  .langbar { flex-wrap: wrap; gap: 8px; margin: 0 0 28px; padding-bottom: 18px; border-bottom: 1px solid var(--line); font-size: 14px; }
  .langbar a { color: var(--ink); text-decoration: none; padding: 5px 12px; border-radius: 999px; background: var(--card); }
  .langbar a.active { background: var(--accent); color: var(--on-accent); }
  footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--line); font-size: 14px; color: var(--muted); }
  footer a { margin-right: 14px; }
  /* Without JavaScript all language versions stay visible (accessibility). */
  html.js section[data-lang] { display: none; }
  html.js section[data-lang].active { display: block; }
  html.js .langbar { display: flex; }
  html:not(.js) .langbar { display: none; }
"""

SCRIPT = """
  (function () {
    var langs = %s;
    function show(lang) {
      document.querySelectorAll('.langbar a').forEach(function (l) { l.classList.toggle('active', l.dataset.set === lang); });
      document.querySelectorAll('section[data-lang]').forEach(function (s) { s.classList.toggle('active', s.dataset.lang === lang); });
      document.querySelectorAll('footer [data-lang]').forEach(function (s) { s.hidden = s.dataset.lang !== lang; });
      document.documentElement.lang = lang;
    }
    document.querySelectorAll('.langbar a').forEach(function (link) {
      link.addEventListener('click', function (event) {
        event.preventDefault();
        show(link.dataset.set);
        history.replaceState(null, '', '#' + link.dataset.set);
      });
    });
    // Language from the link (#en, ?lang=en, as the app sends it), else the browser language, else German.
    var wanted = (location.hash.slice(1) || new URLSearchParams(location.search).get('lang') || navigator.language || 'de').slice(0, 2).toLowerCase();
    show(langs.indexOf(wanted) >= 0 ? wanted : 'de');
  })();
"""


def footer(available):
    rows = []
    for code, _ in LANGS:
        if code not in available:
            continue
        links = " ".join(f'<a href="{page}.html#{code}">{html.escape(PAGES[page][code])}</a>' for page in PAGES)
        rows.append(f'  <span data-lang="{code}">{links}</span>')
    return "<footer>\n" + "\n".join(rows) + "\n</footer>"


def build_page(page):
    available = [code for code, _ in LANGS if os.path.exists(os.path.join(here, "src", page, f"{code}.html"))]
    if "de" not in available:
        sys.exit(f"{page}: German master text missing")
    sections = []
    for code in available:
        body = open(os.path.join(here, "src", page, f"{code}.html"), encoding="utf-8").read().rstrip()
        active = ' class="active"' if code == "de" else ""
        sections.append(f'<section data-lang="{code}"{active}>\n{body}\n</section>')
    langbar = "\n".join(f'  <a href="#{code}" data-set="{code}"{" class=\"active\"" if code == "de" else ""}>{name}</a>'
                        for code, name in LANGS if code in available)
    title = PAGES[page]["de"]
    out = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light dark">
<title>{html.escape(title)} — Whistlebook</title>
<script>document.documentElement.className += ' js';</script>
<style>{STYLE}</style>
</head>
<body>

<header class="brand"><span class="dot"></span><a href="index.html">Whistlebook</a></header>

<nav class="langbar">
{langbar}
</nav>

{chr(10).join(sections)}

{footer(available)}

<script>{SCRIPT % available}</script>
</body>
</html>
"""
    open(os.path.join(here, "docs", f"{page}.html"), "w", encoding="utf-8").write(out)
    missing = [code for code, _ in LANGS if code not in available]
    return missing


def build_index():
    items = "\n".join(
        f'    <li><a href="{page}.html">{html.escape(PAGES[page]["de"])} <span class="also">{html.escape(PAGES[page]["en"])}</span></a></li>'
        for page in ["support", "impressum", "terms", "privacy"])
    out = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="light dark">
<title>Whistlebook — Rechtliches</title>
<style>{STYLE}
  body {{ max-width: 480px; margin: 72px auto; text-align: center; }}
  ul {{ list-style: none; padding: 0; margin-top: 28px; }}
  li {{ margin: 12px 0; }}
  li a {{ display: inline-block; width: 260px; padding: 12px 20px; border-radius: 14px; background: var(--card); color: var(--ink); text-decoration: none; font-weight: 600; }}
  .also {{ display: block; font-size: 12px; font-weight: 500; color: var(--muted); }}
  p.sub {{ color: var(--muted); font-size: 14px; }}
</style>
</head>
<body>
  <h1>Whistlebook</h1>
  <p class="sub">Die App für Fußball-Schiedsrichter · The app for football referees</p>
  <ul>
{items}
  </ul>
  <p class="sub">Deutsch · English · Nederlands · Français · Español · Italiano</p>
</body>
</html>
"""
    open(os.path.join(here, "docs", "index.html"), "w", encoding="utf-8").write(out)


if __name__ == "__main__":
    os.makedirs(os.path.join(here, "docs"), exist_ok=True)
    report = {page: build_page(page) for page in PAGES}
    build_index()
    for page, missing in report.items():
        print(f"{page}: " + ("all languages" if not missing else "missing " + ", ".join(missing)))
