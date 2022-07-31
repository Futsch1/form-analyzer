from form_analyzer.selectors import MultiSelect# form-analyzer

[![Python package](https://github.com/Futsch1/form-analyzer/actions/workflows/python-package.yml/badge.svg)](https://github.com/Futsch1/form-analyzer/actions/workflows/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/form-analyzer/badge/?version=latest)](https://form-analyzer.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/Futsch1/form-analyzer/badge.svg?branch=main)](https://coveralls.io/github/Futsch1/form-analyzer?branch=main)
[![Maintainability](https://api.codeclimate.com/v1/badges/743708a08f4e8fd7bf7e/maintainability)](https://codeclimate.com/github/Futsch1/form-analyzer/maintainability)

Python package to analyze scanned questionnaires and forms with AWS Textract and convert the results to an XLSX.

No thorough Python programming abilities are required, but a basic understanding is needed.

## Prerequisites

- Install form-analyzer using pip

```
pip install asn1editor
```

- Get an AWS account and create an access key (under security credentials)
- If your scanned questionnaires are in PDF format, install the required tools
  for [pdf2image](https://pypi.org/project/pdf2image/)

## Example

For a comprehensive example, see the 
[example folder in this project](https://github.com/Futsch1/form-analyzer/tree/main/example)

## Prepare questionnaires

In order to process your input data, the questionnaires need to be converted to a proper format.
form-analyzer requires PNG files for the upload to AWS Textract. If your data is already in this
format, make sure that their lexicographic order corresponds to the number of pages in your form.

Example:

```
Form1_Page1.png
Form1_Page2.png
Form1_Page3.png
Form2_Page1.png
Form2_Page2.png
Form2_Page3.png
```

### Convert PDF files

form-analyzer can convert PDF input files to properly named PNG files ready for upload. Each PDF
page can optionally be post-processed by a custom function to split pages.

Create a Python script like this to convert single page PDF files (assuming that the PDFs are located
in the folder "questionnaires":

```python
import form_analyzer

form_analyzer.pdf_to_image('questionnaires')
```

The following example shows how to split a single PDF page into two images:

```python
import form_analyzer


def one_page_to_two(_: int, image):
    left = image.crop((0, 0, image.width // 2, image.height))
    right = image.crop((image.width // 2, 0, image.width, image.height))

    return [form_analyzer.ProcessedImage(left, '_1'), form_analyzer.ProcessedImage(right, '_2')]


form_analyzer.pdf_to_image('questionnaires', image_processor=one_page_to_two)
```

The argument image_processor specifies a function that receives the current PDF page number (starting with 0)
and an [Image](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image) object.
It returns a list of form_analyzer.ProcessedImage objects that contain an Image object and a file name suffix.

The resulting images are stored in the same folder as the PDF source files.

## AWS Textract

The converted images can now be processed by AWS Textract to extract the form data. You can either
provide your AWS access key and region as parameters or set them up according to
[this manual](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html).

It is also possible to upload the images to an AWS S3 bucket and analyze them from there. If that's
desired, pass the S3 bucket name and an optional sub folder.

Assuming that the credentials are already set, this script will upload and process the data.

```python
import form_analyzer

form_analyzer.run_textract('questionnaires')
```

The result data is saved as JSON files in the target folder. Before using AWS Textract, the
function checks if result data is already present. If that is the case, the Textract call is skipped.

## Form description

In order to convert your form to a meaningful Excel file, form-analyzer needs to know the expected
form fields. A description has to be provided as a Python module.

This module needs to contain two variables:

- form_fields: The list of form fields
- keywords_per_page: A list of keywords to expect on each page

### form_fields variable

This variable is a list of FormField objects, which each describes a single field in the form. Each
FormField object consists of a title and a Selector object. The title is the column header in the Excel
file and the Selector defines the type of the form field and its location.

**_Important_**:
Note that the form description greatly affects the result of the form analyzing process. The AWS
Textract process often has slight errors and does not yield 100% correct results. The form descriptions
needs to account for that and on the one hand provide a detailed description of where to look for
form fields and on the other hand needs to keep search strings generic to help to detect the correct
field.

#### Selectors

Some selectors require a key and all require filter for initialization. The key is the label
of the form field which is searched in the extracted form data. It is recommended to not
indicate the full label but a unique part of it to compensate for potential detection errors.

- SingleSelect: Describes a list of checkboxes where only one may be marked
- MultiSelect: Describes a list of checkboxes where none, one or several may be marked
- TextField: Describes a text input box or input line where free text can be entered
- TextFieldWithCheckbox: Describes a text input field with an additional checkbox
- Number: Special case of TextField where only numbers may be entered
- Placeholder: Results in an empty column in the Excel file

For single and multi selects, additional and alternative text fields can be given. The 
content of the additional field is always added to the output and can be used to handle
optional free text fields. The alternative text field is used when no selection is made.
Both additional and alternative fields can be either TextField, Number or 
TextFieldWithCheckbox.

Note that all text matching will be done case-insensitive and with a certain fuzziness, so that
no exact match is required.

#### Filters

Filters restrict the extracted form fields to search for the current form field. The lower the number
of potential extracted form fields, the higher the probability of correct results.

Filters can be combined using the & (and) and | (or) operator.

- Page: Restricts the search to a certain page (page numbers starting with 0, so 0 is the first page)
- Pages: Restricts the search to a list of pages
- Location: Restricts the search to a part of the page indicated by horizontal and vertical ranges as page fractions.
- Selected: Restricts the search to fields which are selected checkboxes

Location filters apply to all selection possibilities for single and multi selects and to the label
for text and number fields.

#### Examples

```python
from form_analyzer.filters import *
from form_analyzer.selectors import *

# Single select on the first page with two options
single_select = SingleSelect(['First option', 'Second option'], 
                             Page(0))

# Multi select on the top half of the first page
multi_select = MultiSelect(['First option', 'Second option'],
                           Page(0) & Location(vertical=(.0, .5)))

# Text field on the upper left quarter of the first page
text_field = TextField('Field label',
                       Page(0) & Location(horizontal=(.0, .5), vertical=(.0, .5)))

# Single select on the lowest third of the second page or the top half of the third page
single_select_2 = SingleSelect(['First option', 'Second option', 'Third option'],
                               (Page(1) & Location(vertical=(.66, 1))) |
                               (Page(2) & Location(vertical=(.0, .5))))
```

### Keywords per page

The variable keywords_per_page in the form description is used to validate that a correct form is 
being analyzed. It is a list of a list of strings. For each page, a list of strings can be given 
where at least one of them has to be found in the strings discovered by Textract on the page.

If the list is empty or empty for a single page, no validation is performed.

Example

```python
# Will search for 'welcome' on the first page and for 'future' or 'past' on the second
keywords_per_page = [['welcome'], ['future', 'past']]
```

## Form analysis

The data returned from AWS Textract and the form description are the inputs for the final
analysis step that will try to locate all described form fields, get their value in the respective
filled forms and put this in an Excel file.

To run the analysis, use the following where the AWS Textract JSON files and PNGs are located
in the folder "questionnaires" and a Python module "my_form" exists in the Python search path 
that contains the form description.
(this should usually be the current folder, where a "my_form.py" is located).

```python
import form_analyzer

form_analyzer.analyze('questionnaires', 'my_form')
```
