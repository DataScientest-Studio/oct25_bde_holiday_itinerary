from neo4j import GraphDatabase
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

uri = "bolt://localhost:7687"
username = ""
password = ""

driver = GraphDatabase.driver(uri, auth=(username, password))

query = """
MATCH (c:City)
RETURN c.latitude AS lat, c.longitude AS lon
"""

lats = []
lons = []

with driver.session() as session:
    result = session.run(query)
    for record in result:
        lat = record["lat"]
        lon = record["lon"]
        if lat is not None and lon is not None:   # safety check
            lats.append(lat)
            lons.append(lon)

driver.close()

plt.figure(figsize=(10, 12))

# Good projection & bounding box just for metropolitan France
m = Basemap(
    projection='lcc',             # Lambert Conformal Conic → nice for Europe
    lat_1=44, lat_2=50,           # standard parallels
    lat_0=46.5, lon_0=3,          # map center
    llcrnrlon=-5.5, llcrnrlat=41,
    urcrnrlon=10,   urcrnrlat=51.2,
    resolution='i'                # 'i'ntermediate resolution is good compromise
)

# Draw nice background elements
m.drawcoastlines(color='#444444', linewidth=0.8)
m.drawcountries(color='darkgray', linewidth=1.2)     # ← country borders!
m.drawmapboundary(fill_color='#a6d1f5')               # light blue ocean
m.fillcontinents(color='#f0f0e8', lake_color='#a6d1f5')  # land + lakes

# Optional: draw French regions / départements (finer lines)
# m.drawstates(color='lightgray', linewidth=0.4)

# Plot your cities
x, y = m(lons, lats)           # convert lon/lat → map projection coordinates
m.scatter(x, y, marker='o', s=25, color='red', edgecolor='darkred', zorder=10,
          alpha=0.9, label='Cities')

# Title & legend
plt.title("City Coverage in France\n(with metropolitan border)", fontsize=14, pad=20)
plt.legend(loc='upper left', frameon=True, fontsize=10)

# Save & show
plt.tight_layout()
plt.savefig('france_city_coverage_with_border.png', dpi=200, bbox_inches='tight')
plt.show()

print("Map saved as 'france_city_coverage_with_border.png'")