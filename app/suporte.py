# !/usr/bin/env python3

import tornado
import tornado.web
import tornado.httpserver
import tornado.ioloop
from tornado.options import options
from tornadose.stores import DataStore
from tornadose.handlers import EventSource
import logging
import settings
from routes import url_patterns
import os


logger = logging.getLogger()


class Application(tornado.web.Application):

    def __init__(self):
        # SSE
        store = DataStore()
        url_patterns.append(("/events", EventSource, {"store": store}))
        settings['trello']['store'] = store
        settings['trello']['store'].submit('Started')
        tornado.web.Application.__init__(self, url_patterns, **settings)


def main():
    app = Application()

    if (len(logger.handlers) > 0):
        formatter = logging.Formatter(
            "[%(levelname).1s %(asctime)s %(module)s:%(lineno)s] %(message)s",
            datefmt='%y%m%d %H:%M:%S')
        logger.handlers[0].setFormatter(formatter)

    if options.debug:
        logging.info('== Tornado in DEBUG mode ==============================')
        for k, v in settings.items():
            logging.info('{} = {}'.format(k, v))
        logging.info('=======================================================')

    PORT = int(os.environ.get('PORT', options.port))
    logging.info('Suporte LT listen on port: %d' % PORT)

    logging.info('Suporte LT handlers:')
    for h in url_patterns:
        logging.info(str(h))

    httpserver = tornado.httpserver.HTTPServer(
        app, max_body_size=settings.MAX_BODY_SIZE,
        max_buffer_size=settings.MAX_BUFFER_SIZE, xheaders=True)
    httpserver.listen(PORT)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
