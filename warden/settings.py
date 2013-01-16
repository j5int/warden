import platform
import logging

# WARDEN GENERAL
# ----------------

STDOUT_LEVEL = logging.INFO

# DIAMOND
# ----------------

DIAMOND_CONFIG = '/home/benm/.diamond/etc/diamond/diamond.conf'

DIAMOND_STDOUT_LEVEL = logging.ERROR

# GENTRY
# ----------------

GENTRY_SETTINGS_MODULE = 'gentry.settings'

# CARBON
# ----------------

GRAPHITE_ROOT = '/home/benm/.graphite'

# the path to the carbon config is derived from the GRAPHITE_ROOT unless defined here
CARBON_CONFIG = '/home/benm/.graphite/conf/carbon.conf'

# windows overrides

if platform.system() == 'Windows':
    GRAPHITE_ROOT = 'C:\\Graphite'
    CARBON_CONFIG = 'C:\\Graphite\\conf\\carbon.conf'
    DIAMOND_CONFIG = 'C:\\.diamond\\diamond.conf'
