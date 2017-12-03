#!/usr/bin/env python
install_requires = ['numpy','matplotlib']
#%% install
from setuptools import setup,find_packages

setup(name='texcounts',
      packages=find_packages(),
	  description='Count pages, figures, and tables for publication page count.',
	  author='Michael Hirsch, Ph.D.',
	  url='https://github.com/scivision/texcounts',
	  classifiers=[
	        'Programming Language :: Python :: 3.6',
	        ],
      install_requires=install_requires,
      python_requires='>=3.6',
      extras_require={'ssh':['paramiko'],},
	  )
