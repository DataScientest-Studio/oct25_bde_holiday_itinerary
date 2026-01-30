# Process of creating cities-roads dataset

## Purpose

This dataset is intended for demonstration and experimentation with graph algorithms
(e.g. routing, clustering, centrality) rather than real-world road accuracy.
Roads are synthetically generated based on geographic proximity.

## Prerequisites

- Neo4j 5.x
- Graph Data Science library 2.x
- APOC Core enabled

## Original dataset

Original dataset can be found [here](https://simplemaps.com/data/fr-cities)
It consists of 627 French cities which is enough for the demonstration purposes.
The CSV file looks like so:

| city        | lat     | lng     | country | iso2 | admin_name                 | capital | population | population_proper |
| ----------- | ------- | ------- | ------- | ---- | -------------------------- | ------- | ---------- | ----------------- |
| Paris       | 48.8567 | 2.3522  | France  | FR   | Île-de-France              | primary | 11060000   | 2148271           |
| Bordeaux    | 44.8400 | -0.5800 | France  | FR   | Nouvelle-Aquitaine         | admin   | 994920     | 994920            |
| Marseille   | 43.2964 | 5.3700  | France  | FR   | Provence-Alpes-Côte d’Azur | admin   | 873076     | 873076            |
| Lyon        | 45.7600 | 4.8400  | France  | FR   | Auvergne-Rhône-Alpes       | admin   | 522250     | 522250            |
| Toulouse    | 43.6045 | 1.4440  | France  | FR   | Occitanie                  | admin   | 504078     | 504078            |
| Nice        | 43.7034 | 7.2663  | France  | FR   | Provence-Alpes-Côte d’Azur | minor   | 348085     | 348085            |
| Nantes      | 47.2181 | -1.5528 | France  | FR   | Pays de la Loire           | admin   | 323204     | 323204            |
| Montpellier | 43.6119 | 3.8772  | France  | FR   | Occitanie                  | minor   | 302454     | 302454            |

## Import dataset

```cypher
load csv with headers from "file:///france_cities.csv" as row
merge (city:City {id: row.city})
on create set
    city.id = row.city,
    city.name = row.city,
    city.administration = row.admin_name,
    city.population = row.population,
    city.population_proper = row.population_proper,
    city.location = point({latitude: toFloat(row.lat), longitude: toFloat(row.lng)})
```

There we can use _lat_ and _lng_ for our coordinates. This gives us only the cities without any roads between them.
I didn't find any suitable road dataset therefore I decided to simulate one in a naive way:

Use KNN algorithm to find K-nearest neighbors of a city __A__ and connect it with it's K nearest cities.

## Create roads: KNN

Used KNN with `K = 5` which I found reasonable.

```cypher
match (c1:City)
call {
    with c1
    match (c2:City)
    where c1 <> c2
    with c1, c2, point.distance(c1.location, c2.location) as distance
    order by distance asc
    limit 5
    return c2, distance
}
merge (c1) - [r1:ROAD_TO] -> (c2)
on create set r1.km = round(distance/1000, 2)
merge (c2) - [r2:ROAD_TO] -> (c1)
on create set r2.km = round(distance/1000, 2);
```

We can verify the cities are interconnected using WCC algorithm.

First create a graph projection

```cypher
CALL gds.graph.project(
  'cities',          // graph name
  'City',               // node label
  {ROAD_TO: {orientation: "UNDIRECTED"}} // relationship
);
```

and call WCC:

```cypher
CALL gds.wcc.stream('cities')
YIELD nodeId, componentId
WITH componentId, count(*) AS size
RETURN componentId AS component, size
ORDER BY size ASC
```

returns

| component | size |
| --------- | ---- |
| 0         | 531  |
| 9         | 30   |
| 2         | 20   |
| 5         | 14   |
| 48        | 13   |
| 39        | 10   |
| 8         | 8    |

that means most of the cities are interconnected, but we have still 7 separated clusters.
We need to connect the clusters as well. Since this is not much manual work, we will do the iterations manually.
Repeat steps until only one cluster exists

### Iterate

1. Project graph

```cypher
call gds.graph.drop("cities", false);
CALL gds.graph.project(
  'cities',          // graph name
  'City',               // node label
  {ROAD_TO: {orientation: "UNDIRECTED"}}
);
CALL gds.wcc.write('cities',{
  writeProperty: 'wccId'
});
```

2. verify clustering

```cypher
CALL gds.wcc.stream('cities')
YIELD nodeId, componentId
WITH componentId, count(*) AS size
RETURN componentId AS component, size
ORDER BY size ASC
```

3. Create connection between two nearest clusters

```cypher
MATCH (c1:City), (c2:City)
  WHERE c1.wccId <> c2.wccId
  WITH c1, c2, point.distance(c1.location, c2.location) AS distance
  ORDER BY distance ASC
  LIMIT 1
merge (c1) - [r1:ROAD_TO] -> (c2)
on create set
  r1.km = round(distance/1000, 2),
  r1.wcc_connect = true
merge (c2) - [r2:ROAD_TO] -> (c1)
on create set
  r2.km = round(distance/1000, 2),
  r2.wcc_connect = true
```

# Export dataset

export `cities_nodes.csv`

```cypher
 CALL apoc.export.csv.query(
    'MATCH (c:City)
    RETURN
        c.id as `cityId:ID(City)`,
        c.name as name,
        c.administration as administration,
        c.population as `population:DOUBLE`,
        c.population_proper as `population_proper:DOUBLE`,
        c.location.latitude as `latitude:DOUBLE`,
        c.location.longitude as `longitude:DOUBLE`,
        \'City\' as `:LABEL`',
    'cities_nodes.csv',
    {}
)
```

export `roads_rels.csv`

```cypher
 CALL apoc.export.csv.query(
            'MATCH (from:City)-[r:ROAD_TO]->(to:City)
             RETURN from.id AS `:START_ID(City)`, to.id as `:END_ID(City)`, r.km AS `km:DOUBLE`, r.wcc_connect as `wcc_connect:BOOLEAN`',
            'roads_rels.csv',
            {}
        )
```
