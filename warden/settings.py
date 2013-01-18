import platform
import logging

# WARDEN GENERAL
# ----------------

STDOUT_LEVEL = logging.DEBUG

# DIAMOND
# ----------------

DIAMOND_CONFIG = '~/.diamond/etc/diamond/diamond.conf'

DIAMOND_STDOUT_LEVEL = logging.ERROR

# GENTRY
# ----------------

GENTRY_SETTINGS_PATH = '~/work/venvs/gentrytest/lib/python2.7/site-packages/gentry-0.0.1-py2.7.egg/gentry/settings.py'
SENTRY_KEY_FILE = None

# CARBON
# ----------------

GRAPHITE_ROOT = '~/.graphite'

# the path to the carbon config is derived from the GRAPHITE_ROOT unless defined here
CARBON_CONFIG = '~/.graphite/conf/carbon.conf'

# windows overrides

if platform.system() == 'Windows':
    GRAPHITE_ROOT = 'C:\\Graphite'
    CARBON_CONFIG = 'C:\\Graphite\\conf\\carbon.conf'
    DIAMOND_CONFIG = 'C:\\.diamond\\diamond.conf'
