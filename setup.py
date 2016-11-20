#!/usr/bin/env python
from setuptools import setup #enables develop
import subprocess

try:
    subprocess.call(['conda','install','--file','requirements.txt'])
except Exception as e:
    pass

#%% install

setup(name='texcounts',
	  description='Python wrapper for LOWTRAN7 atmosphere transmission model',
      packages=['texcounts']
	  )
