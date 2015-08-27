from manager import CollectorManager
from client import CollectorService
from twisted.python import log
import sys

class RegularBus:
    """
    bus = RegularBus()
    bus.start_trace()
    """

    def __init__(self, server, port, ignore_paths=None):
        self.manager = CollectorManager()
        self.service = CollectorService(
            manager=self.manager,
            server=server,
            port=port,
            debug=False)

    def lets_go(self):
        log.startLogging(sys.stdout)
        self.manager.start_trace()
        self.service.start()


