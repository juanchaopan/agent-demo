FROM python:3.14-slim AS build
RUN pip install --no-cache-dir poetry==2.5.1
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --only main --no-root --no-interaction

FROM python:3.14-slim
RUN useradd --create-home app
WORKDIR /app
COPY --from=build /app/.venv .venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
