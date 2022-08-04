import typing

from form_analyzer.filters import Filter
from form_analyzer.form_parser import FieldWithPage, FieldList
from form_analyzer.selectors.base import Selector, simple_str, FormValue


class TextField(Selector):
    """
    Simple text field which is identified by a field label.

    :param label: Label of the text field
    :param filter_: Filter
    """
    def __init__(self, label: str, filter_: Filter):
        self.label = label
        self.simple_label = simple_str(label)
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

            if self.simple_label in simple_str(tx_field.key.text) and tx_field.value is not None:
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
        self.label = label
        self.simple_label = simple_str(label)
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
            if self.simple_label in simple_str(tx_field.key.text):
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
