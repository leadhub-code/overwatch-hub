FROM debian:stretch

MAINTAINER Petr Messner

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y --no-install-recommends python3 python3-venv python3-dev libyaml-dev

RUN python3 -m venv /venv
RUN /venv/bin/pip install -U pip wheel
RUN /venv/bin/pip install flask pymongo pyyaml simplejson gunicorn

COPY . /src/overwatch-hub
RUN /venv/bin/pip install /src/overwatch-hub

RUN useradd --system --uid 900 --home-dir /app app
USER app
WORKDIR /app

ENV OVERWATCH_HUB_CONF /conf/overwatch-hub.yaml

EXPOSE 8000

CMD [ \
    "/venv/bin/gunicorn", \
    "--workers", "16", \
    "--bind", "0.0.0.0:8000", \
    "--preload", \
    "--max-requests", "100", \
    "overwatch_hub:get_app()" \
]
