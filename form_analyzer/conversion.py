import glob
import os
import typing

import pdf2image
from PIL.Image import Image

ImageProcessor = typing.Callable[[int, Image], typing.List[typing.Tuple[str, Image]]]


def pdf_to_image(folder: str, dpi: int = 400, poppler_path: str = None, image_processor: ImageProcessor = lambda _, img: ['', img]):
    # Document
    for file_name in glob.glob(f'{folder}/*.pdf'):

        file_name_without_ext = os.path.splitext(file_name)[0]
        if os.path.exists(f'{file_name_without_ext}_1_1.png'):
            continue

        print(f'Converting {file_name}')
        images = pdf2image.convert_from_path(file_name, dpi=dpi, poppler_path=poppler_path)

        for image_index, image in enumerate(images):
            processed_images = image_processor(image_index, image)
            for processed_extension, processed_image in processed_images:
                processed_image.save(file_name_without_ext + processed_extension)
