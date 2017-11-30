Overwatch Hub
=============

[![CircleCI](https://circleci.com/gh/leadhub-code/overwatch-hub/tree/master.svg?style=svg&circle-token=ff4678e69f5252993c2fdfade4bdfd02696a9e9d)](https://circleci.com/gh/leadhub-code/overwatch-hub/tree/master)

This is a standalone HTTP server that:

- accepts reports from agents
- manages all report, check, watchdog and alert data
- provides API for web UI [overwatch-web](https://github.com/leadhub-code/overwatch-web)

Implemented using [asyncio](https://docs.python.org/3/library/asyncio.html) and [aiohttp](http://aiohttp.readthedocs.io/en/stable/).

See [Overwatch monitoring overview](https://github.com/leadhub-code/overwatch-monitoring/blob/master/README.md).
