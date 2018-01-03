FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

RUN apt-get clean \
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
