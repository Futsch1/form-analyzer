import enum
import typing
from dataclasses import dataclass

from form_analyzer.form_parser import FieldList, FieldWithPage


def simple_str(s: str) -> str:
    return ''.join(filter(lambda x: ord('a') <= ord(x) <= ord('z') or ord('0') <= ord(x) <= ord('9'), s.lower()))


class Match(enum.Enum):
    EXACT_SELECTED = 0
    EXACT_NOT_SELECTED = 1
    SIMILAR_SELECTED = 2
    SIMILAR_NOT_SELECTED = 3
    NOT_FOUND = 4


@dataclass
class FormValue:
    value: str
    page: int
    uncertain: bool = False


class SimpleField:
    def __init__(self, field_with_page: FieldWithPage):
        self.key = simple_str(field_with_page.field.key.text)
        self.selected = field_with_page.field.value.text != 'NOT_SELECTED' if field_with_page.field.value else True
        self.uncertain = field_with_page.field.confidence < 40
        self.page = field_with_page.page

    def __repr__(self):
        return self.key + ' ' + ('selected' if self.selected else 'not selected')


class Selector:
    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        raise NotImplementedError

    def headers(self) -> typing.List[str]:
        raise NotImplementedError


class Placeholder(Selector):
    """
    Placeholder selector

    This selector will appear as an empty column in the Excel sheet.
    """
    def headers(self) -> typing.List[str]:
        return []

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        return [FormValue('', 0, False)]
