from zope.interface import implements

from os.path import exists
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from carbon import service
from carbon import conf


from twisted.application.internet import TCPServer, TCPClient, UDPServer
from twisted.internet.protocol import ServerFactory
from twisted.application.service import MultiService

from carbon import util, state, events, instrumentation
from carbon.log import carbonLogObserver
state.events = events
state.instrumentation = instrumentation

class CarbonCombinedServiceMaker(object):

    implements(IServiceMaker, IPlugin)
    tapname = "carbon-combined"
    description = "Collect stats for graphite."
    options = conf.CarbonAggregatorOptions

    def makeService(self, options):

        from carbon.cache import MetricCache
        from carbon.conf import settings
        from carbon.protocols import CacheManagementHandler
        from carbon.aggregator import receiver
        from carbon.aggregator.rules import RuleManager
        from carbon.routers import ConsistentHashingRouter
        from carbon.client import CarbonClientManager
        from carbon.rewrite import RewriteRuleManager

        # Configure application components
        events.metricReceived.addHandler(MetricCache.store)

        root_service = service.createBaseService(None)
        factory = ServerFactory()
        factory.protocol = CacheManagementHandler
        svc = TCPServer(int(settings.CACHE_QUERY_PORT), factory, interface=settings.CACHE_QUERY_INTERFACE)
        svc.setServiceParent(root_service)

        # have to import this *after* settings are defined
        from carbon.writer import WriterService

        svc = WriterService()
        svc.setServiceParent(root_service)

        if settings.USE_FLOW_CONTROL:
            events.cacheFull.addHandler(events.pauseReceivingMetrics)
            events.cacheSpaceAvailable.addHandler(events.resumeReceivingMetrics)


        router = ConsistentHashingRouter()
        client_manager = CarbonClientManager(router)
        client_manager.setServiceParent(root_service)

        events.metricReceived.addHandler(receiver.process)
        events.metricGenerated.addHandler(client_manager.sendDatapoint)

        RuleManager.read_from(settings["aggregation-rules"])
        if exists(settings["rewrite-rules"]):
            RewriteRuleManager.read_from(settings["rewrite-rules"])

        if not settings.DESTINATIONS:
            raise Exception("Required setting DESTINATIONS is missing from carbon.conf")

        for destination in util.parseDestinations(settings.DESTINATIONS):
            client_manager.startClient(destination)

        return root_service


# Now construct an object which *provides* the relevant interfaces
serviceMaker = CarbonCombinedServiceMaker()
