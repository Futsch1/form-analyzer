import logging
from unittest import TestCase

import examples.example_form
import form_analyzer


class TestFormAnalyzer(TestCase):
    def setUp(self) -> None:
        form_analyzer.form_analyzer_logger.setLevel(logging.ERROR)

    def test_analyze_fail(self):
        with self.assertRaises(FileNotFoundError):
            form_analyzer.analyze('folder_does_not_exist', 'examples.example_form')

        with self.assertRaises(ModuleNotFoundError):
            form_analyzer.analyze('examples/results', 'module_not_there')

        with self.assertRaises(form_analyzer.FormDescriptionError):
            form_analyzer.analyze('examples/results', 'examples.example')

    def test_keywords(self):
        for i in range(len(examples.example_form.keywords_per_page)):
            keywords = examples.example_form.keywords_per_page[i]
            examples.example_form.keywords_per_page[i] = ['some weird text']

            with self.assertRaises(AssertionError):
                form_analyzer.analyze('examples/results', 'examples.example_form')

            examples.example_form.keywords_per_page[i] = keywords

        del examples.example_form.keywords_per_page
        with self.assertRaises(form_analyzer.FormDescriptionError):
            form_analyzer.analyze('examples/results', 'examples.example_form')

    def test_dump_fields(self):
        form_analyzer.dump_fields('examples/results', 'examples.example_form')
        form_analyzer.dump_fields('examples/results', None)

    def test_example(self):
        form_analyzer.analyze('examples/results', 'examples.example_form')