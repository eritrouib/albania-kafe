# Can you draw Albania with its bar-kafe?

**[Read the story](https://etymo.co.uk/albania-kafe/)**

The third in the series after [the UK pubs](https://etymo.co.uk/uk-pubs/) and [the Greek tavernas](https://etymo.co.uk/greek-tavernas/). It maps bar-kafe, restaurants and the traditional byrektore, zgara and qebaptore from OpenStreetMap, looks at what INSTAT publishes, and finds Albania's own Red Lion: "Bar Kafe".

## Data

| Data | Source | Used for |
|---|---|---|
| Every amenity=cafe, bar, pub, restaurant and fast_food in Albania (21 October 2026) | OpenStreetMap via Overpass, © OpenStreetMap contributors (ODbL) | The dot map and the names |
| Enterprises and employment in accommodation and food services, 2016–2024 | [INSTAT Structural Business Statistics](https://www.instat.gov.al/en/themes/industry-trade-and-services/structural-business-statistics/) | Trend |
| Active legal units by activity, 2021–2025 | [INSTAT Business Registers](https://www.instat.gov.al/en/themes/industry-trade-and-services/business-registers/) | Trend |
| Local units by county and activity ("Hotels, Coffee, Restaurants"), 2010 | [INSTAT Economic Enterprises Census](https://www.instat.gov.al/en/themes/censuses/economic-enterprises-census/) | The last count by county |
| Population on 1 January 2026 by county | [INSTAT](https://www.instat.gov.al/en/themes/demography-and-social-indicators/population/) | Per person |
| NUTS 3 boundaries 2021 | Eurostat GISCO via [Nuts2json](https://github.com/eurostat/Nuts2json) | Counties |

## Pipeline

| Script | What it does |
|---|---|
| `01_data.py` | Reads the INSTAT tables, sorts OpenStreetMap places into bar-kafe, restaurants, byrektore/zgara/qebaptore and pizza/fast food, joins them to counties |
| `02_analysis.py` | Names, chains, Italian words, "Bar Kafe" |
| `03_build_site.py` | Writes `docs/data/*.js` and copies `page_template.html` to `docs/index.html` |

The OpenStreetMap file was downloaded from overpass-turbo.eu with:

```
[out:json][timeout:600];
area["ISO3166-1"="AL"][admin_level=2]->.al;
nwr["amenity"~"^(restaurant|cafe|bar|pub|fast_food)$"](area.al);
out center tags;
```

## Limits

- **INSTAT does not count cafés on their own.** They are always together with hotels and restaurants, and the last count by county is from 2010. The "on the map against the last count" chart compares 2026 with 2010 and includes hotels, so it is only a rough guide.
- **OpenStreetMap is uneven.** Shkodër and Kukës are mapped in much more detail than Tirana, Durrës or Fier.
- **Places are sorted by name and tags.** Most bars in Albania are cafés, so bars and pubs are counted as bar-kafe.

---

Made by [Eriola Trungu Impersimi](https://etymo.co.uk) · @ET
