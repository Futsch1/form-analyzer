import logging
from unittest import TestCase


class TestFormAnalyzer(TestCase):
    def test_analyze_fail(self):
        import form_analyzer
        form_analyzer.form_analyzer_logger.setLevel(logging.ERROR)

        with self.assertRaises(FileNotFoundError):
            form_analyzer.analyze('folder_does_not_exist', 'examples.example_form')

        with self.assertRaises(ModuleNotFoundError):
            form_analyzer.analyze('examples/results', 'module_not_there')

        with self.assertRaises(form_analyzer.FormDescriptionError):
            form_analyzer.analyze('examples/results', 'examples.example')
