# Build image
FROM python:3.13-slim-trixie AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DISPLAY=:99

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /builder

RUN python -m pip install --no-cache-dir poetry==2.2.1 && poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock ./README.md ./


# Build image for make_dataset target
FROM builder AS make_dataset-builder

RUN poetry install --no-interaction --no-ansi --no-root --without dev,neo4j_api
RUN eval $(poetry env activate) && pip freeze > requirements.txt

# Make dataset image
FROM python:3.13-slim-trixie AS make_dataset

WORKDIR /make_dataset

COPY --from=make_dataset-builder /builder/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./example_data .
COPY ./src/data/ .

ENTRYPOINT ["python", "make_dataset.py"]


# Build image for Neo4j_api target
FROM builder AS api-builder

RUN poetry install --no-interaction --no-ansi --no-root --without dev,make_dataset
RUN eval $(poetry env activate) && pip freeze > requirements.txt

# API image
FROM python:3.13-slim-trixie AS neo4j_api

WORKDIR /app

COPY --from=api-builder /builder/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/neo4j_api /app/neo4j_api
COPY ./src/neo4j_driver /app/neo4j_driver

ENV PYTHONPATH=/app

WORKDIR /

ENTRYPOINT ["uvicorn", "neo4j_api:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]


# development image
FROM python:3.13-slim-trixie AS development

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/app/src


SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /app

RUN python -m pip install --no-cache-dir poetry==2.2.1 \
    && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

CMD ["python", "-m", "pytest"]
