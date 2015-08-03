from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import sys
from twisted.python import log
from twisted.internet import reactor, task
from threading import Thread
import json
from collector import CoverageCollector


class BusStation(WebSocketServerProtocol):

    def __init__(self):
        self.cov_task = task.LoopingCall(self._collect_data)
        self.cov_collector = CoverageCollector()
        self.cov_interval = 1
        self.cov_peer = None

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))
        self.cov_peer = request.peer

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
        if op == "add":
            # add a new file to display
            self.cov_collector.add_cov_file(s['files'])

        elif op == "clear":
            # clear the trace data
            self.cov_collector.clear()

        elif op == "filter":
            # init display files
            self.cov_collector.init_cov_files(s['files'])

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

        elif op == "start_trace":
            # start trace, set the trace function to sys.settrace
            self.cov_collector.start_trace()

        elif op == "stop":
            # stop coverage task
            if self.cov_task and self.cov_task.running:
                self.cov_task.stop()
                print "coverage task stopped"

        elif op == "stop_trace":
            # stop trace, set None to sys.settrace
            self.cov_collector.stop_trace()

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        if self.cov_task and self.cov_task.running:
            self.cov_task.stop()

    def _collect_data(self):
        cov_data = self.cov_collector.harvest_data()
        # The ensure_ascii == False option allows the JSON serializer
        # to use Unicode strings. We can do this since we are encoding
        # to UTF8 afterwards anyway. And UTF8 can represent the full
        # Unicode character set.
        s = json.dumps(cov_data, ensure_ascii=False).encode('utf8')
        self.sendMessage(s, False)


class CollectorService:

    def __init__(self, server, port, debug):
        self.factory = WebSocketServerFactory("ws://%s:%d" % (server, port), debug=debug)
        self.factory.protocol = BusStation
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
