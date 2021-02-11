import codecs
import os
from os import path

from setuptools import setup, find_packages

here = os.getcwd()
# Get the long description from the README file
with codecs.open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()
with open(path.join(here, "requirements.txt")) as f:
    requirements_lines = f.readlines()
install_requires = [r.strip() for r in requirements_lines]

setup(
    name="batteryopt",
    version="0.1.0",
    packages=find_packages(),
    url="https://github.com/MITSustainableDesignLab/batteryopt",
    license="MIT",
    author="Jakub Tomasz Szczesniak",
    author_email="jakubszc@mit.edu",
    description="battery operation optimization",
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    entry_points="""
        [console_scripts]
        batteryopt=batteryopt.cli:batteryopt
    """,
)
