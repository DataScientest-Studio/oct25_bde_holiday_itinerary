# Underlying Data Structure

This document describes the data structure used in the Neo4j database for the holiday itinerary project.

## Cities and Roads

### City Nodes
The `City` nodes represent French cities. They were imported from a dataset of 627 French cities (source: [simplemaps.com](https://simplemaps.com/data/fr-cities)). Each city contains properties such as name, administration, population, and its geographical location (latitude/longitude stored as a Neo4j `Point`).

### ROAD_TO Relationships
Since no suitable road dataset was readily available, a road network was simulated to enable routing between cities.

**Reasoning and Creation:**
1.  **Initial Connectivity (KNN):** To create a realistic yet manageable set of roads, we used the K-Nearest Neighbors (KNN) approach. Each city was connected to its 5 nearest neighbors using the `ROAD_TO` relationship. The distance in kilometers was calculated and stored on the relationship property `km`.
2.  **Ensuring Full Connectivity (WCC):** After the KNN step, the graph contained several disconnected clusters. To ensure that an itinerary can be calculated between any two cities, we used the Weakly Connected Components (WCC) algorithm to identify these clusters.
3.  **Manual Iteration:** We iteratively identified the nearest cities between different clusters and connected them with `ROAD_TO` relationships until the entire graph became a single connected component.

## Points of Interest (POI) and Types

### POI Nodes
`POI` nodes represent various tourist attractions, hotels, restaurants, etc., imported from the [DataTourisme](https://www.datatourisme.fr/) API. They contain metadata such as labels, descriptions, contact information, and coordinates.

### Type Nodes and IS_A Relationship
Instead of using Neo4j labels to categorize POIs (e.g., `:POI:Restaurant:Hotel`), we use a separate `Type` node and an `IS_A` relationship.

**Reasoning:**
-   **Multiple Categorization:** DataTourisme provides a wide and often overlapping set of types for each POI. Using nodes for types is more flexible than managing a large, dynamic set of labels on individual POI nodes.
-   **Hierarchy Support:** Using nodes allows for future expansion into a hierarchical type system (e.g., a "Bistro" `IS_A` "Restaurant").
-   **Query Performance:** It simplifies queries that need to filter POIs by category, especially when dealing with many categories or complex overlaps.

## Spatial Relationships

### IS_IN
The `IS_IN` relationship connects a `POI` to a `City`.
-   **Creation:** This relationship is created when the `city` property of a POI exactly matches the `name` of a `City` node.
-   **Purpose:** It provides a direct link between a city and its attractions, facilitating quick lookups for POIs within a specific municipality.

### IS_NEARBY
The `IS_NEARBY` relationship is used for POIs that do not have a direct `IS_IN` link to a city (often POIs located outside city limits).
-   **Creation:** For POIs without an `IS_IN` relationship, the system searches for the nearest `City` node within a 100km radius. A link is created to the single closest city. The distance is stored in `distance_km`.
-   **Purpose:** It ensures that every POI is associated with at least one urban center, which is crucial for itinerary planning and "nearby" search functionality.
