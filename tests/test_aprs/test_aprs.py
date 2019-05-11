#!/usr/bin/env python3

from nose.tools import eq_, assert_set_equal, assert_is

from aioax25.aprs import APRSInterface
from aioax25.aprs.message import APRSMessageFrame, APRSMessageHandler

from ..loop import DummyLoop


class DummyAX25Interface(object):
    def __init__(self):
        self._loop = DummyLoop()
        self.bind_calls = []
        self.transmitted = []

    def bind(self, callback, callsign, ssid=0, regex=False):
        self.bind_calls.append((callback, callsign, ssid, regex))

    def transmit(self, frame):
        self.transmitted.append(frame)


def test_constructor_bind():
    """
    Test the constructor binds to the usual destination addresses.
    """
    ax25int = DummyAX25Interface()
    aprsint = APRSInterface(ax25int, 'VK4MSL-10')
    eq_(len(ax25int.bind_calls), 26)

    assert_set_equal(
            set([
                (call, regex, ssid)
                for (cb, call, ssid, regex)
                in ax25int.bind_calls
            ]),
            set([
                # The first bind call should be for the station SSID
                ('VK4MSL',  False,  10),
                # The rest should be the standard APRS ones.
                ('^AIR',    True,   None),
                ('^ALL',    True,   None),
                ('^AP',     True,   None),
                ('BEACON',  False,  None),
                ('^CQ',     True,   None),
                ('^GPS',    True,   None),
                ('^DF',     True,   None),
                ('^DGPS',   True,   None),
                ('^DRILL',  True,   None),
                ('^ID',     True,   None),
                ('^JAVA',   True,   None),
                ('^MAIL',   True,   None),
                ('^MICE',   True,   None),
                ('^QST',    True,   None),
                ('^QTH',    True,   None),
                ('^RTCM',   True,   None),
                ('^SKY',    True,   None),
                ('^SPACE',  True,   None),
                ('^SPC',    True,   None),
                ('^SYM',    True,   None),
                ('^TEL',    True,   None),
                ('^TEST',   True,   None),
                ('^TLM',    True,   None),
                ('^WX',     True,   None),
                ('^ZIP',    True,   None)
            ])
    )

def test_constructor_bind_altnets():
    """
    Test the constructor binds to "alt-nets".
    """
    ax25int = DummyAX25Interface()
    aprsint = APRSInterface(
            ax25int, 'VK4MSL-10',
            listen_altnets=[
                dict(callsign='VK4BWI', regex=False, ssid=None)
            ])
    eq_(len(ax25int.bind_calls), 27)

    assert_set_equal(
            set([
                (call, regex, ssid)
                for (cb, call, ssid, regex)
                in ax25int.bind_calls
            ]),
            set([
                # The first bind call should be for the station SSID
                ('VK4MSL',  False,  10),
                # The rest should be the standard APRS ones.
                ('^AIR',    True,   None),
                ('^ALL',    True,   None),
                ('^AP',     True,   None),
                ('BEACON',  False,  None),
                ('^CQ',     True,   None),
                ('^GPS',    True,   None),
                ('^DF',     True,   None),
                ('^DGPS',   True,   None),
                ('^DRILL',  True,   None),
                ('^ID',     True,   None),
                ('^JAVA',   True,   None),
                ('^MAIL',   True,   None),
                ('^MICE',   True,   None),
                ('^QST',    True,   None),
                ('^QTH',    True,   None),
                ('^RTCM',   True,   None),
                ('^SKY',    True,   None),
                ('^SPACE',  True,   None),
                ('^SPC',    True,   None),
                ('^SYM',    True,   None),
                ('^TEL',    True,   None),
                ('^TEST',   True,   None),
                ('^TLM',    True,   None),
                ('^WX',     True,   None),
                ('^ZIP',    True,   None),
                # Now should be the "alt-nets"
                ('VK4BWI',  False,  None)
            ])
    )

