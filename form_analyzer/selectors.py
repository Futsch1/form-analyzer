import difflib
import enum
import typing
from abc import ABC
from dataclasses import dataclass

from .filters import Filter
from .form_parser import FieldList, FieldWithPage


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
    def values(self, form_fields: FieldList) -> typing.List[FormValue]:  # pragma: no cover
        raise NotImplementedError

    def headers(self) -> typing.List[str]:  # pragma: no cover
        raise NotImplementedError


class Select(Selector, ABC):
    @dataclass
    class SelectionMatch:
        match: Match
        page: int = 0
        uncertain: bool = True

        def __eq__(self, other):
            return self.match == other.match

    def __init__(self, selections: typing.List[str], filter_: Filter, alternative: typing.Union['TextField', 'TextFieldWithCheckbox'] = None,
                 additional: typing.Union['TextField', 'TextFieldWithCheckbox'] = None):
        self.selections = selections
        self.selection_matches = [Select.SelectionMatch(Match.NOT_FOUND)] * len(self.selections)
        self.alternative = alternative
        self.additional: TextField = additional
        self.filter = filter_

    def headers(self) -> typing.List[str]:
        if self.additional:
            return [self.additional.label]
        else:
            return []

    def _get_filtered_fields(self, form_fields: FieldList) -> typing.List[SimpleField]:
        return [SimpleField(field_with_page) for field_with_page in self.filter.filter(form_fields)]

    def __check_exact_match(self, simple_selection: str, index: int, simple_fields: typing.List[SimpleField]) -> bool:
        for simple_field in simple_fields:
            if simple_field.key == simple_selection:
                self.selection_matches[index] = Select.SelectionMatch(
                    Match.EXACT_SELECTED if simple_field.selected else Match.EXACT_NOT_SELECTED,
                    simple_field.page, simple_field.uncertain)
                return True

        return False

    def __check_similar_match(self, simple_selection: str, index: int, simple_fields: typing.List[SimpleField]) -> bool:
        match_found = False
        max_ratio = 0.9
        # Second pass: similar match
        for simple_field in simple_fields:
            s = difflib.SequenceMatcher(a=simple_selection, b=simple_field.key)
            ratio = s.ratio()
            if ratio > max_ratio:
                self.selection_matches[index] = Select.SelectionMatch(
                    Match.SIMILAR_SELECTED if simple_field.selected else Match.SIMILAR_NOT_SELECTED,
                    simple_field.page, simple_field.uncertain)
                max_ratio = ratio
                match_found = True

        return match_found

    def __check_part_match(self, simple_selection: str, index: int, simple_fields: typing.List[SimpleField]):
        for simple_field in simple_fields:
            if simple_field.key in simple_selection:
                self.selection_matches[index] = Select.SelectionMatch(
                    Match.SIMILAR_SELECTED if simple_field.selected else Match.SIMILAR_NOT_SELECTED,
                    simple_field.page, simple_field.uncertain)
                break

    def _match_selections(self, simple_fields: typing.List[SimpleField]):
        self.selection_matches = [Select.SelectionMatch(Match.NOT_FOUND)] * len(self.selections)

        for index, selection in enumerate(self.selections):
            simple_selection = simple_str(selection)

            if not self.__check_exact_match(simple_selection, index, simple_fields) and \
                    not self.__check_similar_match(simple_selection, index, simple_fields) and \
                    len(selection) > 15:
                self.__check_part_match(simple_selection, index, simple_fields)


class SingleSelect(Select):
    """
    This selector handles single-select fields in a form.

    It requires a list of selections where one can be selected. The selected field will
    be represented as its value in the resulting Excel column.

    It is possible to indicate an alternative selector that will be used if no selection was found (i.e.
    to give a free text).

    :param selections: List of possible selections
    :param filter_: Filter
    :param alternative: Alternative text field that is used when no selection was found
    :param additional: Additional text field whose content is always added to the result
    """
    def __init__(self, selections: typing.List[str], filter_: Filter, alternative: typing.Union['TextField', 'TextFieldWithCheckbox'] = None,
                 additional: typing.Union['TextField', 'TextFieldWithCheckbox'] = None):
        super().__init__(selections, filter_, alternative, additional)

    def __form_value_from_match(self, select_index: int) -> FormValue:
        return FormValue(self.selections[select_index], self.selection_matches[select_index].page,
                         self.selection_matches[select_index].uncertain,
                         )

    def __get_matched_select_index(self) -> typing.Optional[int]:
        try:
            select_index = self.selection_matches.index(Select.SelectionMatch(Match.EXACT_SELECTED))
        except ValueError:
            try:
                select_index = self.selection_matches.index(Select.SelectionMatch(Match.SIMILAR_SELECTED))
            except ValueError:
                select_index = None
        return select_index

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        simple_fields = self._get_filtered_fields(form_fields)
        self._match_selections(simple_fields)

        # Find best matching fields
        select_index = self.__get_matched_select_index()

        if select_index is not None:
            return_value = [self.__form_value_from_match(select_index)]
        else:
            # No selection found, try alternatives
            not_found_match = Select.SelectionMatch(Match.NOT_FOUND)

            # Alternative field given, take that one.
            if self.alternative is not None:
                return_value = [self.alternative.values(form_fields)[0]]

            elif self.selection_matches.count(not_found_match) == 1:
                select_index = self.selection_matches.index(not_found_match)
                return_value = [self.__form_value_from_match(select_index)]

            else:
                return_value = [FormValue('', simple_fields[0].page, self.selection_matches.count(not_found_match) > 1)]

        if self.additional is not None:
            return_value.append(self.additional.values(form_fields)[0])

        return return_value


