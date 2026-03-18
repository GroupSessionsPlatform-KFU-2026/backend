import logging

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler('app.log')
console_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[file_handler, console_handler],
)