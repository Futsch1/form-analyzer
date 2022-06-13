import glob
import logging
import os
import typing

import pdf2image
from PIL.Image import Image

ImageProcessor = typing.Callable[[int, Image], typing.List[typing.Tuple[str, Image]]]


def pdf_to_image(folder: str, dpi: int = 400, poppler_path: str = None,
                 image_processor: ImageProcessor = lambda image_index, img: [(str(image_index + 1), img)]):
    from form_analyzer import form_analyzer_logger

    for file_name in glob.glob(f'{folder}/*.pdf'):
        form_analyzer_logger.log(logging.INFO, f'Converting {file_name}')
        images = pdf2image.convert_from_path(file_name, dpi=dpi, poppler_path=poppler_path)
        file_name_without_ext = os.path.splitext(file_name)[0]

        for image_index, image in enumerate(images):
            processed_images = image_processor(image_index, image)
            for processed_extension, processed_image in processed_images:
                processed_image.save(file_name_without_ext + processed_extension + '.png')
