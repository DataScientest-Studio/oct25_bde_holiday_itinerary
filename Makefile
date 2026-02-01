.SILENT:
.ONESHELL:
.PHONY: tests

init: run make-dataset

manual-import:
	poetry run transform-datatourisme

run:
	docker compose up -d

start-airflow:
	docker compose -f docker-compose.airflow.yaml up -d

tests:
	-docker network create testnet

	docker run -d \
		--name neo4j-test \
		--network testnet \
    	-e NEO4J_AUTH=none \
		-e NEO4JLABS_PLUGINS='["apoc"]' \
		neo4j:2025.10.1

	@echo "Waiting for Neo4j to be ready..."
	@while ! docker exec neo4j-test cypher-shell -u neo4j -p neo4j "RETURN 1" > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "Neo4j is ready!"

	docker build --target=development -t holiday:development .

	docker run --rm -it \
		--network testnet \
		-e NEO4J_URI=bolt://neo4j-test:7687 \
		-e NEO4J_USER=neo4j \
		-e NEO4J_PASSPHRASE="" \
		holiday:development

	docker rm -f neo4j-test
