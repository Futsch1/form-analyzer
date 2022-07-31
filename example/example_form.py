from form_analyzer import FormField, FormFields
from form_analyzer.filters import Page, Location
from form_analyzer.selectors import SingleSelect, TextFieldWithCheckbox, MultiSelect, TextField, Placeholder

form_fields: FormFields = [
    FormField('Start with a single select',
              SingleSelect(['Option 1', 'Option 2', 'Option 3'],
                           Page(0) & Location(vertical=(.2, .4)),
                           alternative=TextFieldWithCheckbox('Other',
                                                             Page(0) & Location(
                                                                 vertical=(.2, .4))))
              ),
    FormField('And now a different one',
              SingleSelect(['Option 1', 'Option 2', 'Option 3'],
                           Page(0) & Location(vertical=(.4, .6)))
              ),
    FormField('First multi select',
              MultiSelect(['Either this way', 'Or that way', 'Or completely different'],
                          Page(0),
                          additional=TextFieldWithCheckbox('Other',
                                                           Page(0) & Location(
                                                               vertical=(.6, 1))))
              ),
    FormField('Some text',
              TextField('Now ask for some text', Page(0) | Page(1))
              ),
    FormField('Second multi select',
              MultiSelect(
                  ['Green', 'Red', 'Black', 'Yellow', 'Purple', 'Orange', 'White'],
                  Page(1))
              ),
    FormField('And a placeholder',
              Placeholder()
              )
]
keywords_per_page = [['example'], ['another']]
