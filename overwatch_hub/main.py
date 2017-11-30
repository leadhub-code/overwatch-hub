import argparse
import aiohttp.web
import asyncio
from datetime import datetime
import logging
import re
import yaml
from uuid import uuid4

from .configuration import Configuration
from .model import Model
from .web import Handlers


default_bind_address = '127.0.0.1:8090'

logger = logging.getLogger(__name__)


def hub_main():
    p = argparse.ArgumentParser()
    p.add_argument('--verbose', '-v', action='count')
    p.add_argument('conf_file')
    args = p.parse_args()
    setup_logging(args.verbose)
    conf = Configuration(args.conf_file)
    if conf.log.file_path:
        setup_log_file(conf.log.file_path)
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_main(loop, conf))
    except BaseException as e:
        logger.info('Overwatch hub finished: %r', e)
        raise e


log_format = '%(asctime)s %(name)-30s %(levelname)5s: %(message)s'


def setup_logging(verbosity):
    from logging import DEBUG, INFO, ERROR, Formatter, StreamHandler, getLogger

    if not verbosity:
        console_level = ERROR
    elif verbosity == 1:
        console_level = INFO
    else:
        console_level = DEBUG

    getLogger().setLevel(DEBUG)

    h = StreamHandler()
    h.setLevel(console_level)
    h.setFormatter(Formatter(log_format))
    getLogger().addHandler(h)


def setup_log_file(log_file_path):
    from logging import DEBUG, Formatter, getLogger
    from logging.handlers import WatchedFileHandler
    h = WatchedFileHandler(str(log_file_path))
    h.setLevel(DEBUG)
    h.setFormatter(Formatter(log_format))
    getLogger().addHandler(h)


async def _main(loop, conf):
    '''
    Main application logic.
    Logging is already set up.
    '''
    model = Model()
    handlers = Handlers(conf, model)
    app = aiohttp.web.Application()
    handlers.register(app.router)
    app_handler = app.make_handler()
    bind_host = conf.http_interface.bind_host
    bind_port = conf.http_interface.bind_port
    server = await loop.create_server(app_handler, bind_host, bind_port)
    logger.debug('server: %r', server)
    logger.info('Serving on %s', server.sockets[0].getsockname())
    try:
        await server.wait_closed()
        logger.debug('wait_closed done')
    finally:
        logger.info('Shutdown (in finally section)')
        await app.shutdown()
        await app_handler.shutdown(60)
        await app.cleanup()
        logger.info('Shutdown done')
