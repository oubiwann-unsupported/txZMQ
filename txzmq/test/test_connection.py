"""
Tests for L{txzmq.connection}.
"""
from zmq.core import constants

from zope.interface import verify as ziv

from twisted.internet.interfaces import IFileDescriptor, IReadDescriptor
from twisted.trial import unittest

from txzmq import exceptions
from txzmq.connection import BIND, CONNECT, ZmqAddress, ZmqConnection
from txzmq.factory import ZmqFactory
from txzmq.test import _wait


class ZmqTestSender(ZmqConnection):
    socketType = constants.PUSH


class ZmqTestReceiver(ZmqConnection):
    socketType = constants.PULL

    def messageReceived(self, message):
        if not hasattr(self, 'messages'):
            self.messages = []

        self.messages.append(message)


class ZmqAddressTestCase(unittest.TestCase):
    """
    """
    def test_init(self):
        addressString = "tcp://127.0.0.1:27935"
        a = ZmqAddress(addressString)
        self.assertEqual(a.address, addressString)
        self.assertEqual(a.scheme, "tcp")
        self.assertEqual(a.host, "127.0.0.1")
        self.assertEqual(a.port, 27935)

    def test_parse_no_port(self):
        scheme, host, port = ZmqAddress.parse("inproc://name")
        self.assertEqual(scheme, "inproc")
        self.assertEqual(host, "name")
        self.assertEqual(port, None)
        scheme, host, port = ZmqAddress.parse("tcp://1.2.3.4")
        self.assertEqual(scheme, "tcp")
        self.assertEqual(host, "1.2.3.4")
        self.assertEqual(port, None)
        scheme, host, port = ZmqAddress.parse("tcp://1.2.3.4:")
        self.assertEqual(scheme, "tcp")
        self.assertEqual(host, "1.2.3.4")
        self.assertEqual(port, None)

    def test_bad_scheme(self):
        self.assertRaises(AssertionError, ZmqAddress.parse, "icmp://1.2.3.4")


class ZmqConnectionTestCase(unittest.TestCase):
    """
    Test case for L{zmq.twisted.connection.Connection}.
    """

    def setUp(self):
        self.factory = ZmqFactory()

    def tearDown(self):
        self.factory.shutdown()

    def test_interfaces(self):
        ziv.verifyClass(IReadDescriptor, ZmqConnection)
        ziv.verifyClass(IFileDescriptor, ZmqConnection)

    def test_init(self):
        receiver = ZmqTestReceiver("inproc://#1", type=BIND)
        sender = ZmqTestSender("inproc://#1", type=CONNECT)
        self.assertEqual(receiver.connectionType, "bind")
        self.assertEqual(sender.connectionType, "connect")
        # XXX perform some more checks here

    def test_init_multiple_addresses(self):
        sender = ZmqConnection(
            "ipc://name", "inproc://#3", "tpc://localhost:5555", type=CONNECT)
        expected = ('ipc://name', 'inproc://#3', 'tpc://localhost:5555')
        self.assertEqual(sender.addresses, expected)

    def test_init_bad_connection_type(self):
        self.assertRaises(
            AssertionError, ZmqConnection, "ipc://name", "listen")

    def test_repr(self):
        expected = ("ZmqTestReceiver(ZmqFactory(), "
                    "(ZmqEndpoint(type='bind', address='inproc://#1'),))")
        r = ZmqTestReceiver(
            ZmqEndpoint(ZmqEndpointType.bind, "inproc://#1"))
        r.connect(self.factory)
        self.failUnlessEqual(expected, repr(r))

    def test_send_recv(self):
        r = ZmqTestReceiver(
            ZmqEndpoint(ZmqEndpointType.bind, "inproc://#1"))
        r.listen(self.factory)
        s = ZmqTestSender(
            ZmqEndpoint(ZmqEndpointType.connect, "inproc://#1"))
        s.connect(self.factory)

        s.send('abcd')

        def check(ignore):
            result = getattr(r, 'messages', [])
            expected = [['abcd']]
            self.failUnlessEqual(
                result, expected, "Message should have been received")

        return _wait(0.01).addCallback(check)

    def test_send_recv_tcp(self):
        r = ZmqTestReceiver(
            ZmqEndpoint(ZmqEndpointType.bind, "tcp://127.0.0.1:5555"))
        r.listen(self.factory)
        s = ZmqTestSender(
            ZmqEndpoint(ZmqEndpointType.connect, "tcp://127.0.0.1:5555"))
        s.connect(self.factory)

        for i in xrange(100):
            s.send(str(i))

        def check(ignore):
            result = getattr(r, 'messages', [])
            expected = map(lambda i: [str(i)], xrange(100))
            self.failUnlessEqual(
                result, expected, "Messages should have been received")

        return _wait(0.01).addCallback(check)

    def test_send_recv_tcp_large(self):
        r = ZmqTestReceiver(
            ZmqEndpoint(ZmqEndpointType.bind, "tcp://127.0.0.1:5555"))
        r.listen(self.factory)
        s = ZmqTestSender(
            ZmqEndpoint(ZmqEndpointType.connect, "tcp://127.0.0.1:5555"))
        s.connect(self.factory)
        s.send(["0" * 10000, "1" * 10000])

        def check(ignore):
            result = getattr(r, 'messages', [])
            expected = [["0" * 10000, "1" * 10000]]
            self.failUnlessEqual(
                result, expected, "Messages should have been received")

        return _wait(0.01).addCallback(check)

    def test_connect_success(self):

        def fakeConnectOrBind(ignored):
            self.factory.testMessage = "Fake success!"

        def check(ignored):
            self.assertEqual(self.factory.testMessage, "Fake success!")

        s = ZmqTestSender(
            ZmqEndpoint(ZmqEndpointType.connect, "inproc://#1"))
        self.patch(s, '_connectOrBind', fakeConnectOrBind)
        d = s.connect(self.factory)
        d.addCallback(check)
        return d

    def test_connect_fail(self):

        def fakeConnectOrBind(factory):
            raise Exception("ohnoz!")

        def check(error):
            self.assertEqual(str(error), "exceptions.Exception: ohnoz!")

        s = ZmqTestSender(
            ZmqEndpoint(ZmqEndpointType.connect, "inproc://#1"))
        self.patch(s, '_connectOrBind', fakeConnectOrBind)
        failure = s.connect(self.factory)
        d = self.assertFailure(failure, exceptions.ConnectionError)
        d.addCallback(check)
        return d

    def test_listen_success(self):

        def fakeConnectOrBind(ignored):
            self.factory.testMessage = "Fake success!"

        def check(ignored):
            self.assertEqual(self.factory.testMessage, "Fake success!")

        s = ZmqTestReceiver(
            ZmqEndpoint(ZmqEndpointType.bind, "inproc://#1"))
        self.patch(s, '_connectOrBind', fakeConnectOrBind)
        d = s.listen(self.factory)
        d.addCallback(check)
        return d

    def test_listen_fail(self):

        def fakeConnectOrBind(factory):
            raise Exception("ohnoz!")

        def check(error):
            self.assertEqual(str(error), "exceptions.Exception: ohnoz!")

        s = ZmqTestReceiver(
            ZmqEndpoint(ZmqEndpointType.bind, "inproc://#1"))
        self.patch(s, '_connectOrBind', fakeConnectOrBind)
        failure = s.listen(self.factory)
        d = self.assertFailure(failure, exceptions.ListenError)
        d.addCallback(check)
        return d
