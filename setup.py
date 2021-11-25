#!/usr/bin/env python3

from setuptools import setup, find_packages # type: ignore


long_description=\
"""============================================================
    UPF_PYPERPLAN
 ============================================================

    upf_pyperplan is a small package that allows an exchange of
    equivalent data structures between UPF and Pyperplan.
"""

VERSION = (0, 0, 1, "dev", 1)

# Try to provide human-readable version of latest commit for dev versions
# E.g. v0.5.1-4-g49a49f2-wip
#      * 4 commits after tag v0.5.1
#      * Latest commit "49a49f2"
#      * -wip: Working tree is dirty (non committed stuff)
# See: https://git-scm.com/docs/git-describe

if len(VERSION) == 5:
    import subprocess
    try:
        git_version = subprocess.check_output(["git", "describe",
                                               "--dirty=-wip"],
                                              stderr=subprocess.STDOUT)
        commits_from_tag = git_version.strip().decode('ascii')
        commits_from_tag = commits_from_tag.split("-")[1]
        VERSION = VERSION[:4] + (int(commits_from_tag),)
    except Exception as ex:
        pass

# PEP440 Format
__version__ = "%d.%d.%d.%s%d" % VERSION if len(VERSION) == 5 else \
              "%d.%d.%d" % VERSION[:3]

setup(name='upf_pyperplan',
      version=__version__,
      description='upf_pyperplan',
      author='UPF Team',
      author_email='info@upf.com',
      url='https://aiplan4eu.fbk.eu/',
      packages=['upf_pyperplan'],
      install_requires=['upf @ https://github.com/aiplan4eu/upf.git', 'pyperplan'],
      license='APACHE'
     )
