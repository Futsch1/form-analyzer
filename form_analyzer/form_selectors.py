import difflib
import enum
import typing
from abc import ABC
from dataclasses import dataclass

import trp

from .filter import Filter
from .forms import FieldList


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
    uncertain: bool = False


class SimpleField:
    def __init__(self, field: trp.Field):
        self.key = simple_str(field.key.text)
        self.selected = field.value.text != 'NOT_SELECTED' if field.value else True
        self.uncertain = field.confidence < 40

    def __repr__(self):
        return self.key + ' ' + ('selected' if self.selected else 'not selected')


class Selector:
    key = None

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:  # pragma: no cover
        raise NotImplementedError

    def headers(self) -> typing.List[str]:  # pragma: no cover
        raise NotImplementedError

    def get_page(self) -> int:  # pragma: no cover
        raise NotImplementedError


class Select(Selector, ABC):

    def __init__(self, selections: typing.List[str], filter_: Filter, alternative: 'Selector' = None,
                 additional: 'Selector' = None):
        self.selections = selections
        self.selection_matches = [Match.NOT_FOUND] * len(selections)
        self.uncertain_matches = []
        self.alternative = alternative
        self.additional = additional
        self.filter = filter_

    def get_page(self) -> int:
        return self.filter.get_page()

    def headers(self) -> typing.List[str]:
        if self.additional:
            return [self.additional.key]
        else:
            return []

    def _get_filtered_fields(self, form_fields: FieldList) -> typing.List[SimpleField]:
        return [SimpleField(field_with_page.field) for field_with_page in self.filter.filter(form_fields)]

    def _match_selections(self, simple_fields: typing.List[SimpleField]):
        self.selection_matches = [Match.NOT_FOUND] * len(self.selections)
        self.uncertain_matches = [False] * len(self.selections)

        for index, selection in enumerate(self.selections):
            simple_selection = simple_str(selection)

            # First pass: exact match
            decision = False
            for simple_field in simple_fields:
                if simple_field.key == simple_selection:
                    self.selection_matches[index] = Match.EXACT_SELECTED if simple_field.selected \
                        else Match.EXACT_NOT_SELECTED
                    self.uncertain_matches[index] = simple_field.uncertain
                    decision = True
                    break

            if not decision:
                max_ratio = 0.9
                # Second pass: similar match
                for simple_field in simple_fields:
                    s = difflib.SequenceMatcher(a=simple_selection, b=simple_field.key)
                    ratio = s.ratio()
                    if ratio > max_ratio:
                        self.selection_matches[index] = Match.SIMILAR_SELECTED if simple_field.selected \
                            else Match.SIMILAR_NOT_SELECTED
                        self.uncertain_matches[index] = simple_field.uncertain
                        decision = True
                        max_ratio = ratio

            if not decision and len(selection) > 15:
                # Third pass: part match
                for simple_field in simple_fields:
                    if simple_field.key in simple_selection:
                        self.selection_matches[index] = Match.SIMILAR_SELECTED if simple_field.selected \
                            else Match.SIMILAR_NOT_SELECTED
                        self.uncertain_matches[index] = simple_field.uncertain
                        break


class SingleSelect(Select):
    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        simple_fields = self._get_filtered_fields(form_fields)
        self._match_selections(simple_fields)

        # Find best matching fields
        try:
            select_index = self.selection_matches.index(Match.EXACT_SELECTED)
        except ValueError:
            try:
                select_index = self.selection_matches.index(Match.SIMILAR_SELECTED)
            except ValueError:
                select_index = None

        if select_index is not None:
            return_value = [FormValue(self.selections[select_index], self.uncertain_matches[select_index])]
        else:
            if self.alternative is not None:
                return_value = [self.alternative.values(form_fields)[0]]

            elif self.selection_matches.count(Match.NOT_FOUND) == 1:
                return_value = [FormValue(self.selections[self.selection_matches.index(Match.NOT_FOUND)], True)]

            else:
                return_value = [FormValue('', self.selection_matches.count(Match.NOT_FOUND) > 1)]

        if self.additional is not None:
            return_value.append(self.additional.values(form_fields)[0])

        return return_value


