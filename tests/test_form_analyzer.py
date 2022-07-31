import logging
from unittest import TestCase

import example.example_form
import form_analyzer


class TestFormAnalyzer(TestCase):
    def setUp(self) -> None:
        form_analyzer.form_analyzer_logger.setLevel(logging.ERROR)

    def test_analyze_fail(self):
        with self.assertRaises(FileNotFoundError):
            form_analyzer.analyze('folder_does_not_exist', 'example.example_form')

        with self.assertRaises(ModuleNotFoundError):
            form_analyzer.analyze('example/results', 'module_not_there')

        with self.assertRaises(form_analyzer.FormDescriptionError):
            form_analyzer.analyze('example/results', 'example.example')

    def test_keywords(self):
        for i in range(len(example.example_form.keywords_per_page)):
            keywords = example.example_form.keywords_per_page[i]
            example.example_form.keywords_per_page[i] = ['some weird text']

            with self.assertRaises(AssertionError):
                form_analyzer.analyze('example/results', 'example.example_form')

            example.example_form.keywords_per_page[i] = keywords

        del example.example_form.keywords_per_page
        with self.assertRaises(form_analyzer.FormDescriptionError):
            form_analyzer.analyze('example/results', 'example.example_form')

    def test_dump_fields(self):
        form_analyzer.dump_fields('example/results', 'example.example_form')
        form_analyzer.dump_fields('example/results', None)

    def test_example(self):
        form_analyzer.analyze('example/results', 'example.example_form')