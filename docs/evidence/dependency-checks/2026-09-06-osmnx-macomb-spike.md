# OSMnx dependency spike — 2026-09-06

**What was tested:** does a real city's road graph load via OSMnx and
route correctly, per the Get gate for Candidate C (Disaster Response
Coordination)?

**Place:** Macomb, Illinois, USA (`network_type="drive"`)

**Result:**
- Graph loaded: 641 nodes, 1804 edges, 1.2s (cached run; first cold run
  was 7.3s)
- Routed McDonald's → Chick-fil-A (two real, OSM-tagged businesses in
  Macomb): 28-node route, 3413m (2.12 mi), computed in 0.008s
- Business-name geocoding via `ox.geocode()` failed for two originally
  requested points ("Taco Bell, Macomb, IL" and "Dad's Garage, Macomb,
  IL") — Nominatim's plain geocoder wants structured addresses, not
  business names, and neither point is tagged in OSM as a business
  (Macomb has no mapped Taco Bell; "Dad's Garage" isn't a public
  business). Switched to `ox.features_from_place()` POI search instead,
  which found 13 real fast-food businesses in the area (Subway,
  Chick-fil-A, KFC, McDonald's ×2, Burger King, Wendy's, Jimmy John's,
  Dairy Queen, Dunkin', Arby's) — confirms OSM's data coverage for this
  town is solid, the two specific misses were just unmapped/nonexistent
  points, not a data-quality problem.

**Verdict: PASS.** The road network loads, is routable, and returns
sane results, for a real town at the scale this project needs.

**Tool:** OSMnx 2.1.1, run locally, no API key/account.
