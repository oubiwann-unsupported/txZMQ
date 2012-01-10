from collections import deque

from zope.interface import implements

from zmq.core import constants
from zmq.core.context import Context

from twisted.internet import abstract, base, interfaces, reactor
from twisted.internet.protocol import connectionDone, Factory, Protocol


class ZMQReadWriteDescriptor(object):
    """
    """
    implements(interfaces.IReadWriteDescriptor)

    def __init__(self, zmqSocket):
        self.socket = zmqSocket
        self.fd = self.socket.getsockopt(constants.FD)
        self.queue = deque()

    def fileno(self):
        """
        @return: The platform-specified representation of a file descriptor
                 number.
        """
        return self.fd

    def _startWriting(self):
        """
        Start delivering messages from the queue.
        """
        while self.queue:
            try:
                self.socket.send(
                    self.queue[0][1], constants.NOBLOCK | self.queue[0][0])
            except error.ZMQError as e:
                if e.errno == constants.EAGAIN:
                    break
                self.queue.popleft()
                raise e
            self.queue.popleft()

    def doWrite(self, data):
        """
        Send message via ZeroMQ.

        @param message: message data
        """
        if not hasattr(message, '__iter__'):
            self.queue.append((0, message))
        else:
            self.queue.extend([(constants.SNDMORE, m) for m in message[:-1]])
            self.queue.append((0, message[-1]))

        # this is crazy hack: if we make such call, zeromq happily signals
        # available events on other connections
        self.socket.getsockopt(constants.EVENTS)

        self._startWriting()

    # backwards compatibility
    send = doWrite

    def _readMultipart(self):
        """
        Read multipart in non-blocking manner, returns with ready message
        or raising exception (in case of no more messages available).
        """
        while True:
            self.recv_parts.append(self.socket.recv(constants.NOBLOCK))
            if not self.socket.getsockopt(constants.RCVMORE):
                result, self.recv_parts = self.recv_parts, []

                return result

    def doRead(self):
        """
        Some data is available for reading on your descriptor.

        ZeroMQ is signalling that we should process some events.

        Part of L{IReadDescriptor}.
        """
        events = self.socket.getsockopt(constants.EVENTS)
        if (events & constants.POLLIN) == constants.POLLIN:
            while True:
                if self.factory is None:  # disconnected
                    return
                try:
                    message = self._readMultipart()
                except error.ZMQError as e:
                    if e.errno == constants.EAGAIN:
                        break

                    raise e

                log.callWithLogger(self, self.messageReceived, message)
        if (events & constants.POLLOUT) == constants.POLLOUT:
            self._startWriting()

    def logPrefix(self):
        """
        Part of L{ILoggingContext}.

        @return: Prefix used during log formatting to indicate context.
        @rtype: C{str}
        """
        return 'ZMQ'


class ZMQTransport(object):
    """
    """
    implements(interfaces.ITransport)

    def __init__(self, zmqSocket):
        self.fd = ZMQReadWriteDescriptor(zmqSocket)

    def write(self, data):
        """
        """
        self.fd.doWrite(data)

    def writeSequence(self, data):
        """
        """
        raise NotImplementedError()

    def loseConnection(self):
        """
        """
        self.fd.socket = None
        self.fd = None


class ZMQProtocol(Protocol):
    """
    """
    implements(interfaces.IProtocol)

    def connectionMade(self):
        pass

    def connectionLost(self, reason=connectionDone):
        """
        Called when the connection was lost.

        Part of L{IFileDescriptor}.

        This is called when the connection on a selectable object has been
        lost.  It will be called whether the connection was closed explicitly,
        an exception occurred in an event handler, or the other end of the
        connection closed it first.

        @param reason: A failure instance indicating the reason why the
                       connection was lost.  L{error.ConnectionLost} and
                       L{error.ConnectionDone} are of special note, but the
                       failure may be of other classes as well.
        """
        log.err(reason, "Connection to ZeroMQ lost in %r" % (self))
        if self.factory:
            self.factory.reactor.removeReader(self)

    def dataReceived(self, data):
        """
        Called on incoming data from ZeroMQ.

        @param data: message data
        """
        raise NotImplementedError(self)

    # backwards compatibility
    messageReceived = dataReceived

    def sendMessage(self, data):
        """
        """
        raise NotImplementedError(self)

    def getSocket(self):
        return self.transport.fd.socket


class ZMQFactory(Factory):
    """
    """
    implements(interfaces.IProtocolFactory)

    protocol = ZMQProtocol
    allowLoopbackMulticast = False
    multicastRate = 100
    highWaterMark = 0
    identity = None
    ioThreads = 1
    lingerPeriod = 100

    def __init__(self, socketType=None):
        self.socketType = socketType
        self.connections = set()
        self.context = Context(self.ioThreads)

    def startFactory(self):
        """
        """

    def stopFactory(self):
        """
        """

    def _createSocket(self):
        socket = Socket(self.context, self.socketType)
        socket.setsockopt(constants.LINGER, self.lingerPeriod)
        socket.setsockopt(
            constants.MCAST_LOOP, int(self.allowLoopbackMulticast))
        socket.setsockopt(constants.RATE, self.multicastRate)
        socket.setsockopt(constants.HWM, self.highWaterMark)
        if self.identity is not None:
            socket.setsockopt(constants.IDENTITY, self.identity)
        return socket

    def buildProtocol(self, addr=None):
        p = super(ZMQFactory, self).buildProtocol(addr)
        p.transport = ZMQTransport(self._createSocket())
        return p

    def shutdown(self):
        """
        Shutdown factory.

        This is shutting down all created connections
        and terminating ZeroMQ context.
        """
        for connection in self.connections.copy():
            connection.shutdown()

        self.connections = None

        self.context.term()
        self.context = None

    def registerForShutdown(self):
        """
        Register factory to be automatically shut down
        on reactor shutdown.
        """
        reactor.addSystemEventTrigger('during', 'shutdown', self.shutdown)


class ZMQBinder(abstract.FileDescriptor):
    """
    Analog to twisted.internet.tcp.Port
    """


class ZMQConnector(base.Connector):
    """
    Analog to twisted.internet.tcp.Connector
    """
