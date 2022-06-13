import typing

from PIL.Image import Image

import form_analyzer


def one_page_to_two(_: int, image: Image) -> typing.List[typing.Tuple[str, Image]]:
    left = image.crop((0, 0, image.width // 2, image.height))
    right = image.crop((image.width // 2, 0, image.width, image.height))

    return [('_1', left), ('_2', right)]


form_analyzer.pdf_to_image('results', image_processor=one_page_to_two)
form_analyzer.run_textract('results')
form_analyzer.dump_fields('results')
form_analyzer.analyze('results', 'example_form')
