import logging
import typing

from . import forms
from openpyxl import Workbook


class FormDescriptionError(BaseException):
    pass


def __get_form_description(form_description: str):
    from form_analyzer import form_analyzer_logger

    form_analyzer_logger.log(logging.INFO, f'Loading form description from {form_description}')

    import importlib
    form = importlib.import_module(form_description)
    if 'form_items' not in dir(form):
        raise FormDescriptionError(f'Form description does not contain a "form_items" list')
    if 'keywords_per_page' not in dir(form):
        raise FormDescriptionError(f'Form description does not contain a "keywords_per_page" list')

    return form


def dump_fields(form_folder: str, form_description: typing.Optional[str] = None):
    if form_description is not None:
        form = __get_form_description(form_description)
        parsed_forms = forms.build(form_folder,
                                   forms.FormDescription(len(form.keywords_per_page), form.keywords_per_page))
    else:
        parsed_forms = forms.build(form_folder, forms.FormDescription(0, []))

    from form_analyzer import form_analyzer_logger

    form_analyzer_logger.log(logging.INFO, f'Dumping fields to {form_folder}')

    for parsed_form in parsed_forms:
        lines = []
        for page_num, field in sorted(parsed_form.fields, key=lambda x: str(x[0]) + x[1].key.text):
            value = '' if field.value is None else field.value.text
            lines.append(f'{page_num} {field.key.text}: {field.geometry.boundingBox.left} '
                         f'{field.geometry.boundingBox.top} {value} {field.confidence}')

        with open(f'{form_folder}/fields{parsed_form.page_files[0]}.txt', 'w') as f:
            f.write('\n'.join(lines))


def analyze(form_folder: str, form_description: str):
    from form_analyzer import form_analyzer_logger

    form = __get_form_description(form_description)
    parsed_forms = forms.build(form_folder, forms.FormDescription(len(form.keywords_per_page), form.keywords_per_page))

    wb = Workbook()
    sheet = wb.active
    sheet.title = 'Results'
    table_headers = ['']

    for field_name, form_field in form.form_items:
        table_headers.append(field_name)
        table_headers.extend(form_field.headers())
    sheet.append(table_headers)

    num_fields = 0
    uncertain_fields = []

    for parsed_form in parsed_forms:
        form_name = ", ".join(parsed_form.page_files)
        form_analyzer_logger.log(logging.INFO, f'Analyzing {form_name}')

        fields = parsed_form.fields

        table_line = [form_name]

        for _, form_field in form.form_items:
            values = form_field.values(fields)

            for i, value in enumerate(values):
                if value.uncertain:
                    uncertain_fields.append((sheet.max_row + 1, len(table_line) + 1 + i,
                                             parsed_form.page_files[form_field.get_page() - 1]))

            table_line.extend(list(map(lambda x: int(x.value) if x.value.isnumeric() else x.value, values)))
            num_fields += 1

        sheet.append(table_line)

    # Look for uncertain fields and add hyperlinks
    for uncertain in uncertain_fields:
        uncertain_cell = sheet.cell(row=uncertain[0], column=uncertain[1])
        uncertain_cell.hyperlink = f'{uncertain[2]}'
        try:
            if len(uncertain_cell.value) == 0:
                uncertain_cell.value = '???'
        except TypeError:
            pass
        uncertain_cell.style = 'Hyperlink'

    for row in sheet.rows:
        row[0].hyperlink = f'{row[0].value.split(",")[0]}'
        row[0].style = 'Hyperlink'

    form_analyzer_logger.log(logging.DEBUG, f'Found {len(uncertain_fields)} uncertain fields in total {num_fields} '
                                            f'fields')

    sheet.freeze_panes = "A2"
    sheet.print_title_rows = '1:1'

    results_file = f'{form_folder}/result.xlsx'
    form_analyzer_logger.log(logging.INFO, f'Finished. Results saved in {results_file}')
    wb.save(results_file)
