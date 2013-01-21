import platform
import logging

# WARDEN GENERAL
# ----------------

STDOUT_LEVEL = logging.DEBUG

# DIAMOND
# ----------------
# path to diamond.conf
DIAMOND_CONFIG = '~/.diamond/etc/diamond/diamond.conf'
# logging level of diamond. this produces a lot of logs if set to info/debug
DIAMOND_STDOUT_LEVEL = logging.ERROR

# GENTRY
# ----------------
# path to the gentry settings.py file
GENTRY_SETTINGS_PATH = '/home/benm/work/venvs/gentrytest/lib/python2.7/site-packages/gentry-0.0.1-py2.7.egg/gentry/settings.py'
# optional path to an overriding sentry secret key
SENTRY_KEY_FILE = None

# CARBON
# ----------------
# path to graphite root
GRAPHITE_ROOT = '~/.graphite'

# the path to the carbon config is derived from the GRAPHITE_ROOT unless defined here
CARBON_CONFIG = '~/.graphite/conf/carbon.conf'

# windows overrides

if platform.system() == 'Windows':
    GRAPHITE_ROOT = 'C:\\Graphite'
    CARBON_CONFIG = 'C:\\Graphite\\conf\\carbon.conf'
    DIAMOND_CONFIG = 'C:\\.diamond\\diamond.conf'
