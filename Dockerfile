FROM python:3.12-slim as builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/prod-wheels -r requirements.txt

COPY requirements-dev.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/dev-wheels -r requirements-dev.txt


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y git sudo && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /usr/src/app

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app/src"

ARG INSTALL_DEV=false

COPY --from=builder /usr/src/app/prod-wheels /prod-wheels
COPY --from=builder /usr/src/app/dev-wheels /dev-wheels

RUN if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache /dev-wheels/*; \
    else pip install --no-cache /prod-wheels/*; fi

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


RUN mkdir -p logs && \
    touch logs/petcare.json.log && \
    chown appuser:appuser logs/petcare.json.log

USER appuser

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
