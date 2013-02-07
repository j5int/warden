from setuptools import setup
import re

def get_version():
    VERSIONFILE="warden/__init__.py"
    initfile_lines = open(VERSIONFILE, "rt").readlines()
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    for line in initfile_lines:
        mo = re.search(VSRE, line, re.M)
        if mo:
            return mo.group(1)
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

def check_fault_requires():
    pass

setup(
    name             = 'warden',
    version          = get_version(),
    license          =  'MIT',
    description      = 'A set of tools for monitoring Python applications, and shipping events to Sentry and metrics to Graphite',
    long_description = \
"""
Warden is a Python application that monitors other Python applications running locally, and ships events to a Sentry instance and metrics to a Graphite instance.

Warden uses Diamond to collect stats. Using Diamond's plug-in Collectors architecture, many stats can be collected and custom Collectors added.
""",
#Finally, there is an API that can be used by the monitored application to publish events, and do some internal checks (e.g. for stuck threads).
    author           = 'Richard Graham',
    author_email     = 'support@sjsoft.com',
    packages         = ['warden', 'warden.smtp_forwarder'],
    zip_safe = False,
    install_requires = [
          'carbon==0.9.10-warden',
          'gentry==0.0.1',
          'diamond'],
    dependency_links = [
        'http://github.com/richg/gentry/tarball/master#egg=gentry-0.0.1',
        'http://github.com/richg/carbon/tarball/0.9.x-warden#egg=carbon-0.9.10-warden',
        'http://github.com/richg/Diamond/tarball/master#egg=diamond'
    ],
    keywords         = 'sentry carbon graphite monitoring',
    url              = 'https://github.com/richg/warden',
    entry_points     = {
          'console_scripts': [
              'warden = warden.warden:main',
              'warden_setup = warden.warden_setup:main'
          ]
    },
    classifiers      = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Environment :: Web Environment',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: System :: Monitoring',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
