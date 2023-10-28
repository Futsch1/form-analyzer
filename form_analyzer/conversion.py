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
                 image_processor: ImageProcessor = lambda image_index, img: [ProcessedImage(img, '')]):
    """
    Converts PDF files in a folder to PNG images.

    PDF files are converted page by page using pdf2image. Each generated page can optionally be passed to a
    function that can further process the image (e.g. split it or crop it). Additionally, the extension of the
    resulting file name can be passed. This can be used to reorder pages in a PDF.

    :param folder: The folder containing the PDF files.
    :param dpi: DPI to use for image generation. The higher, the bigger the image. 400 is the default.
    :param poppler_path: Path to a poppler installation, required for Windows.
    :param image_processor: A function that takes an image index and an image and returns a list of ProcessedImage.
    """
    from form_analyzer import form_analyzer_logger

    for file_name in glob.glob(f'{folder}/*.pdf'):
        form_analyzer_logger.log(logging.INFO, f'Converting {file_name}')
        pages = pdf2image.convert_from_path(file_name, dpi=dpi, poppler_path=poppler_path)
        file_name_without_ext = os.path.splitext(file_name)[0]

        for page_index, image in enumerate(pages):
            processed_images = image_processor(page_index, image)
            for processed_image in processed_images:
                processed_image.image.save(f'{file_name_without_ext}_{page_index}{processed_image.extension}.png')
