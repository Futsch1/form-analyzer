from form_analyzer.filter import Page, Location
from form_analyzer.form_selectors import SingleSelect, TextFieldWithCheckbox, MultiSelect, TextField

form_items = [('Start with a single select',
               SingleSelect(['Option 1', 'Option 2', 'Option 3'], Page(1) & Location(top=(.2, .4)),
                            alternative=TextFieldWithCheckbox('Other', Page(1) & Location(top=(.2, .4))))
               ),
              ('And now a different one',
               SingleSelect(['Option 1', 'Option 2', 'Option 3'], Page(1) & Location(top=(.4, .6)))
               ),
              ('First multi select',
               MultiSelect(['Either this way', 'Or that way', 'Or completely different'], Page(1),
                           additional=TextFieldWithCheckbox('Other', Page(1) & Location(top=(.6, 1))))
               ),
              ('Some text',
               TextField('Now ask for some text', Page(1))
               ),
              ('Second multi select',
               MultiSelect(['Green', 'Red', 'Black', 'Yellow', 'Purple', 'Orange', 'White'], Page(2))
               )
              ]
keywords_per_page = [['example'], ['another']]
