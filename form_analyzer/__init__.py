__version__ = "0.0.1"
__author__ = "Florian Fetz"

import logging

from .analyze import analyze, dump_fields
from .conversion import pdf_to_image
from .textract import run_textract

form_analyzer_logger = logging.Logger('form_analyzer')
if not form_analyzer_logger.hasHandlers():
    handler = logging.StreamHandler()
    log_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(log_format)
    form_analyzer_logger.addHandler(handler)
