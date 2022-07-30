import typing
from copy import copy

from .form_parser import FieldList


class Filter:
    def __init__(self):
        self.__operations: typing.List[typing.Tuple[str, Filter]] = []

    def __and__(self, other):
        self.__operations.append(('and', other))
        return self

    def __or__(self, other):
        self.__operations.append(('or', other))
        return copy(self)

    def filter(self, fields: FieldList) -> FieldList:
        filtered_fields = self._filter(fields)
        for operation, other in self.__operations:
            if operation == 'and':
                filtered_fields = other.filter(filtered_fields)
            if operation == 'or':
                filtered_fields.extend(other.filter(fields))

        return filtered_fields

    def _filter(self, fields: FieldList) -> FieldList:
        raise NotImplementedError


class Pages(Filter):
    def __init__(self, pages: typing.List[int]):
        super(Pages, self).__init__()
        self.__pages = pages

    def _filter(self, fields: FieldList) -> FieldList:
        filtered_fields = []
        for field in fields:
            if field.page in self.__pages:
                filtered_fields.append(field)

        return filtered_fields


class Page(Pages):
    def __init__(self, page: int):
        super(Page, self).__init__([page])


class Location(Filter):
    optional_dimension = typing.Optional[typing.Tuple[float, float]]

    def __init__(self, horizontal: optional_dimension = None, vertical: optional_dimension = None):
        super(Location, self).__init__()
        self.__horizontal = horizontal
        self.__vertical = vertical

    def _filter(self, fields: FieldList) -> FieldList:
        filtered_fields = []
        for field in fields:
            tx_field = field.field
            if (self.__horizontal is None or self.__horizontal[0] < tx_field.geometry.boundingBox.left <
                self.__horizontal[1]) and \
                    (self.__vertical is None or self.__vertical[0] < tx_field.geometry.boundingBox.top <
                     self.__vertical[1]):
                filtered_fields.append(field)

        return filtered_fields


class Selected(Filter):
    def _filter(self, fields: FieldList) -> FieldList:
        filtered_fields = []
        for field in fields:
            tx_field = field.field
            if tx_field.value is not None and tx_field.value.text == 'SELECTED':
                filtered_fields.append(field)

        return filtered_fields
