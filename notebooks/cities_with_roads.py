from neo4j import GraphDatabase
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np

# ── Neo4j connection ─────────────────────────────────────────────────────────
uri = "bolt://localhost:7687"          # ← your URI
username = ""
password = ""

driver = GraphDatabase.driver(uri, auth=(username, password))

# 1. Get all cities with coordinates + unique id (for matching)
cities_query = """
MATCH (c:City)
WHERE c.latitude IS NOT NULL AND c.longitude IS NOT NULL
RETURN id(c) AS id, c.latitude AS lat, c.longitude AS lon, c.name AS name
"""

# 2. Get ROAD_TO relationships (assuming directed, change to -[]- if undirected)
roads_query = """
MATCH (c1:City)-[r:ROAD_TO]->(c2:City)
RETURN id(c1) AS start_id, id(c2) AS end_id
"""

city_data = {}
with driver.session() as session:
    # Cities
    result = session.run(cities_query)
    for record in result:
        city_data[record["id"]] = {
            "lat": record["lat"],
            "lon": record["lon"],
            "name": record["name"] or "?"
        }

    # Roads (list of (start_id, end_id))
    roads = []
    result = session.run(roads_query)
    for record in result:
        start = record["start_id"]
        end   = record["end_id"]
        if start in city_data and end in city_data:
            roads.append((start, end))

driver.close()

print(f"Found {len(city_data):,} cities and {len(roads):,} ROAD_TO relationships")

# ── Create France-focused map ────────────────────────────────────────────────
plt.figure(figsize=(12, 14))

m = Basemap(
    projection='lcc',
    lat_1=44, lat_2=50,
    lat_0=46.5, lon_0=3,
    llcrnrlon=-5.5, llcrnrlat=41,
    urcrnrlon=10,   urcrnrlat=51.2,
    resolution='i'
)

# Background
m.drawcoastlines(color='#444444', linewidth=0.8)
m.drawcountries(color='darkgray', linewidth=1.2)
m.drawmapboundary(fill_color='#a6d1f5')
m.fillcontinents(color='#f0f0e8', lake_color='#a6d1f5')

# ── Plot cities ──────────────────────────────────────────────────────────────
city_lons = [d["lon"] for d in city_data.values()]
city_lats = [d["lat"] for d in city_data.values()]
x_cities, y_cities = m(city_lons, city_lats)
m.scatter(x_cities, y_cities,
          s=30, color='royalblue', edgecolor='navy', zorder=10,
          label=f'{len(city_data):,} Cities')

# ── Plot ROAD_TO connections as straight lines ───────────────────────────────
for start_id, end_id in roads:
    c1 = city_data[start_id]
    c2 = city_data[end_id]

    lons = [c1["lon"], c2["lon"]]
    lats = [c1["lat"], c2["lat"]]

    x, y = m(lons, lats)
    m.plot(x, y,
           color='tomato', linewidth=1.1, alpha=0.7, zorder=5)  # roads under cities

# Optional: add city names (only for bigger cities or on hover if interactive)
# for cid, data in city_data.items():
#     x, y = m(data["lon"], data["lat"])
#     plt.text(x+8000, y+8000, data["name"], fontsize=7, color='darkblue', zorder=15)

plt.title("French Cities + ROAD_TO Connections", fontsize=15, pad=20)
plt.legend(loc='upper left', frameon=True)

plt.tight_layout()
plt.savefig('france_cities_with_roads_straight.png', dpi=200, bbox_inches='tight')
plt.show()

print("Map saved as 'france_cities_with_roads_straight.png'")