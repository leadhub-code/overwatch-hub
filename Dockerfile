FROM python:3.6-stretch

RUN pip install pyyaml aiohttp

COPY . /overwatch-hub/

RUN pip install /overwatch-hub

RUN mkdir /overwatch-hub/local

CMD ["overwatch-hub", "/conf/overwatch-hub.yaml"]
