import platform
import logging

# WARDEN GENERAL
# ----------------

STDOUT_LEVEL = logging.DEBUG

# DIAMOND
# ----------------
START_DIAMOND = False

DIAMOND_CONFIG = '/home/benm/.diamond/etc/diamond/diamond.conf'

# GENTRY
# ----------------
START_GENTRY = False

GENTRY_SETTINGS_MODULE = 'gentry.settings'

# CARBON
# at least carbon-cache is required to run the other threads
# ----------------

GRAPHITE_ROOT = '/home/benm/.graphite'

# 'carbon-cache' , 'carbon-aggregator' or 'carbon-relay'
CARBON_DAEMONS = ['carbon-cache', 'carbon-aggregator']

CARBON_CONFIG = '/home/benm/.graphite/conf/carbon.conf'

# windows overrides

if platform.system() == 'Windows':
    CARBON_CONFIG = 'C:\\Graphite\\conf\\carbon.conf'
    DIAMOND_CONFIG = 'C:\\.diamond\\diamond.conf'