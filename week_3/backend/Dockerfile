
FROM python:3.12-bookworm
 
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
 
WORKDIR /app
 
# Copy dependency files first for layer caching
COPY pyproject.toml .
COPY .python-version .
 
# Install dependencies
RUN uv sync --no-dev
 
# Copy source (includes app.py and week_2/ folder)
COPY src/ src/
 
ENTRYPOINT ["uv", "run", "uvicorn"]
CMD ["--app-dir", "src", "--host", "0.0.0.0", "app:app"]