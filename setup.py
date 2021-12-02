#!/usr/bin/env python3

from setuptools import setup # type: ignore


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
      author='AIPlan4EU Organization',
      author_email='aiplan4eu@fbk.eu',
      url='https://www.aiplan4eu-project.eu',
      packages=['upf_pyperplan'],
      install_requires=['pyperplan'],
      license='APACHE'
     )
