FROM mcr.microsoft.com/devcontainers/python:3.12

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.main:app
ENV FLASK_ENV=development
ENV PYTHONPATH=/workspace

# Instalar UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /workspace

# Copiar solo pyproject.toml primero para aprovechar la caché
COPY pyproject.toml .

# Instalar dependencias con UV usando pyproject.toml
RUN uv pip install -e .

EXPOSE 5000

CMD ["uv", "run", "app.main:app", "--reload"]
