import os
import sys

# import a settings file, this just contains things like paths to the various config files
# and any other things users may need to change
import settings

from twisted.scripts.twistd import ServerOptions
from twisted.application import service
from twisted.python.runtime import platformType

# import platform specific twisted appstortlication runner
if platformType == "win32":
    from twisted.scripts._twistw import ServerOptions, WindowsApplicationRunner as _SomeApplicationRunner
else:
    from twisted.scripts._twistd_unix import ServerOptions, UnixApplicationRunner as _SomeApplicationRunner

# change graphite_root path if needed
if settings.GRAPHITE_ROOT is not None:
    os.environ["GRAPHITE_ROOT"] = settings.GRAPHITE_ROOT

GRAPHITE_ROOT = os.environ['GRAPHITE_ROOT']

print("$GRAPHITE_ROOT = %s" % GRAPHITE_ROOT)

# ensure that storage directory exists
STORAGEDIR = os.path.join(GRAPHITE_ROOT, 'storage')
if not os.path.exists(STORAGEDIR):
    os.makedirs(STORAGEDIR)


daemons = ['carbon-cache', 'carbon-aggregator'] # settings.CARBON_DAEMONS

print("Carbon Daemons = %s" % daemons)

topsvc = service.MultiService()

for program in daemons:
    twistd_options = ["--no_save", "--nodaemon", program]

    if settings.CARBON_CONFIG != None:
        twistd_options.append('--config='+settings.CARBON_CONFIG)

    config = ServerOptions()
    config.parseOptions(twistd_options)
    config['originalname'] = program

    plg = config.loadedPlugins[config.subCommand]
    ser = plg.makeService(config.subOptions)
    ser.setServiceParent(topsvc)

topsvc.startService()

from twisted.internet import reactor

reactor.run()
