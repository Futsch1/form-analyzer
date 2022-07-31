import logging
import typing
from dataclasses import dataclass

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from . import form_parser
from .form_parser import ParsedForm
from .selectors.base import Selector


@dataclass
class FormField:
    title: str
    selector: Selector


FormFields = typing.List[FormField]


class FormDescriptionError(BaseException):
    pass


def __get_form_description_module(form_module_name: str):
    from form_analyzer import form_analyzer_logger

    form_analyzer_logger.log(logging.INFO, f'Loading form description from {form_module_name}')

    import importlib
    form = importlib.import_module(form_module_name)
    if 'form_fields' not in dir(form) or not isinstance(form.form_fields, list):
        raise FormDescriptionError('Form description does not contain a "form_fields" list')
    if 'keywords_per_page' not in dir(form) or not isinstance(form.keywords_per_page, list):
        raise FormDescriptionError('Form description does not contain a "keywords_per_page" list')

    return form


def __get_form(form_module_name: typing.Optional[str]) -> typing.Tuple[form_parser.FormPages, FormFields]:
    if form_module_name is not None:
        form = __get_form_description_module(form_module_name)
        form_keywords_per_page: typing.List[typing.List[str]] = form.keywords_per_page
        form_pages = form_parser.FormPages(len(form_keywords_per_page),
                                           form_keywords_per_page)
        form_fields = form.form_fields
    else:
        form_pages = form_parser.FormPages(0, [])
        form_fields = []

    return form_pages, form_fields


def __prepare_workbook(form_fields: FormFields) -> Workbook:
    wb = Workbook()
    sheet = wb.active
    sheet.title = 'Results'
    table_headers = ['']

    for form_field in form_fields:
        table_headers.append(form_field.title)
        table_headers.extend(form_field.selector.headers())
    sheet.append(table_headers)

    return wb


class FormToSheet:
    @dataclass
    class UncertainField:
        col: int
        page_file: str

    def __init__(self, sheet: Worksheet, form_fields: FormFields):
        self.__sheet = sheet
        self.__form_fields = form_fields
        self.num_fields = 0
        self.uncertain_fields = 0

    def __get_table_line(self, form_name: str, parsed_form: ParsedForm) -> \
            typing.Tuple[typing.List[str], typing.List[UncertainField]]:
        table_line = [form_name]
        uncertain_fields = []

        for form_field in self.__form_fields:
            values = form_field.selector.values(parsed_form.fields)

            uncertain_fields.extend([FormToSheet.UncertainField(len(table_line) + i,
                                                                parsed_form.page_files[value.page])
                                     for i, value in enumerate(values) if value.uncertain])

            table_line.extend(list(map(lambda x: int(x.value) if x.value.isnumeric() else x.value, values)))
            self.num_fields += 1

        return table_line, uncertain_fields

    @staticmethod
    def __annotate_uncertain_fields(uncertain_fields: typing.List[UncertainField], row):
        for uncertain in uncertain_fields:
            uncertain_cell = row[uncertain.col]
            uncertain_cell.hyperlink = f'{uncertain.page_file}'
            try:
                if len(uncertain_cell.value) == 0:
                    uncertain_cell.value = '???'
            except TypeError:
                pass
            uncertain_cell.style = 'Hyperlink'

    def add_parsed_form(self, form_name: str, parsed_form: ParsedForm):
        table_line, uncertain_fields = self.__get_table_line(form_name, parsed_form)
        self.__sheet.append(table_line)
        row = self.__sheet[self.__sheet.max_row]

        self.__annotate_uncertain_fields(uncertain_fields, row)

        row[0].hyperlink = f'{row[0].value.split(",")[0]}'
        row[0].style = 'Hyperlink'

        self.uncertain_fields += len(uncertain_fields)


def dump_fields(form_folder: str, form_description_module_name: typing.Optional[str] = None):
    """
    Dumps the analyzed fields from AWS Textract to text files to support debugging.

    :param form_folder: Folder with the AWS Textract result files
    :param form_description_module_name: Optional form description module name
    """
    form_pages, _ = __get_form(form_description_module_name)
    parsed_forms = form_parser.parse(form_folder, form_pages)

    from form_analyzer import form_analyzer_logger

    form_analyzer_logger.log(logging.INFO, f'Dumping fields to {form_folder}')

    for parsed_form in parsed_forms:
        lines = []
        for field_with_page in sorted(parsed_form.fields, key=lambda tx_field_: str(tx_field_.page) + tx_field_.field.key.text):
            tx_field = field_with_page.field
            value = '' if tx_field.value is None else tx_field.value.text
            lines.append(f'{field_with_page.page} {tx_field.key.text}: {tx_field.geometry.boundingBox.left} '
                         f'{tx_field.geometry.boundingBox.top} {value} {tx_field.confidence}')

        with open(f'{form_folder}/fields{parsed_form.page_files[0]}.txt', 'w') as f:
            f.write('\n'.join(lines))


def analyze(form_folder: str, form_description_module_name: str, excel_file_name: str = 'results'):
    """
    Analyzes the AWS Textract results in a folder based on a given form description and writes the results to
    an Excel file.

    :param form_folder: Folder with the AWS Textract result files
    :param form_description_module_name: Name of the form description Python module
    :param excel_file_name: Name of the result Excel file, default is 'results'
    """
    from form_analyzer import form_analyzer_logger

    form_pages, form_fields = __get_form(form_description_module_name)

    parsed_forms = form_parser.parse(form_folder, form_pages)

    wb = __prepare_workbook(form_fields)
    sheet = wb.active

    form_to_sheet = FormToSheet(sheet, form_fields)

    for parsed_form in parsed_forms:
        form_name = ", ".join(parsed_form.page_files)
        form_analyzer_logger.log(logging.INFO, f'Analyzing {form_name}')

        form_to_sheet.add_parsed_form(form_name, parsed_form)

    form_analyzer_logger.log(logging.DEBUG,
                             f'Found {form_to_sheet.uncertain_fields} uncertain fields in total '
                             f'{form_to_sheet.num_fields} fields')

    sheet.freeze_panes = "A2"
    sheet.print_title_rows = '1:1'

    results_file = f'{form_folder}/{excel_file_name}.xlsx'
    form_analyzer_logger.log(logging.INFO, f'Finished. Results saved in {results_file}')
    wb.save(results_file)
