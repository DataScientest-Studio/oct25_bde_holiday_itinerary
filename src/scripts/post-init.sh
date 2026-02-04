#!/bin/bash

set -euo pipefail

export $(grep -v '^#' .env | xargs)

NEO4J_USER="neo4j"
NEO4J_PASS="${NEO4J_PASSWORD}"
IMPORT_VERSION="initial"

echo "Waiting for Neo4j to accept connections..."

until cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASS}" -d system \
    "SHOW DATABASE neo4j YIELD currentStatus WHERE currentStatus = 'online' RETURN 1" \
    | grep -q 1; do
    sleep 2
done

echo "Neo4j is ready."

execute_cypher() {
    STEP_NAME="$1"
    CYPHER="$2"

    APPLIED=$(
        cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASS}" --format plain <<EOF
            MATCH (m:_Migration {name: "${STEP_NAME}"})
            RETURN count(m);
EOF
    )

    APPLIED=$(echo "$APPLIED" | tail -n 1 | tr -d '[:space:]')

    if [ "${APPLIED}" != "0" ]; then
        echo "Step '${STEP_NAME}' already applied. Skipping."
        return
    fi

    echo "Creating '${STEP_NAME}'..."

    cypher-shell -u "${NEO4J_USER}" -p "${NEO4J_PASS}" <<EOF
$CYPHER
CREATE (:_Migration {
    name: "${STEP_NAME}",
    version: "${IMPORT_VERSION}",
    appliedAt: datetime()
});
EOF

    echo "Step '${STEP_NAME}' completed."
}

# ------------------------------------------------------------
# 1. ROAD_TO relationships
# ------------------------------------------------------------
execute_cypher "roads" "
MATCH (c1:City)
CALL {
    WITH c1
    MATCH (c2:City)
    WHERE c1 <> c2
    WITH c1, c2, point.distance(
         point({ latitude: c1.latitude, longitude: c1.longitude }),
         point({ latitude: c2.latitude, longitude: c2.longitude })
    ) AS distance
    ORDER BY distance ASC
    LIMIT 5
    RETURN c2, distance
}
MERGE (c1)-[r1:ROAD_TO]->(c2)
ON CREATE SET r1.km = round(distance / 1000.0, 2)
MERGE (c2)-[r2:ROAD_TO]->(c1)
ON CREATE SET r2.km = round(distance / 1000.0, 2);
"

# ------------------------------------------------------------
# 2. IS_IN relationships
# ------------------------------------------------------------
execute_cypher "is_in" "
CALL apoc.periodic.iterate(
    'MATCH (p:POI)
    WHERE p.city IS NOT NULL
    RETURN p',
    'MATCH (c:City)
    WHERE p.city = c.name
    MERGE (p)-[:IS_IN]->(c)',
    { batchSize: 2000, parallel: true }
);
"

# ------------------------------------------------------------
# 3. IS_NEARBY relationships
# ------------------------------------------------------------
execute_cypher "is_nearby" "
CALL apoc.periodic.iterate(
    'MATCH (p:POI)
    WHERE NOT (p)-[:IS_IN]->(:City)
    AND p.latitude IS NOT NULL
    AND p.longitude IS NOT NULL
    RETURN p',
    'MATCH (c:City)
    WHERE c.latitude IS NOT NULL
    AND c.longitude IS NOT NULL
    WITH p, c,
       point.distance(
         point({ latitude: p.latitude, longitude: p.longitude }),
         point({ latitude: c.latitude, longitude: c.longitude })
       ) AS dist
    WHERE dist < 100000
    ORDER BY dist ASC
    WITH p,
       collect(c)[0] AS nearestCity,
       collect(dist)[0] AS shortestDist
    MERGE (p)-[r:IS_NEARBY]->(nearestCity)
    SET r.distance_km = round(shortestDist / 1000.0, 2)',
    { batchSize: 1000, parallel: false }
);
"

execute_cypher "city-road-graph" "
CALL gds.graph.project(
    'city-road-graph',
    'City',
    {
        ROAD_TO: {
            type: 'ROAD_TO',
            orientation: 'UNDIRECTED',
            properties: ['km']
        }
    }
);
"

echo "All post-import steps complete."
