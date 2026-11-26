FROM python:3.9-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --progress-bar off -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/

RUN useradd -m techcorp && chown -R techcorp:techcorp /app
USER techcorp

ENV PYTHONPATH=/app

CMD ["pytest", "-v"]