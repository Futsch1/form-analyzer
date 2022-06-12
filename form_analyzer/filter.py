import typing
from copy import copy

from forms import FieldList


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

    def get_page(self):
        page = self._get_page()
        if page is None:
            for _, other in self.__operations:
                page = other.get_page()
                if page is not None:
                    break
        return page

    def _get_page(self):
        return None

    def _filter(self, fields: FieldList) -> FieldList:
        raise NotImplementedError


class Pages(Filter):
    def __init__(self, pages: typing.List[int]):
        super(Pages, self).__init__()
        self.__pages = pages

    def _get_page(self):
        return self.__pages[0]

    def _filter(self, fields: FieldList) -> FieldList:
        filtered_fields = []
        for field in fields:
            if field[0] + 1 in self.__pages:
                filtered_fields.append(field)

        return filtered_fields


class Page(Pages):
    def __init__(self, page: int):
        super(Page, self).__init__([page])


class Location(Filter):
    optional_dimension = typing.Optional[typing.Tuple[float, float]]

    def __init__(self, left: optional_dimension = None, top: optional_dimension = None):
        super(Location, self).__init__()
        self.__left = left
        self.__top = top

    def get_page(self):
        return None

    def _filter(self, fields: FieldList) -> FieldList:
        filtered_fields = []
        for field_ in fields:
            field = field_[1]
            if (self.__left is None or self.__left[0] < field.geometry.boundingBox.left < self.__left[1]) and \
                    (self.__top is None or self.__top[0] < field.geometry.boundingBox.top < self.__top[1]):
                filtered_fields.append(field_)

        return filtered_fields


class Selected(Filter):
    def _filter(self, fields: FieldList) -> FieldList:
        filtered_fields = []
        for field_ in fields:
            field = field_[1]
            if field.value is not None and field.value.text == 'SELECTED':
                filtered_fields.append(field_)

        return filtered_fields

