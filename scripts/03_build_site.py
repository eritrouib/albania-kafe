"""Write docs/data/*.js and copy the page."""
import os, json, shutil
import numpy as np, pandas as pd, geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC, DOCS = os.path.join(ROOT, "data", "processed"), os.path.join(ROOT, "docs")
os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
conv = lambda o: o.item() if hasattr(o, "item") else (None if o != o else str(o))
w = lambda name, obj: open(os.path.join(DOCS, "data", name + ".js"), "w", encoding="utf-8").write(
    f"window.AL=window.AL||{{}};window.AL.{name}=" + json.dumps(obj, separators=(",", ":"), ensure_ascii=False, default=conv) + ";\n")

d = pd.read_csv(os.path.join(PROC, "osm_places.csv"), dtype=str).fillna("")
K = {"kafe": 0, "byrek": 1, "restorant": 2, "pizza": 3}
d["k"] = d.kind.map(K)
d = d.sort_values("k", ascending=False)
w("points", {"lat": (d.lat.astype(float) * 1e5).round().astype(int).tolist(), "lon": (d.lon.astype(float) * 1e5).round().astype(int).tolist(),
             "k": d.k.astype(int).tolist(), "n": d.name.tolist(), "c": d.city.tolist()})
t = pd.read_csv(os.path.join(PROC, "counties.csv")).set_index("county")
g = gpd.read_file(os.path.join(PROC, "counties.geojson"))
g["geometry"] = g.geometry.simplify(0.002, preserve_topology=True)
gj = json.loads(g.to_json())
for f in gj["features"]:
    c = f["properties"]["county"]; r = t.loc[c]
    f["properties"] = {"county": c, **{k: (round(float(r[k]), 4) if isinstance(r[k], (float, np.floating)) else r[k]) for k in ["hcr2010", "pop2026", "kafe", "restorant", "byrek", "pizza", "osm_all", "kafe_per10k", "osm_per10k", "cov2010"]}}
w("counties", gj)
facts = json.load(open(os.path.join(PROC, "facts.json"), encoding="utf-8"))
facts["national"] = json.load(open(os.path.join(PROC, "national.json")))
facts["pop2026"] = int(t.pop2026.sum()); facts["hcr2010"] = int(t.hcr2010.sum())
w("facts", facts)
shutil.copy(os.path.join(ROOT, "scripts", "page_template.html"), os.path.join(DOCS, "index.html"))
for f in sorted(os.listdir(os.path.join(DOCS, "data"))): print(f, round(os.path.getsize(os.path.join(DOCS, "data", f)) / 1e6, 2), "MB")
