from form_analyzer import FormItem, FormDescription
from form_analyzer.filters import Page, Location
from form_analyzer.selectors import SingleSelect, TextFieldWithCheckbox, MultiSelect, TextField, Placeholder

form_description: FormDescription = [
    FormItem('Start with a single select',
             SingleSelect(['Option 1', 'Option 2', 'Option 3'],
                          Page(1) & Location(top=(.2, .4)),
                          alternative=TextFieldWithCheckbox('Other',
                                                            Page(1) & Location(
                                                                top=(.2, .4))))
             ),
    FormItem('And now a different one',
             SingleSelect(['Option 1', 'Option 2', 'Option 3'],
                          Page(1) & Location(top=(.4, .6)))
             ),
    FormItem('First multi select',
             MultiSelect(['Either this way', 'Or that way', 'Or completely different'],
                         Page(1),
                         additional=TextFieldWithCheckbox('Other',
                                                          Page(1) & Location(
                                                              top=(.6, 1))))
             ),
    FormItem('Some text',
             TextField('Now ask for some text', Page(1) | Page(2))
             ),
    FormItem('Second multi select',
             MultiSelect(
                 ['Green', 'Red', 'Black', 'Yellow', 'Purple', 'Orange', 'White'],
                 Page(2))
             ),
    FormItem('And a placeholder',
             Placeholder()
             )
]
keywords_per_page = [['example'], ['another']]