class MultiSelect(Select):
    """
    This selector handles multi-select fields in a form.

    It requires a list of selections where none or several can be selected. Each selected field
    will be represented by a "1" in the resulting Excel column.

    It is possible to indicate an alternative selector that will be used if no selection was found (i.e.
    to give a free text).

    :param selections: List of possible selections
    :param filter_: Filter
    :param alternative: Alternative text field that is used when no selection was found
    :param additional: Additional text field whose content is always added to the result
    """
    def __init__(self, selections: typing.List[str], filter_: Filter, alternative: typing.Union['TextField', 'TextFieldWithCheckbox'] = None,
                 additional: typing.Union['TextField', 'TextFieldWithCheckbox'] = None):
        super().__init__(selections, filter_, alternative, additional)

    def headers(self) -> typing.List[str]:
        return self.selections + super(MultiSelect, self).headers()

    def __check_exact_or_part_match(self, matches) -> bool:
        match_found = False
        for index, match in enumerate(self.selection_matches):
            if match.match in [Match.EXACT_SELECTED, Match.SIMILAR_SELECTED]:
                matches[index + 1] = FormValue('1', match.page, match.uncertain)
                match_found = True
        return match_found

    @staticmethod
    def __populate_matches(num_matches: int):
        matches = []
        for i in range(num_matches):
            matches.append(FormValue('', 0))

        return matches

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        matches = self.__populate_matches(len(self.selections) + 1)

        simple_fields = self._get_filtered_fields(form_fields)
        self._match_selections(simple_fields)

        any_found = self.__check_exact_or_part_match(matches)

        # If no matches were found, the matching item might be not detected - but only if there are some missing
        not_found_match = Select.SelectionMatch(Match.NOT_FOUND)
        if not any_found and self.selection_matches.count(not_found_match) > 0:
            matches[0].uncertain = True

        if self.selection_matches.count(not_found_match) > 2:
            matches[0].uncertain = True

        if self.alternative is not None:
            matches[0] = self.alternative.values(form_fields)[0]

        if self.additional is not None:
            matches.append(self.additional.values(form_fields)[0])

        return matches


class TextField(Selector):
    """
    Simple text field which is identified by a field label.

    :param label: Label of the text field
    :param filter_: Filter
    """
    def __init__(self, label: str, filter_: Filter):
        self.label = simple_str(label)
        self.filter = filter_

    def headers(self) -> typing.List[str]:
        return []

    @staticmethod
    def __form_value_from_match(field_with_page: FieldWithPage) -> FormValue:
        tx_field = field_with_page.field
        uncertain = tx_field.confidence < 40

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

        return FormValue(v, field_with_page.page, uncertain)

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        filtered_fields = self.filter.filter(form_fields)
        form_value = FormValue('', filtered_fields[0].page, False)

        for field_with_page in filtered_fields:
            tx_field = field_with_page.field

            if self.label in simple_str(tx_field.key.text):
                if tx_field.value is not None:
                    form_value = self.__form_value_from_match(field_with_page)
                    break

        return [form_value]


class TextFieldWithCheckbox(Selector):
    """
    Text field with an additional checkbox.

    The indicated text is always returned, if it shall only be done when the checkbox is selected,
    use the Selected filter.

    :param label: Label of the text field
    :param filter_: Filter
    :param separator: Separator between the checkbox with label and the free text, default ':'
    """
    def __init__(self, label: str, filter_: Filter, separator: str = ':'):
        self.label = simple_str(label)
        self.separator = separator
        self.filter = filter_

    def headers(self) -> typing.List[str]:
        return []

    def __form_value_from_match(self, field_with_page: FieldWithPage) -> FormValue:
        tx_field = field_with_page.field
        uncertain = tx_field.confidence < 40

        if tx_field.value is not None and tx_field.value.text not in ['NOT_SELECTED', 'SELECTED']:
            v = tx_field.value.text.strip()
        else:
            v = tx_field.key.text.split(self.separator)[1]

        if len(v) > 8:
            uncertain = True
        if len(v) == 0:
            uncertain = False

        return FormValue(v, field_with_page.page, uncertain)

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        filtered_fields = self.filter.filter(form_fields)
        form_value = FormValue('', filtered_fields[0].page, False)

        for field_with_page in filtered_fields:
            tx_field = field_with_page.field
            if self.label in simple_str(tx_field.key.text):
                form_value = self.__form_value_from_match(field_with_page)
                break

        return [form_value]


class Number(TextField):
    """
    Number field which is identified by a field label.

    To check the validity of a number, the minimum and maximum number of digits can be indicated.

    :param label: Number field label
    :param filter_: Filter
    :param min_digits: Minimum number of digits, set to 0 to ignore, default is 0
    :param max_digits: Maximum number of digits, set to 0 to ignore, default is 0
    """
    def __init__(self, label: str, filter_: Filter, min_digits: int = 0, max_digits: int = 100):
        super(Number, self).__init__(label, filter_)
        self.min_digits = min_digits
        self.max_digits = max_digits

    def headers(self) -> typing.List[str]:
        return []

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        number_value = super(Number, self).values(form_fields)[0]
        if len(number_value.value):
            value = ''.join(list(filter(str.isdecimal, number_value.value.replace('O', '0'))))
            if self.min_digits > len(value) or self.max_digits < len(value):
                return [FormValue('', number_value.page, True)]
        else:
            return [FormValue('', number_value.page, True)]

        return [FormValue(value, number_value.page, number_value.uncertain)]


class Placeholder(Selector):
    """
    Placeholder selector

    This selector will appear as an empty column in the Excel sheet.
    """
    def headers(self) -> typing.List[str]:
        return []

    def values(self, form_fields: FieldList) -> typing.List[FormValue]:
        return [FormValue('', 0, False)]
