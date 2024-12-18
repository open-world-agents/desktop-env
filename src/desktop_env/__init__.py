from loguru import logger

from .desktop import Desktop
from .desktop_args import DesktopArgs

# https://loguru.readthedocs.io/en/stable/resources/recipes.html#configuring-loguru-to-be-used-by-a-library-or-an-application
logger.disable("desktop_env")
