# Build image
FROM python:3.13-slim-trixie AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DISPLAY=:99

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /api

RUN python -m pip install --no-cache-dir poetry==2.2.1 && poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install --no-interaction --no-ansi

# Build image for Neo4j_api target
FROM builder AS API-builder

RUN poetry export --with neo4j_api  --without-hashes -f requirements.txt > requirements.txt

# Build image for make_dataset target
FROM builder AS Make_dataset-builder

RUN poetry export --with make_dataset  --without-hashes -f requirements.txt > requirements.txt

# Make dataset image
FROM python:3.13-slim-trixie AS Make_dataset

WORKDIR /make_dataset

COPY ./example_data .
COPY ./src/data/ .

ENTRYPOINT ["python3" "make_dataset.py"]


# API image
FROM python:3.13-slim-trixie AS Neo4j_API

WORKDIR /neo4j_api

COPY --from=API-builder /api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/neo4j_api/ .

ENTRYPOINT ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
