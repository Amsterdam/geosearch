FROM amsterdam/docker_python:latest
MAINTAINER datapunt.ois@amsterdam.nl

ENV PYTHONUNBUFFERED 1

ENV CONSUL_HOST=${CONSUL_HOST:-notset}
ENV CONSUL_PORT=${CONSUL_PORT:-8500}

EXPOSE 8000

RUN apt-get update \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
&& adduser --system datapunt \
&& mkdir -p /static \
&& chown datapunt /static \
&& pip install uwsgi

WORKDIR /app
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

USER datapunt
COPY geosearch /app/
CMD /app/docker-entrypoint.sh
