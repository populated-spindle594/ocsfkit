FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir --upgrade pip

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY examples ./examples
COPY src ./src

RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["ocsfkit"]
CMD ["--help"]
