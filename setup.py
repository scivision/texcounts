#!/usr/bin/env python
req = ['nose','paramiko','numpy','matplotlib']

import pip
try:
    import conda.cli
    conda.cli.main('install',*req)
except Exception as e:    
    pip.main(['install'] + req)

#%% install
from setuptools import setup #enables develop

setup(name='texcounts',
      packages=['texcounts'],
	  description='Count pages, figures, and tables for publication page count.',
	  author='Michael Hirsch, Ph.D.',
	  url='https://github.com/scivision/texcounts',
	  classifiers=[
	        'Programming Language :: Python :: 3.6',
	        ],
	  )
