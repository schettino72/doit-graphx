#! /usr/bin/env python

from setuptools import setup

setup(name='doit-graphx',
      description='doit command plugin to generate graphs of tasks using networkx',
      version='0.1.dev0',
      license='MIT',
      author='XXX',
      author_email='XXX',
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

      py_modules=['cmd_graphx'],
      # TODO: Fatcor-out matplotlib in an extra-requires.
      install_requires=['networkx', 'matplotlib'],
      # doit>=0.28.0] # doit 0.28 unreleased
      long_description="",
      )
