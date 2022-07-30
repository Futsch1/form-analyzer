# form-analyzer

[![Coverage Status](https://coveralls.io/repos/github/Futsch1/form-analyzer/badge.svg?branch=main)](https://coveralls.io/github/Futsch1/form-analyzer?branch=main)
[![Maintainability](https://api.codeclimate.com/v1/badges/743708a08f4e8fd7bf7e/maintainability)](https://codeclimate.com/github/Futsch1/form-analyzer/maintainability)

Python package to analyze scanned questionnaires and forms with AWS Textract and convert the results to an XLSX.

No thorough Python programming abilities are required, but a basic understanding is needed.

## Prerequisites

- Install form-analyzer using pip

```commandline
pip install asn1editor
```

- Get an AWS account and create an access key (under security credentials)
- If your scanned questionnaires are in PDF format, install the required tools for [pdf2image](https://pypi.org/project/pdf2image/)

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
- form_description: The description itself
- keywords_per_page: A list of keywords to expect on each page

### form_description variable

This variable is a list of FormItem objects, which each describes a single field in the form. Each
FormItem object consists of a title and a Selector object. The title is the column header in the Excel
file and the Selector defines the type of the form item and its location.

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

#### Filters

Filters restrict the extracted form fields to search for the current form item. The lower the number
of potential extracted form fields, the higher the probability of correct results.

Filters can be combined using the & (and) and | (or) operator.

- Page: Restricts the search to a certain page (page numbers starting with 0, so 0 is the first page)
- Pages: Restricts the search to a list of pages
- Location: Restricts the search to a part of the page indicated by horizontal and vertical ranges as page fractions.
- Selected: Restricts the search to fields which are selected checkboxes

#### Examples

SingleSelect on the first page:

```python
from form_analyzer.filters import *
from form_analyzer.selectors import *

single_select_on_first_page = SingleSelect(['First option', 'Second option'], Page(0))

multi_select_on_top_half_of_second_page = MultiSelect(['First option', 'Second option'], 
                                                      Page(0) & Location(vertical=(.0, .5)))
text_field_on_top_left_half_of_first_page = TextField('Field label', 
                                                      Page(0) & Location(horizontal=(.0, .5), vertical=(.0, .5)))

```