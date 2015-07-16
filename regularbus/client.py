from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import sys
from twisted.python import log
from twisted.internet import reactor, task

from threading import Thread
import json

class BusStation(WebSocketServerProtocol):

    def __init__(self, harvest_data):
        self.data = {}
        self.timer = None
        self.task = task.LoopingCall(self._collect_data)
        self.harvest_data = harvest_data

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open, start sending collect data")
        self.task.start(1)

    def onMessage(self, payload, isBinary):
        pass

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        self.task.stop()
        print("send collect data stopped.")

    def _collect_data(self):
        self.data = {
            "file1.py": {
                "code": [1, 2, 3, 4, 5],
                "executed": [1, 2, 3, 4],
                "missing": [5],
                "coverage": 0.8
            }
        }
        self.data = self.harvest_data()
        # The ensure_ascii == False option allows the JSON serializer
        # to use Unicode strings. We can do this since we are encoding
        # to UTF8 afterwards anyway. And UTF8 can represent the full
        # Unicode character set.
        s = json.dumps(self.data, ensure_ascii=False).encode('utf8')
        print s
        self.sendMessage(s, False)
        print("send complete")

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

    def start(self):
        Thread(target=self.reactor.run, args=(False,)).start()
        print("socket service started on %s:%d" % (self.server, self.port))

if __name__ == "__main__":

    def baby():
        return {1: 1}

    log.startLogging(sys.stdout)
    factory = BusStationFactory(baby, "ws://localhost:9000", debug=False)
    reactor.listenTCP(9000, factory)

    Thread(target=reactor.run, args=(False,)).start()
    print("thread started")
