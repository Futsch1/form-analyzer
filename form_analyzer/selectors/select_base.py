import difflib
import typing
from abc import ABC
from dataclasses import dataclass

from form_analyzer.filters import Filter
from form_analyzer.form_parser import FieldList
from form_analyzer.selectors.text_fields import TextField, TextFieldWithCheckbox
from form_analyzer.selectors.base import Selector, Match, SimpleField, simple_str


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

    def _get_first_found_page(self) -> int:
        for selection_match in self.selection_matches:
            if selection_match.match != Match.NOT_FOUND:
                return selection_match.page

        return 0
