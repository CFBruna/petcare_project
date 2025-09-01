FROM python:3.12-slim as builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt



FROM python:3.12-slim


RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY --from=builder /usr/src/app/wheels /wheels
RUN pip install --no-cache /wheels/*

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
