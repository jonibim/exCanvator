import logging

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s",
)

logging.getLogger("urllib3").setLevel(logging.WARNING)


formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

# Create loggers
main_logger = logging.getLogger("main")
api_logger = logging.getLogger("api")
crawl_logger = logging.getLogger("crawl")
ignore_logger = logging.getLogger("ignore")

# Create handlers
main_file_handler = logging.FileHandler("logs/main.log")
api_file_handler = logging.FileHandler("logs/api.log")
crawl_file_handler = logging.FileHandler("logs/crawl.log")
ignore_logger_handler = logging.FileHandler("logs/ignored.log")

# # Set log levels for handlers
main_file_handler.setLevel(logging.DEBUG)
api_file_handler.setLevel(logging.DEBUG)
crawl_file_handler.setLevel(logging.DEBUG)
ignore_logger_handler.setLevel(logging.DEBUG)

# Create formatters and add them to handlers
main_file_handler.setFormatter(formatter)
api_file_handler.setFormatter(formatter)
crawl_file_handler.setFormatter(formatter)
ignore_logger_handler.setFormatter(formatter)

# Add handlers to the loggers
main_logger.addHandler(main_file_handler)
api_logger.addHandler(api_file_handler)
crawl_logger.addHandler(crawl_file_handler)
ignore_logger.addHandler(ignore_logger_handler)

main_logger.propagate = False
api_logger.propagate = False
crawl_logger.propagate = False
ignore_logger.propagate = False
