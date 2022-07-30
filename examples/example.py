import typing

from PIL.Image import Image

import form_analyzer


def one_page_to_two(_: int, image: Image) -> typing.List[form_analyzer.ProcessedImage]:
    left = image.crop((0, 0, image.width // 2, image.height))
    right = image.crop((image.width // 2, 0, image.width, image.height))

    return [form_analyzer.ProcessedImage(left, '_1'), form_analyzer.ProcessedImage(right, '_2')]


if __name__ == '__main__':
    form_analyzer.pdf_to_image('results', image_processor=one_page_to_two)
    form_analyzer.run_textract('results')
    form_analyzer.dump_fields('results')
    form_analyzer.analyze('results', 'example_form')
