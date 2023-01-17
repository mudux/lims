from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in lims/__init__.py
from lims import __version__ as version

setup(
	name='lims',
	version=version,
	description='Lab Information Management System',
	author='erp@mtrh.go.ke',
	author_email='erp@mtrh.go.ke',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
