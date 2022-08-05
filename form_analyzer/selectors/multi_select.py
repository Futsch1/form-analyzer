import typing

from form_analyzer.filters import Filter
from form_analyzer.form_parser import FieldList
from form_analyzer.selectors.base import Match, FormValue
from form_analyzer.selectors.select_base import Select
from form_analyzer.selectors.text_fields import TextField, TextFieldWithCheckbox


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
        matches[0].page = form_fields[0].page

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
