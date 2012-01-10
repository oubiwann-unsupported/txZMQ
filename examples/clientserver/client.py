import zmq

from twisted.internet import reactor

from txzmq.endpoints import ZMQClientEndpoint
from txzmq.protocol import ZMQProtocol, ZMQFactory


class ClientGreeter(ZMQProtocol):
    def sendMessage(self, msg):
        self.transport.write("MESSAGE %s\n" % msg)


class ClientGreeterFactory(ZMQFactory):
    protocol = ClientGreeter


def gotProtocol(p):
    p.sendMessage("Hello")
    reactor.callLater(1, p.sendMessage, "This is sent in one second")
    reactor.callLater(2, p.transport.loseConnection)


endpoint = ZMQClientEndpoint(reactor, "tcp://localhost:5555", timeout=30)
deferred = endpoint.connect(ClientGreeterFactory(socketType=zmq.REQ))
deferred.addCallback(gotProtocol)
reactor.run()
