#!/usr/bin/env python3

from setuptools import setup # type: ignore

upf_commit = 'e5cfd58ac83cfd96556fd4461517b4c1a5330bfb'


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
      install_requires=[f'upf@git+https://github.com/aiplan4eu/upf.git@{upf_commit}', 'pyperplan'],
      license='APACHE'
     )