class MultiSelect(Select):
    def headers(self) -> typing.List[str]:
        return self.selections + super(MultiSelect, self).headers()

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        matches = []
        for i in range(len(self.selections) + 1):
            matches.append(FormValue(''))

        simple_fields = self._get_filtered_fields(form_fields)
        self._match_selections(simple_fields)

        any_found = False
        for index, match in enumerate(self.selection_matches):
            if match in [Match.EXACT_SELECTED, Match.SIMILAR_SELECTED]:
                matches[index + 1].value = '1'
                matches[index + 1].uncertain = self.uncertain_matches[index]
                any_found = True

        # If no matches were found, the matching item might be not detected - but only if there are some missing
        if not any_found and self.selection_matches.count(Match.NOT_FOUND) > 0:
            matches[0].uncertain = True

        if self.selection_matches.count(Match.NOT_FOUND) > 2:
            matches[0].uncertain = True

        if self.alternative is not None:
            matches[0] = self.alternative.values(form_fields)[0]

        if self.additional is not None:
            matches.append(self.additional.values(form_fields)[0])

        return matches


class TextField(Selector):
    def __init__(self, key: str, filter_: Filter):
        self.key = simple_str(key)
        self.filter = filter_

    def get_page(self) -> int:
        return self.filter.get_page()

    def headers(self) -> typing.List[str]:
        return []

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        uncertain = False
        v = ''

        filtered_fields = self.filter.filter(form_fields)
        for field_with_page in filtered_fields:
            tx_field = field_with_page.field
            if self.key in simple_str(tx_field.key.text):
                if tx_field.value is not None:
                    if tx_field.confidence < 40:
                        uncertain = True

                    if tx_field.value.text == 'NOT_SELECTED':
                        v = ''
                        uncertain = False
                    elif tx_field.value.text == 'SELECTED':
                        v = ''
                    else:
                        v = tx_field.value.text
                        if len(v) > 8:
                            uncertain = True
                        if len(v) == 0:
                            uncertain = False

                    break

        return [FormValue(v, uncertain)]


class TextFieldWithCheckbox(Selector):
    def __init__(self, key: str, filter_: Filter, separator: str = ':'):
        self.key = simple_str(key)
        self.separator = separator
        self.filter = filter_

    def get_page(self) -> int:
        return self.filter.get_page()

    def headers(self) -> typing.List[str]:
        return []

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        uncertain = False
        v = ''

        filtered_fields = self.filter.filter(form_fields)
        for field_with_page in filtered_fields:
            tx_field = field_with_page.field
            if self.key in simple_str(tx_field.key.text):
                if tx_field.confidence < 40:
                    uncertain = True

                if tx_field.value is not None and tx_field.value.text not in ['NOT_SELECTED', 'SELECTED']:
                    v = tx_field.value.text.strip()
                else:
                    v = tx_field.key.text.split(self.separator)[1]

                if len(v) > 8:
                    uncertain = True
                if len(v) == 0:
                    uncertain = False

                break

        return [FormValue(v, uncertain)]


class Number(TextField):
    def __init__(self, key: str, filter_: Filter, min_digits: int = 0, max_digits: int = 100):
        super(Number, self).__init__(key, filter_)
        self.min_digits = min_digits
        self.max_digits = max_digits

    def headers(self) -> typing.List[str]:
        return []

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        number_value = super(Number, self).values(form_fields)[0]
        if len(number_value.value):
            value = ''.join(list(filter(str.isdecimal, number_value.value.replace('O', '0'))))
            if self.min_digits > len(value) or self.max_digits < len(value):
                return [FormValue('', True)]
        else:
            return [FormValue('', True)]

        return [FormValue(value, number_value.uncertain)]


class Placeholder(Selector):
    def get_page(self) -> int:
        return 0

    def headers(self) -> typing.List[str]:
        return []

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        return [FormValue('', False)]
