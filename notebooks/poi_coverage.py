import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from neo4j import GraphDatabase

# ── Neo4j connection ─────────────────────────────────────────────────────────
uri = "bolt://localhost:7687"  # ← your URI
username = ""
password = ""

driver = GraphDatabase.driver(uri, auth=(username, password))

# Query — fetch only what we need, no unnecessary properties
query = """
MATCH (p:Poi)
RETURN p.latitude AS lat, p.longitude AS lon
"""

lats = []
lons = []

print("Fetching POI coordinates from Neo4j...")

with driver.session() as session:
    result = session.run(query)
    for record in result:
        lat = record["lat"]
        lon = record["lon"]
        if lat is not None and lon is not None:
            lats.append(lat)
            lons.append(lon)

driver.close()

print(f"Fetched {len(lats):,} POIs")

# Convert to numpy arrays (much faster for large datasets)
lats = np.array(lats)
lons = np.array(lons)

# ── Create map ───────────────────────────────────────────────────────────────
plt.figure(figsize=(12, 14))

m = Basemap(
    projection="lcc",
    lat_1=44,
    lat_2=50,
    lat_0=46.5,
    lon_0=3,
    llcrnrlon=-5.5,
    llcrnrlat=41,
    urcrnrlon=10,
    urcrnrlat=51.2,
    resolution="i",
)

m.drawcoastlines(color="#444444", linewidth=0.8)
m.drawcountries(color="darkgray", linewidth=1.2)
m.drawmapboundary(fill_color="#a6d1f5")
m.fillcontinents(color="#f0f0e8", lake_color="#a6d1f5")

# Plot points — use alpha + small marker size + no edge for performance
x, y = m(lons, lats)
m.scatter(
    x,
    y,
    s=2,  # very small size
    color="red",
    alpha=0.4,  # transparency helps see density
    edgecolor="none",  # no border = faster
    zorder=10,
    label=f"{len(lats):,} POIs",
)

plt.title("POI Coverage in France (300k points)", fontsize=14, pad=20)
plt.legend(loc="upper left", frameon=True)

plt.tight_layout()
plt.savefig("france_poi_coverage_300k.png", dpi=200, bbox_inches="tight")
plt.show()

print("Map saved as 'france_poi_coverage_300k.png'")
