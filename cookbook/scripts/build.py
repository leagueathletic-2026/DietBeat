#!/usr/bin/env python3
"""Build the DietBeat cookbook: recipes/*.yaml -> output/book.html (+ PDF via scripts/pdf.js).

  python3 scripts/build.py            # validate, compute nutrition, render HTML
  python3 scripts/build.py --check    # validate + print nutrition table only
"""
import json
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

# Ingredients that make a recipe non-vegetarian.
ANIMAL_FLESH = {
    "chicken_breast", "chicken_thigh", "beef_lean_ground", "beef_ground_90", "beef_lean",
    "beef_liver", "lamb_lean", "turkey_ground", "salmon", "tilapia", "cod", "sea_bass",
    "mullet", "mackerel", "tuna_water", "sardine_oil", "shrimp", "chicken_broth", "gelatin",
}

# Tag rules (per serving). Documented for readers in content/intro.yaml -> "tags" section.
CAL_LIMIT = {"breakfast": 400, "main": 500, "side": 300, "snack": 200, "dessert": 200}
TAGS = {
    "light":   {"ar": "تخسيس",        "cls": "t-light"},
    "protein": {"ar": "بروتين عالي",   "cls": "t-protein"},
    "keto":    {"ar": "كيتو / لو كارب", "cls": "t-keto"},
    "fiber":   {"ar": "غني بالألياف",  "cls": "t-fiber"},
    "veg":     {"ar": "نباتي",         "cls": "t-veg"},
}

AR_DIGITS = str.maketrans("0123456789.", "٠١٢٣٤٥٦٧٨٩٫")


def ar(n):
    """Format a number with Arabic-Indic digits."""
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    return str(n).translate(AR_DIGITS)


def md(text):
    """Escape text and turn **bold** into <strong>."""
    import re
    from markupsafe import Markup, escape
    return Markup(re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(escape(text))))


def load_ingredients():
    return json.loads((ROOT / "data" / "ingredients.json").read_text())


def compute(recipe, ingredients, kind):
    total = {k: 0.0 for k in ("kcal", "protein", "fat", "carbs", "fiber", "sugar", "sodium_mg")}
    lines = []
    for item in recipe["ingredients"]:
        key, grams, *rest = item
        qty = rest[0] if len(rest) > 0 else None
        name = rest[1] if len(rest) > 1 else None
        if key not in ingredients:
            raise SystemExit(f"[{recipe['id']}] unknown ingredient '{key}'")
        ing = ingredients[key]
        for k in total:
            v = ing["per100g"].get(k)
            if v is not None:
                total[k] += v * grams / 100.0
        lines.append({"name": name or ing["ar"], "qty": qty, "grams": grams})
    s = recipe["servings"]
    per = {k: v / s for k, v in total.items()}
    net_carbs = max(per["carbs"] - per["fiber"], 0)
    # Energy split from 4/4/9 kcal per gram so the three shares add up to 100%.
    e = {"protein": per["protein"] * 4, "carbs": per["carbs"] * 4, "fat": per["fat"] * 9}
    e_total = sum(e.values()) or 1
    split = {k: round(v / e_total * 100) for k, v in e.items()}
    split["carbs"] = 100 - split["protein"] - split["fat"]
    keys = {i[0] for i in recipe["ingredients"]}
    tags = []
    if per["kcal"] <= CAL_LIMIT[kind]:
        tags.append("light")
    if per["protein"] >= 30 or (per["protein"] >= 15 and split["protein"] >= 30):
        tags.append("protein")
    if net_carbs <= 10:
        tags.append("keto")
    if per["fiber"] >= 6:
        tags.append("fiber")
    if not keys & ANIMAL_FLESH:
        tags.append("veg")
    nut = {
        "kcal": round(per["kcal"]),
        "protein": round(per["protein"]),
        "carbs": round(per["carbs"]),
        "fat": round(per["fat"]),
        "fiber": round(per["fiber"]),
        "sugar": round(per["sugar"]),
        "net_carbs": round(net_carbs),
        "sodium": int(round(per["sodium_mg"] / 10.0) * 10),
        "split": split,
    }
    return lines, nut, tags


def load_book():
    ingredients = load_ingredients()
    chapters = []
    seen = set()
    n = 0
    for path in sorted((ROOT / "recipes").glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        ch = data["chapter"]
        ch["recipes"] = []
        ch["no"] = len(chapters) + 1
        for r in data.get("recipes") or []:
            if r["id"] in seen:
                raise SystemExit(f"duplicate recipe id {r['id']}")
            seen.add(r["id"])
            n += 1
            kind = r.get("kind", ch["kind"])
            lines, nut, tags = compute(r, ingredients, kind)
            img = ROOT / "images" / f"{r['id']}.jpg"
            ch["recipes"].append({
                **r,
                "num": n,
                "lines": lines,
                "nut": nut,
                "tags": [dict(TAGS[t], key=t) for t in tags],
                "image": f"../images/{r['id']}.jpg" if img.exists() else None,
            })
        chapters.append(ch)
    return chapters, n


INDEX_ROWS_PER_PAGE = 29


def paginate(chapters, intro):
    """Lay out every printed page in order so the index can show real page numbers.
    Every entry here renders as exactly one A4 page (the CSS clips overflow)."""
    pages = [{"type": "cover"}]
    pages += [{"type": "text", **p} for p in intro["pages"]]

    rows = []
    for ch in chapters:
        rows.append({"chapter": ch})
        rows += [{"recipe": r} for r in ch["recipes"]]
    chunks = [rows[i:i + INDEX_ROWS_PER_PAGE] for i in range(0, len(rows), INDEX_ROWS_PER_PAGE)]
    for i, chunk in enumerate(chunks):
        pages.append({"type": "index", "rows": chunk, "first": i == 0})

    for ch in chapters:
        pages.append({"type": "chapter", "chapter": ch})
        for r in ch["recipes"]:
            pages.append({"type": "recipe", "recipe": r, "chapter": ch})
    pages.append({"type": "references", "refs": intro["references"], "disclaimer": intro["disclaimer"]})

    for i, p in enumerate(pages, start=1):
        p["no"] = i
        if p["type"] == "chapter":
            p["chapter"]["page"] = i
        elif p["type"] == "recipe":
            p["recipe"]["page"] = i
    return pages


def main():
    chapters, n = load_book()
    if "--check" in sys.argv:
        for ch in chapters:
            print(f"\n== {ch['title']} ({len(ch['recipes'])})")
            for r in ch["recipes"]:
                x = r["nut"]
                print(f"{r['num']:>3} {r['id']:<5} {x['kcal']:>4} kcal  P{x['protein']:>3} C{x['carbs']:>3} "
                      f"F{x['fat']:>3} Fib{x['fiber']:>3}  {','.join(t['key'] for t in r['tags']):<28} {r['name']}")
        print(f"\nTotal recipes: {n}")
        return
    intro = yaml.safe_load((ROOT / "content" / "intro.yaml").read_text())
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
    env.filters["ar"] = ar
    env.filters["md"] = md
    pages = paginate(chapters, intro)
    html = env.get_template("book.html.j2").render(
        pages=pages, chapters=chapters, total=n, intro=intro, tags=TAGS,
        css=(ROOT / "templates" / "style.css").read_text())
    OUT.mkdir(exist_ok=True)
    (OUT / "book.html").write_text(html)
    print(f"Rendered {n} recipes -> output/book.html")


if __name__ == "__main__":
    main()