def test_constructor_bind_override():
    """
    Test the constructor allows overriding the usual addresses.
    """
    ax25int = DummyAX25Interface()
    aprsint = APRSInterface(ax25int, 'VK4MSL-10',
            listen_destinations=[
                dict(callsign='APRS', regex=False, ssid=None)
            ])
    eq_(len(ax25int.bind_calls), 2)

    assert_set_equal(
            set([
                (call, regex, ssid)
                for (cb, call, ssid, regex)
                in ax25int.bind_calls
            ]),
            set([
                # The first bind call should be for the station SSID
                ('VK4MSL',  False,  10),
                # The rest should be the ones we gave
                ('APRS',    False,  None)
            ])
    )

def test_send_message_oneshot():
    """
    Test that send_message in one-shot mode generates a message frame.
    """
    ax25int = DummyAX25Interface()
    aprsint = APRSInterface(ax25int, 'VK4MSL-10')
    res = aprsint.send_message(
            'VK4MDL-7', 'Hi', oneshot=True
    )

    # We don't get a return value
    assert_is(res, None)

    # The frame is passed to the AX.25 interface
    eq_(len(ax25int.transmitted), 1)
    frame = ax25int.transmitted.pop(0)

    # Frame is a APRS message frame
    assert isinstance(frame, APRSMessageFrame)

    # There is no pending messages
    eq_(len(aprsint._pending_msg), 0)

def test_send_message_confirmable():
    """
    Test that send_message in confirmable mode generates a message handler.
    """
    ax25int = DummyAX25Interface()
    aprsint = APRSInterface(ax25int, 'VK4MSL-10')
    res = aprsint.send_message(
            'VK4MDL-7', 'Hi', oneshot=False
    )

    # We got back a handler class
    assert isinstance(res, APRSMessageHandler)

    # The APRS message handler will have tried sending the message
    eq_(len(ax25int.transmitted), 1)
    frame = ax25int.transmitted.pop(0)

    # Frame is a APRS message frame
    assert isinstance(frame, APRSMessageFrame)

    # Message handler is in 'SEND' state
    eq_(res.state, APRSMessageHandler.HandlerState.SEND)

def test_send_response_oneshot():
    """
    Test that send_response ignores one-shot messages.
    """
    ax25int = DummyAX25Interface()
    aprsint = APRSInterface(ax25int, 'VK4MSL-10')
    aprsint.send_response(
            APRSMessageFrame(
                destination='VK4BWI-2',
                source='VK4MSL-10',
                addressee='VK4BWI-2',
                message=b'testing',
                msgid=None
            )
    )

    # Nothing should be sent
    eq_(len(ax25int.transmitted), 0)

def test_send_response_ack():
    """
    Test that send_response with ack=True sends acknowledgement.
    """
    ax25int = DummyAX25Interface()
    aprsint = APRSInterface(ax25int, 'VK4MSL-10')
    aprsint.send_response(
            APRSMessageFrame(
                destination='VK4BWI-2',
                source='VK4MSL-10',
                addressee='VK4BWI-2',
                message=b'testing',
                msgid=123
            ),
            ack=True
    )

    # The APRS message handler will have tried sending the message
    eq_(len(ax25int.transmitted), 1)
    frame = ax25int.transmitted.pop(0)

    # Frame is a APRS message acknowledgement frame
    assert isinstance(frame, APRSMessageFrame)
    eq_(frame.payload, b':VK4MSL-10:ack123')

def test_send_response_rej():
    """
    Test that send_response with ack=False sends rejection.
    """
    ax25int = DummyAX25Interface()
    aprsint = APRSInterface(ax25int, 'VK4MSL-10')
    aprsint.send_response(
            APRSMessageFrame(
                destination='VK4BWI-2',
                source='VK4MSL-10',
                addressee='VK4BWI-2',
                message=b'testing',
                msgid=123
            ),
            ack=False
    )

    # The APRS message handler will have tried sending the message
    eq_(len(ax25int.transmitted), 1)
    frame = ax25int.transmitted.pop(0)

    # Frame is a APRS message rejection frame
    assert isinstance(frame, APRSMessageFrame)
    eq_(frame.payload, b':VK4MSL-10:rej123')