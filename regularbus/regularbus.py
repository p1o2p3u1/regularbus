from manager import CollectorManager
from client import CollectorService

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
        self.manager.start_trace()
        self.service.start()

if __name__ == '__main__':
    b = RegularBus('localhost', 9000)
    b.lets_go()
    print("trace started")
