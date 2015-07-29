from collector import CoverageCollector
from client import CollectorService

class RegularBus:
    """
    bus = RegularBus()
    bus.start_trace()
    """

    def __init__(self, server, port, ignore_paths=None):
        self.collector = CoverageCollector(ignore_paths=ignore_paths)
        self.service = CollectorService(
            harvest_data=self.collector.harvest_data,
            server=server,
            port=port,
            debug=False)

    def lets_go(self):
        self.collector.start()
        self.service.start()

if __name__ == '__main__':
    b = RegularBus('localhost', 9000)
    b.lets_go()
    print("trace started")
