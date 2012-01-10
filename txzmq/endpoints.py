class ZMQEndpoint(object):
    """
    """
    def __init__(self, reactor, address):
        self._reactor = reactor
        if isinstance(address, basestring):
            address = [address]
        self._addresses = address


class ZMQClientEndpoint(ZMQEndpoint):
    """
    Example usage:

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
    deferred = endpoint.connect(ClientGreeterFactory())
    deferred.addCallback(gotProtocol)
    reactor.run()
    """
    def __init__(self, reactor, address, timeout=30):
        super(ZMQClientEndpoint, self).__init__(reactor, address)
        self._timeout = timeout

    def connect(self, factory):
        socket = factory.protocol.getSocket()
        for address in self._addresses:
            socket.connect(address)
            

class ZMQServerEndpoint(ZMQEndpoint):
    """
    Example usage:

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
    endpoint.listen(ServerGreeterFactory())
    reactor.run()
    """
    def listen(self, factory):
        socket = factory.protocol.getSocket()
        for address in self._addresses:
            socket.bind(address)
