FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential git --no-install-recommends

# initialize venv
RUN python -m venv /opt/venv

# activate venv
ENV PATH="/opt/venv/bin:$PATH"

# upgrade venv deps
RUN pip install --trusted-host pypi.python.org --upgrade pip setuptools wheel

COPY requirements.txt /app

RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

COPY . /app

# inject railway env vars
ARG RAILWAY_GIT_COMMIT_SHA
ARG RAILWAY_GIT_BRANCH

RUN \
    echo "$(expr substr "$RAILWAY_GIT_COMMIT_SHA" 1 7)@$RAILWAY_GIT_BRANCH" | tee .version ; \
    if test $(expr length "$(cat .version)") -le 3; then echo "$(git describe --tags --always)@$(git branch --show-current)" | tee .version ; fi ; \
    if test $(expr length "$(cat .version)") -le 3; then echo "dirty-build@$(date -Iseconds)" | tee .version; else echo "build@$(date -Iseconds)" | tee -a .version; fi ; \
    rm -rf .git .github config docs && \
    ls -la ; \
    cat .version

#----------------------------------------

FROM python:3.10-slim

# install fonts
RUN apt-get update && apt-get install -y fonts-wqy-microhei

# install wkhtmltopdf  # hmmm, wkhtmltopdf works strangely...
#RUN \
#    apt-get update && apt-get -y install wget && \
#    wget "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_$(dpkg --print-architecture).deb" -O /tmp/wkhtmltopdf.deb && \
#    dpkg -i /tmp/wkhtmltopdf.deb && apt-get -f install && \
#    rm -f /tmp/wkhtmltopdf.deb && apt-get purge wget --auto-remove

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY --from=builder /app /app

# activate venv
ENV PATH="/opt/venv/bin:$PATH"

ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "telegramRSSbot.py"]
