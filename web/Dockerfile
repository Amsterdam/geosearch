FROM python:3.9-slim-bullseye AS builder
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

RUN apt update && apt install --no-install-recommends -y \
    build-essential \
    libgeos-dev \
    libpq-dev \
    python3-dev \
    libffi-dev

COPY requirements* ./
ARG PIP_REQUIREMENTS=requirements.txt

RUN python -m pip install --upgrade pip
RUN python -m pip install uwsgi
RUN python -m pip install --no-cache-dir -r $PIP_REQUIREMENTS


# Start runtime image,
FROM python:3.9-slim-bullseye
RUN apt update && apt install --no-install-recommends -y \
    libgdal28 \
    libgeos-c1v5 \
    libpq5 \
    media-types \
    postgresql-client \
    && python -m pip uninstall pip setuptools -y

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && adduser --system datapunt \
    && mkdir -p /static \
    && chown datapunt /static

# Copy python build artifacts from builder image
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/

WORKDIR /app

EXPOSE 8000
USER datapunt

COPY geosearch /app/
CMD /app/docker-entrypoint.sh
