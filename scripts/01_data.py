"""INSTAT tables, county boundaries and OpenStreetMap places for Albania.

INSTAT publishes cafés, bars and restaurants only inside "Accommodation and food services" (NACE 55+56),
nationally. The last count by county that separates "hotels, cafés, restaurants" is the 2010 enterprise census.
"""
import os, re, json, unicodedata
import pandas as pd, geopandas as gpd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, PROC = os.path.join(ROOT, "data", "raw"), os.path.join(ROOT, "data", "processed")
COUNTY = {"Berat": "AL031", "Dibër": "AL011", "Durrës": "AL012", "Elbasan": "AL021", "Fier": "AL032", "Gjirokastër": "AL033",
          "Korçë": "AL034", "Kukës": "AL013", "Lezhë": "AL014", "Shkodër": "AL015", "Tiranë": "AL022", "Vlorë": "AL035"}

# ---- national series ----
s = pd.read_excel(os.path.join(RAW, "instat", "sbs2.xlsx"), header=None)
years = [int(float(v)) for v in s.iloc[6, 3:12]]
row = s[s[1].astype(str).str.strip() == "55; 56"].iloc[0]
sbs = pd.DataFrame({"year": years, "enterprises": [round(float(v)) for v in row[3:12]], "employed": [round(float(v)) for v in row[12:21]]})
b = pd.read_excel(os.path.join(RAW, "instat", "br_activity_size.xlsx"), header=None)
br, yr = [], None
for _, r in b.iterrows():
    m = re.search(r"(20\d\d)", str(r[1]))
    if "Gjendje" in str(r[1]) and m: yr = int(m.group(1))
    if "Akomodimi" in str(r[1]) and yr and not any(x[0] == yr for x in br): br.append((yr, int(r[2])))
br = pd.DataFrame(br, columns=["year", "active_legal_units"])
nat = {"sbs": sbs.to_dict("records"), "register": br.to_dict("records")}
json.dump(nat, open(os.path.join(PROC, "national.json"), "w"), indent=1)
print(sbs.to_string(index=False)); print(br.to_string(index=False))

# ---- 2010 census: hotels, cafés, restaurants (local units) by county ----
c = pd.read_excel(os.path.join(RAW, "instat", "census_tab18.xls"), header=None)
c = c[c[0].astype(str).str.strip().isin(COUNTY)].drop_duplicates(subset=[0], keep="first")   # second block is percentages
cen = pd.DataFrame({"county": c[0].str.strip(), "hcr2010": c[8].astype(int).values}).set_index("county")

# ---- population ----
p = pd.read_excel(os.path.join(RAW, "instat", "pop_qark.xlsx"), header=None)
p = p[p[0].astype(str).str.strip().isin(COUNTY)]
pop = pd.DataFrame({"county": p[0].str.strip(), "pop2026": p[9].astype(int).values}).set_index("county")

# ---- boundaries ----
g = gpd.read_file(os.path.join(RAW, "bounds", "nutsrg_3.json"))
g = g[g.id.str.startswith("AL")].rename(columns={"id": "code"})[["code", "geometry"]]
inv = {v: k for k, v in COUNTY.items()}
g["county"] = g.code.map(inv)

# ---- OSM ----
def plain(x):
    x = unicodedata.normalize("NFD", str(x or "").lower())
    return "".join(ch for ch in x if unicodedata.category(ch) != "Mn")
TRAD = re.compile(r"byrek|zgar|zgare|qebap|sufllaq|lakror|pite\b|petull|mengjezor|fergese|tave\b|gjel deti")
PIZZA = re.compile(r"pizz|picer|burger|fast|snack|kebab|hot ?dog|chicken|crepe|sandwich|panini")
rows = []
for f in json.load(open(os.path.join(RAW, "osm", "albania_overpass.geojson"), encoding="utf-8"))["features"]:
    t = f["properties"]; lon, lat = f["geometry"]["coordinates"]; am = t.get("amenity")
    name = (t.get("name") or t.get("name:sq") or t.get("name:en") or "").strip()
    txt = plain(" ".join(str(t.get(k, "")) for k in ["name", "name:sq", "name:en", "cuisine"]))
    if TRAD.search(txt): kind = "byrek"
    elif am in ("cafe", "bar", "pub"): kind = "kafe"
    elif am == "restaurant" and not PIZZA.search(txt): kind = "restorant"
    else: kind = "pizza"
    rows.append(dict(id=t.get("@id"), amenity=am, kind=kind, name=name, cuisine=t.get("cuisine", ""), city=t.get("addr:city", ""), lat=lat, lon=lon))
d = pd.DataFrame(rows)
gd = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326)
gd = gpd.sjoin(gd, g[["county", "geometry"]], how="left", predicate="within").drop(columns="index_right")
miss = gd.county.isna()
if miss.any():
    n = gpd.sjoin_nearest(gd[miss].drop(columns="county").to_crs(6870), g[["county", "geometry"]].to_crs(6870), how="left", max_distance=3000)
    n = n[~n.index.duplicated()]; gd.loc[n.index, "county"] = n.county.values
print("outside:", gd.county.isna().sum())
gd = gd.dropna(subset=["county"])
pd.DataFrame(gd.drop(columns="geometry")).to_csv(os.path.join(PROC, "osm_places.csv"), index=False)
print(gd.kind.value_counts().to_dict())

cnt = gd.pivot_table(index="county", columns="kind", aggfunc="size", fill_value=0)
t = cen.join(pop).join(cnt)
t["osm_all"] = cnt.sum(axis=1)
t["kafe_per10k"] = t.kafe / t.pop2026 * 1e4
t["osm_per10k"] = t.osm_all / t.pop2026 * 1e4
t["cov2010"] = t.osm_all / t.hcr2010
t["code"] = t.index.map(COUNTY)
t.reset_index().to_csv(os.path.join(PROC, "counties.csv"), index=False)
g.merge(t.reset_index()[["county"]], on="county").to_file(os.path.join(PROC, "counties.geojson"), driver="GeoJSON", COORDINATE_PRECISION=4)
pd.set_option("display.width", 200)
print(t.round(2).to_string())
print("pop", t.pop2026.sum(), "census 2010 HCR", t.hcr2010.sum())
