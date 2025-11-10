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

RUN apt-get update && apt-get install -y git sudo zsh curl && rm -rf /var/lib/apt/lists/*

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g appuser -m -s /bin/zsh appuser && \
    echo "appuser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/vscode-appuser

WORKDIR /usr/src/app

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app/src"
ENV PATH="/home/appuser/.local/bin:${PATH}"

ARG INSTALL_DEV=false

COPY --from=builder /usr/src/app/prod-wheels /prod-wheels
COPY --from=builder /usr/src/app/dev-wheels /dev-wheels

RUN if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache /dev-wheels/*; \
    else pip install --no-cache /prod-wheels/*; fi

COPY --chown=appuser:appuser . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p logs && \
    chown -R appuser:appuser logs

USER appuser

RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
