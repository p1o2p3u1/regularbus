from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import sys
from twisted.python import log
from twisted.internet import reactor, task
from threading import Thread
import json


class BusStation(WebSocketServerProtocol):

    def __init__(self):
        self.cov_task = task.LoopingCall(self._collect_cov_data)
        self.graph_task = task.LoopingCall(self._collect_graph_image)
        self.cov_interval = 1
        self.trace_filter = {}

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, is_binary):
        """
        receive message from client. Payload should be json string with the following format:
        {
            "op": "filter",
            "files": []
        }
        :param payload:
        :param is_binary:
        :return:
        """
        print payload
        s = json.loads(payload)
        op = s['op']

        if op == "files":
            # init display files
            if self.cov_task and self.cov_task.running:
                self.cov_task.stop()

            self.trace_filter.clear()
            files = s['files']
            for f in files:
                self.trace_filter[f] = None

            self.cov_task.start(self.cov_interval)
            #  send back the current cov data for debugging
            cov_data = self.factory.manager.harvest_coverage_data()
            s = json.dumps(cov_data, ensure_ascii=False).encode('utf8')
            self.sendMessage(s, False)

        elif op == "interval":
            # reset coverage interval
            try:
                self.cov_interval = int(s['interval'])
            except (TypeError, ValueError):
                self.cov_interval = 1
            if self.cov_task and self.cov_task.running:
                self.cov_task.stop()
            self.cov_task.start(self.cov_interval)

        elif op == "pause":
            # pause coverage task
            if self.cov_task and self.cov_task.running:
                self.cov_task.stop()
                print "coverage task paused"

        elif op == "resume":
            # resume coverage task
            if self.cov_task and not self.cov_task.running:
                self.cov_task.start(self.cov_interval)
                print "coverage task resumed"

        elif op == "start":
            # start coverage task
            if self.cov_task and not self.cov_task.running:
                self.cov_task.start(self.cov_interval)
                print "coverage task started"

        elif op == "stop":
            # stop coverage task
            if self.cov_task and self.cov_task.running:
                self.cov_task.stop()
                print "coverage task stopped"

        elif op == "start trace":
            self.factory.manager.do_call_graph = True
            self.graph_task.start(self.cov_interval)

        elif op == "stop trace":
            self.factory.manager.do_call_graph = False
            graph = self.factory.manager.harvest_call_graph_data()
            print json.dumps(graph)
            self.graph_task.stop()
        else:
            pass

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        if self.cov_task and self.cov_task.running:
            self.cov_task.stop()

    def _collect_cov_data(self):
        cov_data = self.factory.manager.harvest_coverage_data()
        result = {k: v for k, v in cov_data.iteritems() if k in self.trace_filter}
        # The ensure_ascii == False option allows the JSON serializer
        # to use Unicode strings. We can do this since we are encoding
        # to UTF8 afterwards anyway. And UTF8 can represent the full
        # Unicode character set.
        s = json.dumps(result, ensure_ascii=False).encode('utf8')
        self.sendMessage(s, False)

    def _collect_graph_image(self):
        image = self.factory.manager.harvest_graph()
        # send binary image to the client
        self.sendMessage(image, isBinary=True)


class CollectorService:

    def __init__(self, manager, server, port, debug):
        self.factory = WebSocketServerFactory("ws://%s:%d" % (server, port), debug=debug)
        self.factory.protocol = BusStation
        self.factory.manager = manager
        self.reactor = reactor
        self.reactor.listenTCP(port, self.factory)
        self.thread = Thread(target=self.reactor.run, args=(False,))

    def start(self):
        self.thread.setDaemon(True)
        self.thread.start()

    def stop(self):
        # stop when the game server stop
        pass

if __name__ == "__main__":

    def baby():
        return {1: 1}

    log.startLogging(sys.stdout)
    factory = WebSocketServerFactory("ws://localhost:9000", debug=False)
    reactor.listenTCP(9000, factory)

    Thread(target=reactor.run, args=(False,)).start()
    print("thread started")
