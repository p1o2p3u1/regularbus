from collector import CoverageCollector
from client import CollectorService

class RegularBus:
    """
    bus = RegularBus()
    bus.start_trace()
    """

    def __init__(self, server, port):
        self.collector = CoverageCollector()
        self.service = CollectorService(
            harvest_data=self.collector.harvest_data,
            server=server,
            port=port,
            debug=False)

    def start_trace(self):
        self.collector.start()
        self.service.start()

if __name__ == '__main__':
    b = RegularBus('localhost', 9000)
    b.start_trace()
