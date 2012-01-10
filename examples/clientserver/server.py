#!/usr/bin/env python
import zmq

from twisted.internet import reactor

from txzmq.endpoints import ZMQServerEndpoint
from txzmq.protocol import ZMQProtocol, ZMQFactory


class ServerGreeter(ZMQProtocol):
    def connectionMade(self):
        self.transport.write("Thanks for connecting!\r\n") 
        self.transport.loseConnection()


class ServerGreeterFactory(ZMQFactory):
    protocol = ServerGreeter


class ServerGreeter(ZMQProtocol):
    def sendMessage(self, msg):
        self.transport.write("MESSAGE %s\n" % msg)


endpoint = ZMQServerEndpoint(reactor, "tcp://*:5555")
endpoint.listen(ServerGreeterFactory(socketType=zmq.REP))
reactor.run()
