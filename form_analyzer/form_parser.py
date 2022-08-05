import glob
import json
import logging
import os
import typing
from dataclasses import dataclass

import trp


@dataclass
class FieldWithPage:
    page: int
    field: trp.Field


FieldList = typing.List[FieldWithPage]


@dataclass
class ParsedForm:
    page_files: typing.List[str]
    fields: FieldList


@dataclass
class FormPages:
    pages: int
    words_on_page: typing.List[typing.List[str]]


def __get_field_list_from_document(document: trp.Document) -> typing.List[FieldList]:
    fields = []
    for page_num, page in enumerate(document.pages):
        for field in page.form.fields:
            fields.append(FieldWithPage(page_num, field))
        if page_num % 4 == 3:
            yield fields
            fields = []


def __is_any_word_in_blocks(blocks, words: typing.List[str]) -> bool:
    word_found = False

    for block in blocks:
        if any(['Text' in block and word in block['Text'] for word in words]):
            word_found = True

    return not len(words) or word_found


def __get_parsed_form(file_names: typing.List[str], form_pages: FormPages) -> ParsedForm:
    base_file_names = []
    responses = []

    for file_name in file_names:
        base_file_names.append(os.path.splitext(os.path.split(file_name)[1])[0])
        with open(file_name) as f:
            responses.append(json.load(f))

    doc = trp.Document(responses)
    for page, words in zip(doc.pages, form_pages.words_on_page):
        page: trp.Page
        assert __is_any_word_in_blocks(page.blocks, words), f'Words {words} not found in files {file_names}\n{page}'

    fields: FieldList = []
    for page_num, page in enumerate(doc.pages):
        for field in page.form.fields:
            fields.append((FieldWithPage(page_num, field)))
    return ParsedForm(base_file_names, fields)


def parse(path: str, form_pages: FormPages) -> typing.List[ParsedForm]:
    file_names = sorted(glob.glob(path + '/*.json'))

    from form_analyzer import form_analyzer_logger

    form_analyzer_logger.log(logging.INFO, f'Loading textract data for {len(file_names)} pages')

    if form_pages.pages == 0:
        form_pages.pages = len(file_names)
        form_pages.words_on_page = [] * len(file_names)
    else:
        if len(file_names) == 0:
            raise FileNotFoundError(f'No textract JSON result files found in {path}')

    for i in range(0, len(file_names), form_pages.pages):
        yield __get_parsed_form(file_names[i:i + form_pages.pages], form_pages)
