import re

from setuptools import find_packages
from setuptools import setup


def find_version():
    return re.search(r'^__version__ = "(.*)"$',
                     open('form_analyzer/__init__.py', 'r').read(),
                     re.MULTILINE).group(1)


setup(name='form-analyzer',
      version=find_version(),
      description='Python package to analyze scanned questionnaires and forms with AWS Textract and convert the '
                  'results to an XLSX.',
      long_description=open('README.md', 'r').read(),
      long_description_content_type='text/markdown',
      author='Florian Fetz',
      author_email='florian.fetz@gmail.com',
      license='MIT',
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'Topic :: Scientific/Engineering :: Image Processing'
      ],
      keywords=['textract', 'AWS', 'form', 'questionnaire', 'xlsx', 'excel'],
      url='https://github.com/futsch1/form-analyzer',
      project_urls={'Documentation': 'http://form-analyzer.rtfd.io'},
      packages=find_packages(exclude=['tests', 'example']),
      include_package_data=True,
      install_requires=[
          'boto3',
          'amazon-textract-caller',
          'amazon-textract-response-parser',
          'pdf2image',
          'openpyxl'
      ],
      test_suite="tests",
      python_requires='>=3.6',
      entry_points={

      })
