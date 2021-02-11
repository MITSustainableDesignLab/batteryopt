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
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    entry_points="""
        [console_scripts]
        batteryopt=batteryopt.cli:batteryopt
    """,
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Researchers",
        "Topic :: Optimization :: Battery",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
