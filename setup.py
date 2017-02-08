#!/usr/bin/env python
from setuptools import setup #enables develop
try:
    import conda.cli
    conda.cli.main('install','--file','requirements.txt')
except Exception as e:
    print(e)
    import pip
    pip.main(['install','-r','requirements.txt'])

#%% install

setup(name='texcounts',
	  description='Count pages, figures, and tables for publication page count.',
	  author='Michael Hirsch, Ph.D.',
	  url='https://github.com/scienceopen/texcounts',
	  classifiers=[
	        'Programming Language :: Python :: 3.6',
	        ],
      packages=['texcounts'],
	  )
