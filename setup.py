#!/usr/bin/env python
from setuptools import setup #enables develop

req = ['nose','paramiko','numpy','matplotlib']

#%% install

setup(name='texcounts',
      packages=['texcounts'],
	  description='Count pages, figures, and tables for publication page count.',
	  author='Michael Hirsch, Ph.D.',
	  url='https://github.com/scienceopen/texcounts',
	  classifiers=[
	        'Programming Language :: Python :: 3.6',
	        ],
	  install_requires=req,
	  )
