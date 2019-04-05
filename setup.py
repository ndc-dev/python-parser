import os
import io
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
def get_readme():
    path = os.path.join(here, 'README.md')
    with io.open(path, encoding='utf-8') as f:
        return '\n' + f.read()

setup(
    name='ndc_parser',
    version='0.1',
    description='NDC Parser',
    long_description=get_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/ndc-dev/python-parser',
    author='CALIL Inc.',
    author_email='info@calil.jp',
    license='MIT',
    keywords='NDC Nippon Decimal Classification Parser',
    packages=[
        "ndc_parser",
    ],
    install_requires=[],
)