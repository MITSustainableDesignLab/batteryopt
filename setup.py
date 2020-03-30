from setuptools import setup

setup(
    name="batteryopt",
    version="0.1.0",
    packages=["batteryopt"],
    url="",
    license="MIT",
    author="Jakub Tomasz Szczesniak",
    author_email="jakubszc@mit.edu",
    description="",
    install_requires=["Click",],
    entry_points="""
        [console_scripts]
        batteryopt=batteryopt.cli:batteryopt
    """,
)
