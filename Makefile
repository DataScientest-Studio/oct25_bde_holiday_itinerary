.SILENT:
.ONESHELL:
.PHONY: install

init: run make-dataset

make-dataset:
	# docker build --target=make_dataset -t holiday_itineray:latest .
	# docker run --rm holiday_itineray:latest
	echo "Just an example"

run:
	docker compose up -d

tests:
	docker build --target=development -t holiday:development .
	docker run holiday:development
