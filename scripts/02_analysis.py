"""Names and fun facts."""
import os, re, json, unicodedata
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
d = pd.read_csv(os.path.join(PROC, "osm_places.csv"), dtype=str).fillna("")

def plain(x):
    x = unicodedata.normalize("NFD", str(x).lower())
    return "".join(ch for ch in x if unicodedata.category(ch) != "Mn")
d["p"] = d.name.map(plain)
named = d[d.name != ""]
facts = {"n": int(len(d)), "kinds": d.kind.value_counts().to_dict(), "no_name": int((d.name == "").sum())}

# "bar" in the name of places of any kind
facts["bar_in_name"] = int(named.p.str.contains(r"\bbar\b").sum())
facts["bar_kafe_in_name"] = int(named.p.str.contains(r"bar[\s-]*kaf|kafe[\s-]*bar|bar[\s-]*caf").sum())
facts["kafe_word"] = int(named.p.str.contains(r"\bkafe|\bcaf|\bcoffee|\bkafene").sum())

# chains
CHAINS = {"Mulliri i Vjetër": r"mulliri", "Mon Chéri": r"mon ?cheri", "Sophie Caffè": r"sophie", "Bar Kafe (just that)": r"^(bar[\s-]*kafe|kafe[\s-]*bar)$",
          "Komiteti": r"komiteti", "Coffee Address": r"coffee address", "Superbast": r"superbast"}
facts["chains"] = {k: int(named.p.str.contains(v).sum()) for k, v in CHAINS.items()}

# Italian touch
ITAL = r"\b(pizz\w*|picer\w*|caffe|piazza|gusto|mare|bella|dolce|vita|amore|italia\w*|trattoria|osteria|il|la|del|della|da|sapori|vino|ristorante|gelat\w*|pasta)\b"
facts["italian_names"] = int(named.p.str.contains(ITAL).sum())
facts["pizza_names"] = int(named.p.str.contains(r"pizz|picer").sum())

# common names (strip generic words)
GEN = r"\b(bar|kafe|cafe|caffe|coffee|restorant|restaurant|ristorante|pizzeria|pizza|piceri|lounge|byrektore|zgara|taverna|grill|fast food|food|club|pub|bistro|&|and|e|te|i)\b"
base = named.p.str.replace(r"[\"'«»“”().,!/&+-]", " ", regex=True).str.replace(GEN, " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
base = base[base.str.len() > 2]
facts["top_names"] = [[k, int(v), named.loc[base[base == k].index[0], "name"]] for k, v in base.value_counts().head(25).items()]
facts["byrek_names"] = named[named.kind == "byrek"].name.sample(min(15, (named.kind == "byrek").sum()), random_state=2).tolist()
json.dump(facts, open(os.path.join(PROC, "facts.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(facts, ensure_ascii=False, indent=1)[:4000])
