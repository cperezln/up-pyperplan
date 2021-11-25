#!/usr/bin/env python3

from setuptools import setup, find_packages # type: ignore


long_description=\
"""============================================================
    UPF_PYPERPLAN
 ============================================================

    upf_pyperplan is a small package that allows an exchange of
    equivalent data structures between UPF and Pyperplan.
"""

setup(name='upf_pyperplan',
      version='0.0.1',
      description='upf_pyperplan',
      author='UPF Team',
      author_email='info@upf.com',
      url='https://aiplan4eu.fbk.eu/',
      packages=['upf_pyperplan'],
      install_requires=['upf@git+https://github.com/aiplan4eu/upf.git@6b712922217df6b3e4e78eb8c14c652756b230a7', 'pyperplan'],
      license='APACHE'
     )
