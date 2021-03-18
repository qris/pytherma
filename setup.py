""" Setuptools configuration for pyTherma. """

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytherma",  # Replace with your own username
    version="0.0.1",
    author="Chris Wilson",
    author_email="chris+pytherma@qwirx.com",
    description=("A Python library and tools for communicating with a Daikin Altherma ASHP "
                 "using serial commands."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/qris/pytherma",
    packages=setuptools.find_namespace_packages(include=["pytherma.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # f-strings
    # As pytherma is a library, dependencies are expressed here:
    # https://pipenv.pypa.io/en/latest/advanced/#pipfile-vs-setup-py
    install_requires=[
        "more_itertools",
        "pySerial>=3.4",
        "sqlalchemy",
    ],
)
