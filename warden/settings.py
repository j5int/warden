import platform
import logging

# WARDEN GENERAL
# ----------------

STDOUT_LEVEL = logging.DEBUG

# CARBON
# ----------------

# 'carbon-cache' , 'carbon-aggregator' or 'carbon-relay'
CARBON_DAEMONS = ['carbon-cache', 'carbon-aggregator']

CARBON_CONFIG = '~/.graphite/conf/carbon.conf'

# GENTRY
# ----------------

GENTRY_SETTINGS_MODULE = 'gentry.settings'

# DIAMOND
# ----------------

DIAMOND_CONFIG = '~/.diamond/etc/diamond/diamond.conf'

# windows overrides

if platform.system() == 'Windows':
    CARBON_CONFIG = 'C:\\Graphite\\conf\\carbon.conf'
    DIAMOND_CONFIG = 'C:\\.diamond\\diamond.conf'