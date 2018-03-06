FROM python:3.6-alpine

RUN apk add --no-cache --update python-dev py-pip gcc build-base linux-headers

RUN pip install pyyaml aiohttp

COPY . /overwatch-hub/

RUN pip install /overwatch-hub

RUN mkdir /overwatch-hub/local

CMD ["overwatch-hub", "/conf/overwatch-hub.yaml"]
