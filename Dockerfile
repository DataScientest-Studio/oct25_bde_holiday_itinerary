# Build image
FROM python:3.13-slim-trixie AS API-builder

ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DISPLAY=:99

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /api

RUN python -m pip install --no-cache-dir poetry==2.2.1 && poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install --no-interaction --no-ansi
RUN poetry export --with neo4j_api  --without-hashes -f requirements.txt > requirements.txt

# API image
FROM python:3.13-slim-trixie AS API

WORKDIR /neo4j_api

COPY --from=API-builder /api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/neo4j_api/ .

ENTRYPOINT ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
