import os
from setuptools import setup


DIR = os.path.dirname(__name__)
with open(f"{DIR}README.md", "r") as f:
    description = f.read()

setup(
    name="xnr-cryptowrapper",
    version="0.1.0",
    install_requires=[
        "requests>=2.21.0",
        "requests-async>=0.2.0",
        "requests-cache>=0.4.13",
    ],
    description="Wrapper around Cryptocurrency related APIs",
    py_modules=["cryptowrapper"],
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/xnr-k/cryptowrapper",
    author="xnr-k",
    author_email="xnr.k@protonmail.com"
)
