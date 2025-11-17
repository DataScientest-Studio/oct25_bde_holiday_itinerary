.SILENT:
.ONESHELL:
.PHONY: install

init: run make-dataset

make-dataset:
		@python - <<END
import time, socket, os
host = "neo4j"
port = 7687
while True:
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        break
    except Exception:
        print("Waiting for Neo4j...")
        time.sleep(1)
print("Neo4j ready!")
END
	docker build --target=Make_dataset -t holiday_itineray:latest .
	docker run --rm holiday_itineray:latest

run:
	docker compose up -d
