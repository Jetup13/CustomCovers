import re, html, pathlib

rows = []
for p in sorted(pathlib.Path("covers").glob("*.png")):
    name = re.sub(r"[\(\[].*?[\)\]]", "", p.stem).strip().lower()  # drop (USA), [Disc 1]
    name = re.sub(r"[\s_]+", " ", name)                            # same order as normalizeString
    name = re.sub(r"[^0-9a-z\s]+", "", name)                       # "spyro - year" -> "spyro  year"
    path = f"/Jetup13/CustomCovers/main/psx/covers/{p.name}"
    rows.append(f'<div data-name="{html.escape(name)}" data-boxart="{html.escape(path)}"></div>')

pathlib.Path("index.html").write_text("\n".join(rows), encoding="utf-8")