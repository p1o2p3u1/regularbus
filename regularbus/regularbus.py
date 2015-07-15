from coverage import coverage

class RegularBus:
    """
    bus = RegularBus()
    bus.start_trace()
    """
    def __init__(self):
        self.coverage = coverage()

    def start_trace(self):
        self.coverage.start()
