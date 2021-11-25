#!/usr/bin/env python3

from setuptools import setup, find_packages # type: ignore
import upf_pyperplan


long_description=\
"""============================================================
    UPF_PYPERPLAN
 ============================================================

    upf_pyperplan is a small package that allows an exchange of
    equivalent data structures between UPF and Pyperplan.
"""

setup(name='upf_pyperplan',
      version=upf_pyperplan.__version__,
      description='upf_pyperplan',
      author='UPF Team',
      author_email='info@upf.com',
      url='https://aiplan4eu.fbk.eu/',
      packages=['upf_pyperplan'],
      install_requires=['upf @ https://github.com/aiplan4eu/upf.git', 'pyperplan'],
      license='APACHE'
     )
