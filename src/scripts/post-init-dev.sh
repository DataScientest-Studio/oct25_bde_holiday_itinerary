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
