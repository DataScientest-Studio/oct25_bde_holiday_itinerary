#!/bin/bash

set -euo pipefail

DB_DIR="/data/databases/neo4j"
FLAG="/data/.import-done"
DB_NAME="neo4j"

# Check if the database data already exists (to prevent re-importing)
if [ ! -d "$DB_DIR" ] || [ ! -f "$FLAG" ]; then
    echo "First start detected → running neo4j-admin import"

    neo4j-admin database import full neo4j\
        --overwrite-destination \
        --verbose \
        --multiline-fields=true \
        --nodes="City=/import/cities_nodes.zip" \
        --nodes="POI=/import/poi_nodes.zip" \
        --nodes="POIType=/import/type_nodes.zip" \
        --relationships="ROAD_TO=/import/roads_rels.zip" \
        --relationships="IS_A=/import/poi_is_a_type_rels.zip"\
        --relationships="IS_IN=/import/poi_is_in_rels.zip" \
        --relationships="IS_NEARBY=/import/poi_is_nearby_rels.zip"

    chown -R neo4j:neo4j /data

    touch "$FLAG"

    echo "--- Import complete. Starting Neo4j server... ---"
else
    echo "--- Database already exists. Starting Neo4j server without import... ---"
fi
