FROM python:3.10-bullseye AS dep-builder-common

ENV PATH="/opt/venv/bin:$PATH"

RUN \
    set -ex && \
    python -m venv --copies /opt/venv && \
    pip install --no-cache-dir --upgrade \
        pip setuptools wheel

COPY requirements.txt .

RUN \
    set -ex && \
    pip install --no-cache-dir \
        -r requirements.txt \
    && \
    rm -rf /opt/venv/src

#-----------------------------------------------------------------------------------------------------------------------

FROM python:3.10-bullseye AS dep-builder

ENV PATH="/opt/venv/bin:$PATH"

COPY --from=dep-builder-common /opt/venv /opt/venv
COPY requirements.txt .

ARG FEEDPARSER_ENHANCED=0
RUN \
    set -ex && \
    if [ "$FEEDPARSER_ENHANCED" = 1 ]; then \
        pip uninstall -y feedparser && \
        sed -i 's/^feedparser[^#]*#\s*//g' requirements.txt ; \
        pip install --no-cache-dir \
            -r requirements.txt \
        ; \
    fi;

#-----------------------------------------------------------------------------------------------------------------------

FROM python:3.10-bullseye as app-builder

WORKDIR /app

COPY . /app

# inject railway env vars
ARG RAILWAY_GIT_COMMIT_SHA
ARG RAILWAY_GIT_BRANCH

RUN \
    set -ex && \
    echo "$(expr substr "$RAILWAY_GIT_COMMIT_SHA" 1 7)@$RAILWAY_GIT_BRANCH" | tee .version && \
    if test $(expr length "$(cat .version)") -le 3; then \
        echo "$(git describe --tags --always)@$(git branch --show-current)" | tee .version ; \
    fi && \
    if test $(expr length "$(cat .version)") -le 3; then \
        echo "dirty-build@$(date -Iseconds)" | tee .version; else echo "build@$(date -Iseconds)" | tee -a .version; \
    fi && \
    mkdir /app-minimal && \
    cp -r .version LICENSE src telegramRSSbot.py /app-minimal && \
    cd / && \
    rm -rf /app && \
    rm -f /app-minimal/*.md && \
    ls -la /app-minimal && \
    du -hd1 /app-minimal && \
    cat /app-minimal/.version

#-----------------------------------------------------------------------------------------------------------------------

FROM python:3.10-slim-bullseye as app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    MALLOC_MMAP_THRESHOLD_=131072

WORKDIR /app

# install fonts
RUN \
    set -ex && \
    apt-get update && \
    apt-get install -yq --no-install-recommends \
        fonts-wqy-microhei dumb-init \
    && \
    rm -rf /var/lib/apt/lists/*

COPY --from=dep-builder /opt/venv /opt/venv
COPY --from=app-builder /app-minimal /app

# verify cryptg installation
RUN python -c 'import logging; logging.basicConfig(level=logging.DEBUG); import telethon; import cryptg'

ENTRYPOINT ["dumb-init", "--"]

CMD ["python", "-u", "telegramRSSbot.py"]
