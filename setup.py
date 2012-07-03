import ez_setup
ez_setup.use_setuptools()
from setuptools import setup, find_packages
import sys

setup(
    name = "Hello Shopply",
    version = 0.1,
    description = "Test Application",
    packages = find_packages(),
    author = "Carlos Aguilar",
    author_email = "caguilar@dwdandsolutions.com"
)
