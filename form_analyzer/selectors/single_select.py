import typing

from form_analyzer.filters import Filter
from form_analyzer.form_parser import FieldList
from form_analyzer.selectors.base import FormValue, Match
from form_analyzer.selectors.select_base import Select
from form_analyzer.selectors.text_fields import TextField, TextFieldWithCheckbox


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
