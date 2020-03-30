from setuptools import setup, find_packages

setup(
    name="batteryopt",
    version="0.1.0",
    packages=find_packages(),
    url="",
    license="MIT",
    author="Jakub Tomasz Szczesniak",
    author_email="jakubszc@mit.edu",
    description="",
    install_requires=["Click", 'pandas'],
    entry_points="""
        [console_scripts]
        batteryopt=batteryopt.cli:batteryopt
    """,
)
