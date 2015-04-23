#! /usr/bin/env python
import io
import os

from setuptools import setup

mydir = os.path.dirname(__file__)


def read_project_version():
    # Version-trick to have version-info in a single place.
    # http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package
    fglobals = {}
    with io.open(os.path.join(mydir, '_version.py')) as fd:
        exec(fd.read(), fglobals)  # To read __version__
    return fglobals['__version__']

setup(name='doit-graphx',
      description="doit command plugin to generate task dependency-graphs using networkx",
      version=read_project_version(),
      license='MIT',
      author='Kostis Anagnostopoulos',
      author_email='ankostis@gmail.com',
      url='https://github.com/pydoit/doit-graphx',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: Science/Research',
          'Intended Audience :: System Administrators',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Software Development :: Testing',
          'Topic :: Software Development :: Quality Assurance',
          'Topic :: Scientific/Engineering',
      ],

      py_modules=['cmd_graphx', '_version'],
      # TODO: Fatcor-out matplotlib in an extra-requires.
      install_requires=['networkx', 'matplotlib'],
      # doit>=0.28.0] # doit 0.28 unreleased
      long_description="",
      )
