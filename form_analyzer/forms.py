import glob
import json
import os
import typing
from dataclasses import dataclass

import trp

FieldList = typing.List[typing.Tuple[int, trp.Field]]


@dataclass
class ParsedForm:
    page_files: typing.List[str]
    fields: FieldList


@dataclass
class FormDescription:
    pages: int
    words_on_page: typing.List[typing.List[str]]


def get_field_list_from_document(document: trp.Document) -> typing.List[FieldList]:
    fields = []
    for page_num, page in enumerate(document.pages):
        for field in page.form.fields:
            fields.append((page_num, field))
        if page_num % 4 == 3:
            yield fields
            fields = []


def is_any_word_in_blocks(blocks, words: typing.List[str]) -> bool:
    if not len(words):
        return True

    for block in blocks:
        for word in words:
            if 'Text' in block and word in block['Text']:
                return True

    return False


def build(path: str, form_description: FormDescription) -> typing.List[ParsedForm]:
    file_names = sorted(glob.glob(path + '/*.json'))

    if form_description.pages == 0:
        form_description.pages = len(file_names)
        form_description.words_on_page = [] * len(file_names)

    for i in range(0, len(file_names), form_description.pages):
        base_file_names = []
        responses = []

        for page_index in range(form_description.pages):
            file_name = file_names[i + page_index]
            base_file_names.append(os.path.splitext(os.path.split(file_name)[1])[0])
            with open(file_name) as f:
                responses.append(json.load(f))

        doc = trp.Document(responses)
        for page, words in zip(doc.pages, form_description.words_on_page):
            assert is_any_word_in_blocks(page.blocks, words), f'Words {words} not found in page {page}'

        fields: FieldList = []
        for page_num, page in enumerate(doc.pages):
            for field in page.form.fields:
                fields.append((page_num, field))
        yield ParsedForm(base_file_names, fields)


