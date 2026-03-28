.PHONY: data requirements

requirements:
	pip install -r requirements.txt

data:
	python src/data_ingestion/api_fetch.py

clean:
	rm -rf data/interim/*
