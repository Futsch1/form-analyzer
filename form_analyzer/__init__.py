__version__ = "0.0.1"
__author__ = "Florian Fetz"

import logging
import typing
from dataclasses import dataclass

from .analyze import analyze, dump_fields, FormDescriptionError
from .conversion import pdf_to_image, ProcessedImage
from .form_selectors import Selector
from .textract import run_textract

__all__ = [analyze, dump_fields, FormDescriptionError, pdf_to_image, run_textract]


@dataclass
class FormItem:
    title: str
    selector: Selector


FormDescription = typing.List[FormItem]

form_analyzer_logger = logging.Logger('form_analyzer')
if not form_analyzer_logger.hasHandlers():
    handler = logging.StreamHandler()
    log_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(log_format)
    form_analyzer_logger.addHandler(handler)
