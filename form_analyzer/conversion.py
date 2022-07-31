import glob
import logging
import os
import typing
from dataclasses import dataclass

import pdf2image
from PIL.Image import Image


@dataclass
class ProcessedImage:
    image: Image
    extension: str


ImageProcessor = typing.Callable[[int, Image], typing.List[ProcessedImage]]


def pdf_to_image(folder: str, dpi: int = 400, poppler_path: str = None,
                 image_processor: ImageProcessor = lambda image_index, img: [(str(image_index + 1), img)]):
    """
    Converts PDF files in a folder to PNG images

    :param folder:
    :param dpi:
    :param poppler_path:
    :param image_processor:
    """
    from form_analyzer import form_analyzer_logger

    for file_name in glob.glob(f'{folder}/*.pdf'):
        form_analyzer_logger.log(logging.INFO, f'Converting {file_name}')
        pages = pdf2image.convert_from_path(file_name, dpi=dpi, poppler_path=poppler_path)
        file_name_without_ext = os.path.splitext(file_name)[0]

        for page_index, image in enumerate(pages):
            processed_images = image_processor(page_index, image)
            for processed_image in processed_images:
                processed_image.image.save(file_name_without_ext + processed_image.extension + '.png')
