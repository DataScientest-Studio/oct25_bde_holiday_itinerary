#!/bin/bash

set -euo pipefail

DB_DIR="/data/databases/neo4j"
FLAG="/data/.import-done"

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
    echo "--- Import complete. Starting Neo4j server... ---"
else
    echo "--- Database already exists. Starting Neo4j server without import... ---"
fi
