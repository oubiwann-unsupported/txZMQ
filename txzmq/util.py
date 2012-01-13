from functools import wraps

from zmq.core import constants


def getSocketType(socketNumber):
    return {
        constants.REQ: "request",
        constants.REP: "reply",
        constants.PUB: "pulish",
        constants.SUB: "subscribe",
        constants.DEALER: "dealer",
        constants.ROUTER: "router",
        constants.XREQ: "xrequest",
        constants.XREP: "xreply",
        constants.PUSH: "push",
        constants.PULL: "pull",
        constants.PAIR: "pair",
    }[socketNumber]


def getDottedClassName(instance):
    parts = repr(instance.__class__).split("'")
    if len(parts) >= 2:
        return parts[1]
    return instance


def buildErrorMessage(err):
    message = str(err)
    if len(err.args) > 0:
        message = err.args[0]
    return "%s: %s" % (getDottedClassName(err), message)


class SkipTest(Exception):
    """
    Raise this exception in a test to skip it.

    Usually you can use TestResult.skip() or one of the skipping decorators
    instead of raising this directly.

    Copied from unittest2, for non-Python 2.7 versions.
    """


def skip(reason):
    """
    Unconditionally skip a test.

    Copied from unittest2, for non-Python 2.7 versions.
    """
    def decorator(test_item):
        if not (isinstance(test_item, type) and 
                issubclass(test_item, TestCase)):
            @wraps(test_item)
            def skip_wrapper(*args, **kwargs):
                raise SkipTest(reason)
            test_item = skip_wrapper
        
        test_item.__unittest_skip__ = True
        test_item.__unittest_skip_why__ = reason
        return test_item
    return decorator


def skipIf(condition, reason):
    """
    Skip a test if the condition is true.

    Copied from unittest2, for non-Python 2.7 versions.
    """
    if condition:
        return skip(reason)
    return _id
