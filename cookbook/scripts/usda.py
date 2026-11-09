#!/usr/bin/env python3
"""USDA FoodData Central (SR Legacy) helper.

Usage:
  python3 usda.py search <words...>        # find foods by description
  python3 usda.py show <fdc_id>            # show per-100g macros for one food
  python3 usda.py build                    # build data/ingredients.json from data/ingredient_map.yaml

The SR Legacy CSV release must be extracted somewhere; point USDA_DIR at the folder
that holds food.csv / food_nutrient.csv. Download:
  https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip
USDA FoodData Central data is in the public domain (CC0).
"""
import csv
import json
import os
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USDA_DIR = Path(os.environ.get("USDA_DIR", ROOT / ".usda" / "FoodData_Central_sr_legacy_food_csv_2018-04"))
CACHE = USDA_DIR / "_cache.pkl"

# USDA nutrient ids -> our field names (all per 100 g edible portion)
NUTRIENTS = {
    "1008": "kcal",
    "1003": "protein",
    "1004": "fat",
    "1005": "carbs",
    "1079": "fiber",
    "2000": "sugar",
    "1093": "sodium_mg",
}


def load():
    if CACHE.exists():
        return pickle.loads(CACHE.read_bytes())
    foods = {}
    with open(USDA_DIR / "food.csv", newline="") as f:
        for row in csv.DictReader(f):
            foods[row["fdc_id"]] = {"name": row["description"], "n": {}}
    with open(USDA_DIR / "food_nutrient.csv", newline="") as f:
        for row in csv.DictReader(f):
            key = NUTRIENTS.get(row["nutrient_id"])
            if key and row["fdc_id"] in foods:
                foods[row["fdc_id"]]["n"][key] = float(row["amount"])
    CACHE.write_bytes(pickle.dumps(foods))
    return foods


def fmt(fid, food):
    n = food["n"]
    return (f"{fid:>7}  {n.get('kcal', '?'):>6} kcal  P{n.get('protein', '?'):>6}  "
            f"F{n.get('fat', '?'):>6}  C{n.get('carbs', '?'):>6}  Fib{n.get('fiber', '?'):>5}  | {food['name']}")


def search(words):
    foods = load()
    words = [w.lower() for w in words]
    hits = [(fid, f) for fid, f in foods.items() if all(w in f["name"].lower() for w in words)]
    hits.sort(key=lambda x: len(x[1]["name"]))
    for fid, f in hits[:25]:
        print(fmt(fid, f))
    if len(hits) > 25:
        print(f"... {len(hits) - 25} more")


def build():
    import yaml
    foods = load()
    mapping = yaml.safe_load((ROOT / "data" / "ingredient_map.yaml").read_text())
    out = {}
    problems = []
    for key, spec in mapping.items():
        fid = str(spec["fdc_id"])
        if fid not in foods:
            problems.append(f"{key}: fdc_id {fid} not found")
            continue
        food = foods[fid]
        n = dict(food["n"])
        for field in ("kcal", "protein", "fat", "carbs"):
            if field not in n:
                problems.append(f"{key}: missing {field}")
        n.setdefault("fiber", 0.0)
        n.setdefault("sugar", None)
        n.setdefault("sodium_mg", None)
        out[key] = {
            "ar": spec["ar"],
            "fdc_id": int(fid),
            "usda_name": food["name"],
            "per100g": n,
            **({"note": spec["note"]} if spec.get("note") else {}),
        }
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)
    dest = ROOT / "data" / "ingredients.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    print(f"wrote {len(out)} ingredients -> {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    if cmd == "search":
        search(args)
    elif cmd == "show":
        foods = load()
        for a in args:
            print(fmt(a, foods[a]))
    elif cmd == "build":
        build()
    else:
        print(__doc__)
