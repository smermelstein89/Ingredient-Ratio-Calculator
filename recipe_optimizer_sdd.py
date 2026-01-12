#!/usr/bin/env python3
import json
import os
import string

RECIPE_FILE = "recipes.json"
FLOUR_HINTS = ["flour"]
LIQUID_HINTS = ["water", "milk"]


def load_recipes():
    if not os.path.exists(RECIPE_FILE):
        return {}
    try:
        with open(RECIPE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_recipes(recipes):
    with open(RECIPE_FILE, "w", encoding="utf-8") as f:
        json.dump(recipes, f, indent=2)


def detect_ingredient(keys, hints):
    for k in keys:
        for h in hints:
            if h in k.lower():
                return k
    return None


def get_float(prompt, allow_blank=False, blank_value=None, min_value=0):
    while True:
        s = input(prompt).strip()
        if allow_blank and s == "":
            return blank_value
        try:
            v = float(s)
            if v < min_value:
                print("Value too small.")
                continue
            return v
        except ValueError:
            print("Invalid number, try again.")


def print_recipe(name, recipe):
    print(f"\n=== {name} ===")
    print(f"Base servings: {recipe['servings']}")
    for ing, amt in recipe["ingredients"].items():
        print(f"  - {ing}: {amt:.3g} per serving")
    print()


def recipe_menu(recipes):
    print("\nRecipes:")
    if not recipes:
        print("  (none)")
        return {}
    mapping = {}
    for l, name in zip(string.ascii_uppercase, recipes.keys()):
        print(f"  {l}) {name}")
        mapping[l] = name
    return mapping


def apply_sdd(amounts, sdd):
    flour = detect_ingredient(amounts.keys(), FLOUR_HINTS)
    liquid = detect_ingredient(amounts.keys(), LIQUID_HINTS)
    warnings = []

    flour_red = 0.5 * sdd
    liquid_red = 0.5 * sdd

    if flour:
        if flour_red > amounts[flour]:
            warnings.append("SDD exceeds flour; flour reduced to 0")
        amounts[flour] = max(0, amounts[flour] - flour_red)

    if liquid:
        if liquid_red > amounts[liquid]:
            warnings.append("SDD exceeds liquid; liquid reduced to 0")
        amounts[liquid] = max(0, amounts[liquid] - liquid_red)

    amounts["sdd"] = sdd
    return amounts, flour, warnings


def hydration(amounts, flour):
    if flour and amounts.get(flour, 0) > 0:
        liquid_total = sum(
            v for k, v in amounts.items()
            if any(h in k.lower() for h in LIQUID_HINTS)
        )
        return 100 * liquid_total / amounts[flour]
    return None


def create_recipe():
    recipes = load_recipes()
    name = input("Recipe name: ").strip()
    if not name or name in recipes:
        print("Invalid or duplicate name.")
        return

    servings = get_float("Servings: ", min_value=0.0001)
    ingredients = {}

    print("Add ingredients (ENTER to finish)")
    while True:
        ing = input("Ingredient name: ").strip()
        if not ing:
            break
        if ing in ingredients:
            print("Already added.")
            continue
        amt = get_float(f"Total amount of {ing}: ")
        ingredients[ing] = amt / servings

    recipes[name] = {"servings": servings, "ingredients": ingredients}
    save_recipes(recipes)
    print("Saved.")
    print_recipe(name, recipes[name])


def optimize_recipe(name):
    recipes = load_recipes()
    recipe = recipes[name]
    ratios = recipe["ingredients"]

    print_recipe(name, recipe)

    print("1) Maximize")
    print("2) Target servings")
    mode = input("Choose [1]: ").strip() or "1"

    use_sdd = input("Use SDD? [y/N]: ").strip().lower() == "y"
    sdd = get_float("SDD amount: ", min_value=0) if use_sdd else 0

    if mode == "2":
        servings = get_float("Target servings: ", min_value=0.0001)
        amounts = {k: v * servings for k, v in ratios.items()}
        if use_sdd:
            amounts, flour, warnings = apply_sdd(amounts, sdd)
        else:
            flour = detect_ingredient(amounts.keys(), FLOUR_HINTS)
            warnings = []

        print("Amounts:")
        for k, v in amounts.items():
            print(f"  - {k}: {v:.3g}")

        h = hydration(amounts, flour)
        if h:
            print(f"Hydration: {h:.1f}%")
        for w in warnings:
            print("Warning:", w)
        return

    available = {}
    for ing in ratios:
        available[ing] = get_float(
            f"{ing} you have (ENTER = inf): ",
            allow_blank=True,
            blank_value=float("inf"),
        )

    servings = min(available[k] / ratios[k] for k in ratios)
    amounts = {k: v * servings for k, v in ratios.items()}

    flour = detect_ingredient(amounts.keys(), FLOUR_HINTS)
    warnings = []
    if use_sdd:
        amounts, flour, warnings = apply_sdd(amounts, sdd)

    print("Max servings:", round(servings, 3))
    print("Amounts:")
    for k, v in amounts.items():
        print(f"  - {k}: {v:.3g}")

    h = hydration(amounts, flour)
    if h:
        print(f"Hydration: {h:.1f}%")
    for w in warnings:
        print("Warning:", w)


def menu():
    while True:
        recipes = load_recipes()
        m = recipe_menu(recipes)
        print("\n1) Create recipe\n2) Optimize recipe\n3) Exit")
        c = input("Choose: ").strip().upper()
        if c in m:
            print_recipe(m[c], recipes[m[c]])
        elif c == "1":
            create_recipe()
        elif c == "2":
            if not m:
                print("No recipes.")
                continue
            r = input("Recipe letter: ").strip().upper()
            if r in m:
                optimize_recipe(m[r])
        elif c == "3":
            break
        else:
            print("Invalid.")


if __name__ == "__main__":
    menu()
