import logging

# create log with 'spam_application'
logger = logging.getLogger("ServerMcServerface")
logger.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s::%(funcName)s::%(lineno)d"
    "- %(levelname)s - %(message)s"
)

# create console handler
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(formatter)

# allows to add only one instance of file handler and stream handler
if logger.handlers:
    for handler in logger.handlers:
        # add the handlers to the log
        # makes sure no duplicate handlers are added

        if not isinstance(handler, logging.StreamHandler):
            logger.addHandler(consoleHandler)
            print('added stream handler')
else:
    logger.addHandler(consoleHandler)
    print('added handler for the first time')