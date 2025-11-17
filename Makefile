.SILENT:
.ONESHELL:
.PHONY: install

make-dataset:
	docker build --target=Make_dataset -t holiday_itineray:latest .
	docker run --rm holiday_itineray:latest
