from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import sys
from twisted.python import log
from twisted.internet import reactor, task

from threading import Thread
import json

class BusStation(WebSocketServerProtocol):

    def __init__(self, harvest_data):
        self.cov_data = {}
        self.timer = None
        self.task = task.LoopingCall(self._collect_data)
        self.harvest_data = harvest_data
        self.interval = 1

    def onConnect(self, request):
        pass

    def onOpen(self):
        if self.task and not self.task.running:
            self.task.start(self.interval)

    def onMessage(self, payload, isBinary):
        if self.task and self.task.running:
            self.task.stop()
            try:
                self.interval = int(payload)
            except (TypeError, ValueError):
                self.interval = 1
            self.task.start(self.interval)

    def onClose(self, wasClean, code, reason):
        if self.task and self.task.running:
            self.task.stop()

    def _collect_data(self):
        self.cov_data = self.harvest_data()
        # The ensure_ascii == False option allows the JSON serializer
        # to use Unicode strings. We can do this since we are encoding
        # to UTF8 afterwards anyway. And UTF8 can represent the full
        # Unicode character set.
        s = json.dumps(self.cov_data, ensure_ascii=False).encode('utf8')
        self.sendMessage(s, False)

class BusStationFactory(WebSocketServerFactory):

    def __init__(self, harvest_data, url=None, debug=True, debugCodePaths=True):
        self.harvest_data = harvest_data
        self.protocol = BusStation(self.harvest_data)
        WebSocketServerFactory.__init__(self, url=url, debug=debug, debugCodePaths=debugCodePaths)

    def buildProtocol(self, addr):
        self.protocol.factory = self
        return self.protocol

class CollectorService:

    def __init__(self, harvest_data, server, port, debug):
        self.server = server
        self.port = port
        self.factory = BusStationFactory(harvest_data, "ws://%s:%d" % (self.server, self.port), debug=debug)
        self.reactor = reactor
        self.reactor.listenTCP(port, self.factory)
        self.thread = Thread(target=self.reactor.run, args=(False,))

    def start(self):
        self.thread.start()

    def stop(self):
        pass

if __name__ == "__main__":

    def baby():
        return {1: 1}

    log.startLogging(sys.stdout)
    factory = BusStationFactory(baby, "ws://localhost:9000", debug=False)
    reactor.listenTCP(9000, factory)

    Thread(target=reactor.run, args=(False,)).start()
    print("thread started")
