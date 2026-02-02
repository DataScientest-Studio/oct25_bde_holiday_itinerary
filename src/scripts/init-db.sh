#!/bin/bash

DB_DIR="/data/databases/neo4j"
FLAG="/data/.import-done"

IMPORT_VERSION=$(uuidgen)

if [ ! -d "$DB_DIR" ] || [ ! -f "$FLAG" ]; then

    echo "Starting the data import into Neo4j..."

    # Run the neo4j-admin import command
    neo4j-admin database import full neo4j \
        --overwrite-destination \
        --verbose \
        --multiline-fields=true \
        --nodes="City=/import/cities_nodes.zip" \
        --nodes="POI=/import/poi_nodes.zip" \
        --nodes="POIType=/import/type_nodes.zip" \
        --relationships="IS_A=/import/poi_is_a_type_rels.zip"

    echo "Data import completed, now running Cypher queries..."

    # Run Cypher queries
    # 1. Create roads between cities
    cypher-shell -u neo4j -p ${NEO4J_PASSWORD} <<EOF
    MATCH (c1:City)
    CALL {
        WITH c1
        MATCH (c2:City)
        WHERE c1 <> c2
        WITH c1, c2, point.distance(c1.location, c2.location) AS distance
        ORDER BY distance ASC
        LIMIT 5
        RETURN c2, distance
    }
    MERGE (c1)-[r1:ROAD_TO]->(c2)
    ON CREATE SET r1.km = round(distance/1000, 2)
    MERGE (c2)-[r2:ROAD_TO]->(c1)
    ON CREATE SET r2.km = round(distance/1000, 2);
EOF

    echo "Created roads between cities."

    # 2. Create IS_IN relationships
    cypher-shell -u neo4j -p ${NEO4J_PASSWORD} <<EOF
    CALL apoc.periodic.iterate(
        "MATCH (p:POI {importVersion: ${IMPORT_VERSION}}) WHERE p.city IS NOT NULL RETURN p",
        "MATCH (c:City {name: p.city})
        MERGE (p)-[r:IS_IN]->(c)
        SET r.importVersion = ${IMPORT_VERSION}",
        {
            batchSize: 2000,
            parallel: true,
            params: { import_version: ${IMPORT_VERSION} }
        }
    )
    YIELD batches, total, errorMessages, committedOperations
    RETURN batches, total, errorMessages, committedOperations;
EOF

    echo "Created IS_IN relationships."

    # 3. Create IS_NEARBY relationships
    cypher-shell -u neo4j -p ${NEO4J_PASSWORD} <<EOF
   CALL apoc.periodic.iterate(
        "MATCH (p:POI {importVersion: ${IMPORT_VERSION}})
        WHERE NOT (p)-[:IS_IN]->(:City) AND p.location IS NOT NULL
        RETURN p",
        "MATCH (c:City)
        WHERE point.distance(p.location, c.location) < 100000
        WITH p, c, point.distance(p.location, c.location) AS dist
        ORDER BY dist ASC
        WITH p, collect(c)[0] AS nearestCity, collect(dist)[0] AS shortestDist
        WHERE nearestCity IS NOT NULL
        MERGE (p)-[r:IS_NEARBY]->(nearestCity)
        SET r.import_version = ${IMPORT_VERSION},
            r.distance_km = round(shortestDist / 1000.0, 2)",
            {
                batchSize: 1000,
                parallel: false,
                params: { import_version: ${IMPORT_VERSION} }
        }
   )
   YIELD batches, total, errorMessages, committedOperations
   RETURN batches, total, errorMessages, committedOperations;
EOF

    echo "Created IS_NEARBY relationships."
    echo "--- Import complete. Starting Neo4j server... ---"
else
    echo "--- Database already exists. Starting Neo4j server without import... ---"
fi
